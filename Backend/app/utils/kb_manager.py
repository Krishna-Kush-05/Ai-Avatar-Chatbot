# app/utils/kb_manager.py

import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Tuple

from sentence_transformers import SentenceTransformer, util
import torch


class KnowledgeBaseManager:

    def __init__(self, db_path: str = "./data/knowledge_base.db"):

        self.db_path = db_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        self.model = SentenceTransformer("all-MiniLM-L6-v2")

        self._cache: List[Tuple[str, str, torch.Tensor, str]] = []

        with sqlite3.connect(self.db_path) as conn:

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS qa_pairs(
                    id INTEGER PRIMARY KEY,
                    workspace_id TEXT,
                    question TEXT,
                    answer TEXT,
                    tags TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

        self._build_cache()

    def _build_cache(self):

        self._cache = []

        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT workspace_id, question, answer FROM qa_pairs"
            ).fetchall()

        if not rows:
            return

        questions = [r[1] for r in rows]

        embeddings = self.model.encode(
            questions,
            convert_to_tensor=True
        )

        for i, row in enumerate(rows):
            workspace_id = row[0]
            question = row[1]
            answer = row[2]

            self._cache.append(
                (question, answer, embeddings[i], workspace_id)
            )

    def add_qa_pair(self, workspace_id: str, q: str, a: str, tags: Optional[str]):

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO qa_pairs(workspace_id, question, answer, tags)
                VALUES(?,?,?,?)
                """,
                (workspace_id, q, a, tags)
            )
            conn.commit()

        emb = self.model.encode(q, convert_to_tensor=True)

        self._cache.append((q, a, emb, workspace_id))

    def get_all_qa_pairs(self, workspace_id: str):

        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT id, question, answer, tags
                FROM qa_pairs
                WHERE workspace_id = ?
                """,
                (workspace_id,)
            ).fetchall()

        return [
            {
                "id": r[0],
                "question": r[1],
                "answer": r[2],
                "tags": r[3]
            }
            for r in rows
        ]

    def delete_qa_pair(self, qa_id: int, workspace_id: str):

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM qa_pairs WHERE id = ? AND workspace_id = ?", (qa_id, workspace_id))
            conn.commit()

        self._build_cache()

    def get_best_answer(self, workspace_id: str, question: str):

        with sqlite3.connect(self.db_path) as conn:

            row = conn.execute(
                """
                SELECT answer
                FROM qa_pairs
                WHERE question = ? AND workspace_id = ?
                """,
                (question, workspace_id)
            ).fetchone()

            if row:
                return row[0], 1.0

        if not self._cache:
            return None, 0.0

        q_emb = self.model.encode(question, convert_to_tensor=True)

        best_score = 0
        best_answer = None

        for q, a, emb, ws in self._cache:

            if ws != workspace_id:
                continue

            score = util.cos_sim(q_emb, emb).item()

            if score > best_score:
                best_score = score
                best_answer = a

        return best_answer, best_score

    def reset_knowledge_base(self, workspace_id: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM qa_pairs WHERE workspace_id = ?", (workspace_id,))
            conn.commit()
        
        self._build_cache()