# app/utils/kb_manager.py
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Tuple

from sentence_transformers import SentenceTransformer, util
import torch


class KnowledgeBaseManager:
    """
    Simple SQLite-backed QA store with an in-memory embedding cache for fast semantic lookup.

    - Stores (question, answer, tags) in SQLite.
    - Keeps an in-memory cache of (question, answer, embedding_tensor) to avoid
      repeatedly encoding DB questions at query time.
    """

    def __init__(self, db_path: str = "./data/knowledge_base.db"):
        self.db_path = db_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        # SentenceTransformer model for embeddings
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

        # in-memory cache: list[ (question, answer, embedding_tensor) ]
        self._cache: List[Tuple[str, str, torch.Tensor]] = []

        # Ensure table exists
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS qa_pairs(
                    id INTEGER PRIMARY KEY,
                    question TEXT,
                    answer TEXT,
                    tags TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()

        # build cache once at startup
        self._build_cache()

    def _build_cache(self) -> None:
        """Load all QA pairs from DB and compute embeddings for the questions."""
        self._cache = []
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute("SELECT question, answer FROM qa_pairs")
            rows = cur.fetchall()
        if not rows:
            return

        questions = [r[0] for r in rows]
        try:
            embs = self.model.encode(questions, convert_to_tensor=True)
        except Exception:
            # fallback: encode one-by-one (slower) to avoid OOM on some environments
            embs_list = []
            for q in questions:
                emb = self.model.encode(q, convert_to_tensor=True)
                embs_list.append(emb)
            embs = torch.stack(embs_list)

        # Pair each DB row with its embedding tensor
        for (q, a), emb in zip(rows, embs):
            self._cache.append((q, a, emb))

    def add_qa_pair(self, q: str, a: str, tags: Optional[str]) -> None:
        """Insert a new QA pair into the DB and append its question embedding to the cache."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO qa_pairs(question, answer, tags) VALUES(?,?,?)",
                (q, a, tags),
            )
            conn.commit()

        # compute embedding for the new question and append to cache
        try:
            emb = self.model.encode(q, convert_to_tensor=True)
            self._cache.append((q, a, emb))
        except Exception:
            # If embedding fails, skip caching (DB still contains the record)
            pass

    def get_all_qa_pairs(self) -> List[Dict]:
        """Return a list of all QA pairs from the DB."""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute("SELECT id, question, answer, tags FROM qa_pairs")
            rows = cur.fetchall()
        return [{"id": r[0], "question": r[1], "answer": r[2], "tags": r[3]} for r in rows]

    def delete_qa_pair(self, qa_id: int) -> None:
        """Delete a QA pair by id and rebuild the in-memory cache."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM qa_pairs WHERE id = ?", (qa_id,))
            conn.commit()
        # Rebuild cache for simplicity (could be optimized to remove single entry)
        self._build_cache()

    def get_best_answer(self, question: str) -> Tuple[Optional[str], float]:
        """
        Return the best-matching answer and a similarity score in [0,1].

        - If an exact question match exists in the DB, return it with score 1.0.
        - Otherwise, compute semantic similarity against cached embeddings (fast).
          Returns (None, 0.0) when no KB entries exist.
        """
        # Exact match first
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute("SELECT answer FROM qa_pairs WHERE question = ?", (question,))
            row = cur.fetchone()
            if row:
                return row[0], 1.0

        # Semantic fallback using cached embeddings
        if not self._cache:
            return None, 0.0

        try:
            q_emb = self.model.encode(question, convert_to_tensor=True)
        except Exception:
            # If embedding fails, return no answer
            return None, 0.0

        # Build a tensor of DB embeddings and compute cosine similarities
        try:
            db_embs = torch.stack([t[2] for t in self._cache])
            scores = util.pytorch_cos_sim(q_emb, db_embs).squeeze(0)
            best_idx = int(torch.argmax(scores).item())
            best_score = float(scores[best_idx].item())
            best_ans = self._cache[best_idx][1]
            return best_ans, best_score
        except Exception:
            return None, 0.0
