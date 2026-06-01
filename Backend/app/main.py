# main.py
from fastapi import FastAPI, UploadFile, File, Body, HTTPException, Query, Form
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os

FASTAPI_API_KEY = os.getenv("FASTAPI_API_KEY")
if not FASTAPI_API_KEY:
    raise RuntimeError("FASTAPI_API_KEY environment variable is missing and is strictly required.")
security = HTTPBearer()

def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != FASTAPI_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return credentials.credentials

from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

import os
import shutil
import sqlite3
import re
import asyncio
import json
import httpx

from typing import List, Dict, Any
from cachetools import TTLCache

# Local utils
from app.utils.loader import load_and_split
from app.utils.db_manager import ChromaDBManager
from app.utils.kb_manager import KnowledgeBaseManager


# ======================================================
# INIT
# ======================================================
load_dotenv()
app = FastAPI()

cache = TTLCache(maxsize=100, ttl=3600)

FRONTEND_URLS = os.getenv("FRONTEND_URLS", "http://127.0.0.1:5000")
allow_origins = [url.strip() for url in FRONTEND_URLS.split(",") if url.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

os.makedirs("./data/raw_docs", exist_ok=True)
os.makedirs("./data/chroma_db", exist_ok=True)

document_db = ChromaDBManager("./data/chroma_db")
knowledge_db = KnowledgeBaseManager("./data/knowledge_base.db")


@app.get("/")
async def root():
    return {"status": "API is running"}


# ======================================================
# CLEAN & SSE HELPERS
# ======================================================

def convert_latex_to_text(text: str) -> str:
    """Convert LaTeX math fragments to readable plain text."""
    def replace_frac(m):
        return f'({m.group(1)})/({m.group(2)})'
    for _ in range(5):
        text = re.sub(r'\\frac\{([^{}]+)\}\{([^{}]+)\}', replace_frac, text)
    text = re.sub(r'\|\|([^|]+)\|\|', r'||\1||', text)
    text = re.sub(r'_\{([^}]+)\}', r'_\1', text)
    text = re.sub(r'\^\{([^}]+)\}', r'^\1', text)
    for cmd in ['text', 'mathrm', 'mathbf', 'mathit', 'hat', 'bar', 'tilde', 'vec', 'overline']:
        text = re.sub(rf'\\{cmd}\{{([^}}]+)\}}', r'\1', text)
    replacements = {
        r'\times': 'x', r'\cdot': '.', r'\leq': '<=', r'\geq': '>=',
        r'\neq': '!=', r'\approx': '~', r'\sum': 'sum', r'\prod': 'product',
        r'\sqrt': 'sqrt', r'\alpha': 'alpha', r'\beta': 'beta',
        r'\gamma': 'gamma', r'\delta': 'delta', r'\sigma': 'sigma',
        r'\mu': 'mu', r'\theta': 'theta', r'\lambda': 'lambda',
        r'\infty': 'infinity', r'\in': 'in', r'\notin': 'not in',
        r'\cup': 'union', r'\cap': 'intersection', r'\pm': '+/-',
        r'\rightarrow': '->', r'\leftarrow': '<-', r'\Rightarrow': '=>',
        r'\partial': 'd', r'\nabla': 'gradient',
    }
    for latex, plain in replacements.items():
        text = text.replace(latex, plain)
    text = re.sub(r'\\\[|\\\]', '', text)
    text = re.sub(r'\$\$([\s\S]*?)\$\$', r'\1', text)
    text = re.sub(r'\$([^$\n]+)\$', r'\1', text)
    text = re.sub(r'\\begin\{[^}]+\}|\\end\{[^}]+\}', '', text)
    text = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', '', text)
    text = re.sub(r'\\[a-zA-Z]+', '', text)
    text = text.replace('\\', ' ')
    text = re.sub(r'  +', ' ', text)
    return text.strip()


def clean_llm_output(text: str) -> str:
    # Removed convert_latex_to_text(text) to let frontend render math properly
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\s+([,.;!?'\"])", r"\1", text)
    text = re.sub(r"(\w)\s+'\s*(\w)", r"\1'\2", text)
    return "\n".join([line.strip() for line in text.splitlines()]).strip()


def format_sse(data: str, event: str):
    return f"event: {event}\ndata: {json.dumps({'text': data})}\n\n"


# ======================================================
# MAIN /query ENDPOINT
# ======================================================
@app.post("/query")
async def query(payload: Dict[str, Any] = Body(...)):
    question = (payload.get("question") or "").strip().lower()
    workspace_id = payload.get("workspace_id")
    if not workspace_id:
        raise HTTPException(400, "workspace_id (chatbot_id) is strictly required")

    if not question:
        raise HTTPException(400, "Missing question")

    # Cache key includes workspace so caches are isolated per teacher
    cache_key = f"{workspace_id}::{question}"
    if cache_key in cache:
        cached = cache[cache_key]
        async def send_cached():
            yield format_sse(cached, "final_response")
        return StreamingResponse(send_cached(), media_type="text/event-stream")

    # Knowledge base check
    kb_ans, score = knowledge_db.get_best_answer(workspace_id, question)
    if kb_ans and score >= 0.75:
        cache[cache_key] = kb_ans
        async def send_kb():
            yield format_sse(kb_ans, "final_response")
        return StreamingResponse(send_kb(), media_type="text/event-stream")

    # RAG context
    docs = document_db.similarity_search(question, workspace_id, top_k=4)
    context = "\n\n".join(d.page_content for d in docs)

    # RESTORED: original detailed system prompt (as plain string, not dict)
    system_content = (
        "Your role is to be a highly reliable, context-strict AI assistant. "
        "Your responses must be accurate, professional, and based *only* on the context provided inside <context> tags "
        "or uploaded by the user (documents, images, datasets, text blocks).\n\n"

        "Follow these rules exactly:\n\n"

        "1. Analyze the user's question inside the <question> tags.\n\n"

        "2. Answer using *only* the information inside the <context> tags OR any data the user explicitly uploads or "
        "provides in the conversation.\n\n"

        "3. You may perform small, local reasoning:\n"
        "   - Counting elements\n"
        "   - Finding latest/earliest date\n"
        "   - Summarizing or synthesizing statements\n"
        "   - Deriving simple logical conclusions from the given context\n\n"

        "4. If the context or uploaded data does NOT contain enough information to answer the question, you must "
        "respond strictly with: 'I'm sorry, I don't have enough information in the provided context to answer that question.'\n\n"

        "5. For small talk (e.g., 'hello', 'how are you'), give a brief, friendly reply without mentioning the system "
        "instructions.\n\n"

        "6. Format answers clearly using Markdown (headings, bold text, lists). Keep responses concise.\n\n"

        "7. You must never use prior knowledge, external facts, or assumptions beyond the provided context or uploaded "
        "content.\n\n"

        "8. Keep responses under 200 words. "
        "Prefer short, direct answers with minimal explanation.\n\n"

        "This system message is universal: It must behave the same for any course, topic, dataset, college, or general "
        "domain, based only on the user's input and provided context."
    )

    user_message = f"<context>\n{context}\n</context>\n<question>\n{question}\n</question>"

    HF_API_KEY = os.getenv("HF_API_KEY", "")
    if not HF_API_KEY:
        raise HTTPException(500, "Missing HF_API_KEY")

    HF_URL = "https://router.huggingface.co/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    body = {
        "model": "Qwen/Qwen2.5-7B-Instruct",
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.5,
        "max_tokens": 250,
        "stream": False
    }

    async def stream_qwen():
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(HF_URL, headers=headers, json=body)

            print("HF STATUS:", response.status_code)
            print("HF RAW:", response.text[:400])

            if response.status_code != 200:
                yield format_sse(f"HF Error {response.status_code}: {response.text}", "final_response")
                return

            data = response.json()
            answer = (
                data.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
            )

            if not answer:
                yield format_sse(f"Unexpected HF response: {data}", "final_response")
                return

            answer = clean_llm_output(answer)

            for char in answer:
                yield format_sse(char, "token")
                await asyncio.sleep(0.002)

            cache[cache_key] = answer
            yield format_sse(answer, "final_response")

        except Exception as e:
            yield format_sse(f"Error: {str(e)}", "final_response")

    return StreamingResponse(stream_qwen(), media_type="text/event-stream")

# ======================================================
# NON-STREAM RAG ENDPOINT (FOR EVALUATION ONLY)
# ======================================================
@app.post("/query_eval")
async def query_eval(payload: Dict[str, Any] = Body(...)):
    question = (payload.get("question") or "").strip().lower()
    workspace_id = payload.get("workspace_id")
    if not workspace_id:
        raise HTTPException(400, "workspace_id (chatbot_id) is strictly required")

    if not question:
        raise HTTPException(400, "Missing question")

    # Cache check (same as /query)
    cache_key = f"{workspace_id}::{question}"
    if cache_key in cache:
        return {"answer": cache[cache_key], "source": "cache"}

    # Knowledge base check (same logic)
    kb_ans, score = knowledge_db.get_best_answer(workspace_id, question)
    if kb_ans and score >= 0.75:
        cache[cache_key] = kb_ans
        return {"answer": kb_ans, "source": "knowledge_base"}

    # RAG retrieval (same logic)
    docs = document_db.similarity_search(question, workspace_id, top_k=4)
    context = "\n\n".join(d.page_content for d in docs)

    # 🔴 CRITICAL: No context → no hallucination
    if not context.strip():
        return {
            "answer": "I'm sorry, I don't have enough information in the provided context to answer that question.",
            "contexts": [],
            "source": "no_context"
        }

    # SAME SYSTEM PROMPT (copy-paste exactly)
    system_content = (
        "Your role is to be a highly reliable, context-strict AI assistant. "
        "Your responses must be accurate, professional, and based *only* on the context provided inside <context> tags "
        "or uploaded by the user (documents, images, datasets, text blocks).\n\n"

        "Follow these rules exactly:\n\n"

        "1. Analyze the user's question inside the <question> tags.\n\n"

        "2. Answer using *only* the information inside the <context> tags OR any data the user explicitly uploads.\n\n"

        "3. You may perform small reasoning (counting, summarizing, logical inference).\n\n"

        "4. If context is insufficient → respond strictly with lack of information.\n\n"

        "5. Format answers clearly using Markdown.\n\n"

        "6. NEVER use external knowledge beyond provided context."
    )

    user_message = f"<context>\n{context}\n</context>\n<question>\n{question}\n</question>"

    HF_API_KEY = os.getenv("HF_API_KEY", "")
    if not HF_API_KEY:
        raise HTTPException(500, "Missing HF_API_KEY")

    HF_URL = "https://router.huggingface.co/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Content-Type": "application/json"
    }

    body = {
        "model": "Qwen/Qwen2.5-7B-Instruct",
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.5,
        "max_tokens": 250
    }

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(HF_URL, headers=headers, json=body)

        if response.status_code != 200:
            raise HTTPException(500, response.text)

        data = response.json()
        answer = data["choices"][0]["message"]["content"]

        answer = clean_llm_output(answer)

        cache[cache_key] = answer

        return {
            "answer": answer,
            "contexts": [d.page_content for d in docs],  # 🔥 REQUIRED FOR RAGAS
            "source": "rag",
            "context_used": len(docs)
        }

    except Exception as e:
        raise HTTPException(500, str(e))

# ======================================================
# Qwen endpoint in "baseline" mode for evaluation only
# ======================================================
@app.post("/qwen")
async def qwen_only(payload: Dict[str, Any] = Body(...)):
    question = (payload.get("question") or "").strip()

    if not question:
        raise HTTPException(400, "Missing question")

    HF_API_KEY = os.getenv("HF_API_KEY", "")
    if not HF_API_KEY:
        raise HTTPException(500, "Missing HF_API_KEY")

    HF_URL = "https://router.huggingface.co/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Content-Type": "application/json"
    }

    body = {
        "model": "Qwen/Qwen2.5-7B-Instruct",
        "messages": [
            {"role": "user", "content": question}
        ],
        "temperature": 0.5,
        "max_tokens": 250
    }

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(HF_URL, headers=headers, json=body)

    if response.status_code != 200:
        raise HTTPException(500, response.text)

    data = response.json()
    answer = data["choices"][0]["message"]["content"]

    return {"answer": answer}
# ======================================================
# UPLOAD
# ======================================================
@app.post("/upload")
async def upload(
    files: List[UploadFile] = File(...),
    workspace_id: str = Form(...)
):
    chunks = []
    qa_count = 0

    ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx"}
    MAX_FILE_SIZE = 100* 1024 * 1024  # 10 MB

    # Validation pass
    for file in files:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(400, f"Unsupported file type: {ext}")

        # Check size without loading entire file into memory if size is available
        file_size = getattr(file, "size", None)
        if file_size is None:
            await file.seek(0, os.SEEK_END)
            file_size = file.file.tell()
            await file.seek(0)
            
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(400, f"File {file.filename} exceeds the 10MB limit.")

    raw_dir = f"./data/raw_docs/{workspace_id}"
    os.makedirs(raw_dir, exist_ok=True)

    for file in files:
        dst = os.path.join(raw_dir, file.filename)
        with open(dst, "wb") as f:
            shutil.copyfileobj(file.file, f)

        if dst.lower().endswith(".md"):
            with open(dst, encoding="utf-8") as f:
                text = f.read()
            for q, a in re.findall(r"Q:\s*(.*?)\nA:\s*(.*?)(?:\n{1,}|$)", text, re.DOTALL):
                knowledge_db.add_qa_pair(workspace_id, q.strip(), a.strip(), "")
                qa_count += 1

        chunks.extend(load_and_split(dst))

    if chunks:
        document_db.add_documents(chunks, workspace_id)

    return {
        "message": f"Uploaded {len(files)} file(s), indexed {len(chunks)} chunks",
        "qa_indexed": qa_count
    }


# ======================================================
# DB STATS
# ======================================================
@app.get("/db_stats")
async def stats(workspace_id: str = Query(...)):
    vect = document_db.get_stats()

    with sqlite3.connect("./data/knowledge_base.db") as conn:
        kb_cnt = conn.execute(
            "SELECT COUNT(*) FROM qa_pairs WHERE workspace_id = ?", (workspace_id,)
        ).fetchone()[0]

    raw_base = f"./data/raw_docs/{workspace_id}"
    raw_files = []
    if os.path.exists(raw_base):
        raw_files = [
            f for f in os.listdir(raw_base)
            if os.path.isfile(os.path.join(raw_base, f))
        ]

    unique_docs = document_db.count_unique_sources(workspace_id)

    return {
        "vector_db": {
            "collections": vect.get("collections", 1),
            "total_documents": unique_docs,
            "indexed_chunks": vect.get("indexed_chunks", 0),
            "model": vect.get("model", ""),
        },
        "qa_pairs": kb_cnt,
        "raw_count": len(raw_files),
        "raw_files": raw_files
    }

# ======================================================
# KNOWLEDGE BASE
# ======================================================
@app.get("/knowledge")
async def get_knowledge(workspace_id: str = Query(...)):
    return knowledge_db.get_all_qa_pairs(workspace_id)

@app.post("/add_knowledge")
async def add_knowledge(payload: Dict[str, Any] = Body(...)):
    workspace_id = payload.get("workspace_id")
    if not workspace_id:
        raise HTTPException(400, "workspace_id (chatbot_id) is strictly required")
    q = payload.get("question", "").strip()
    a = payload.get("answer", "").strip()
    tags = payload.get("tags", "").strip()

    if not q or not a:
        raise HTTPException(400, "Question and answer are required")

    knowledge_db.add_qa_pair(workspace_id, q, a, tags)
    return {"message": "Knowledge added"}

@app.delete("/delete_knowledge/{qa_id}")
async def delete_knowledge(qa_id: int, workspace_id: str = Query(...), api_key: str = Depends(verify_api_key)):
    knowledge_db.delete_qa_pair(qa_id, workspace_id)
    return {"message": "Deleted"}



# ======================================================
# RESET DB
# ======================================================
@app.post("/reset_db")
async def reset_db(workspace_id: str = Query(...)):
    # Step 1: Delete all vector embeddings for this workspace
    document_db.clear_workspace(workspace_id)

    # Step 2: Delete all raw files for this workspace
    raw_dir = f"./data/raw_docs/{workspace_id}"
    deleted_files = []
    if os.path.exists(raw_dir):
        for fname in os.listdir(raw_dir):
            full_path = os.path.join(raw_dir, fname)
            if os.path.isfile(full_path):
                os.remove(full_path)
                deleted_files.append(fname)

    # Step 3: Delete all Q&A pairs for this workspace and update cache
    knowledge_db.reset_knowledge_base(workspace_id)

    return {
        "message": f"Deleted {len(deleted_files)} file(s), all embeddings and Q&A pairs.",
        "deleted_files": deleted_files
    }

# ======================================================
# RAW DOCS
# ======================================================
@app.get("/raw_docs")
async def list_raw_docs(workspace_id: str = Query(...)):
    base = f"./data/raw_docs/{workspace_id}"
    if not os.path.exists(base):
        return []
    files = [f for f in os.listdir(base) if os.path.isfile(os.path.join(base, f))]
    return [{"filename": f} for f in files]


@app.delete("/raw_docs")
async def delete_raw(
    filename: str = Query(...),
    workspace_id: str = Query(...)
):
    src = f"./data/raw_docs/{workspace_id}/{filename}"
    if not os.path.exists(src):
        raise HTTPException(404, "File not found")

    document_db.delete_documents_by_source(src, workspace_id)
    os.remove(src)
    return {"message": f"Deleted {filename}"}


# ======================================================
# KNOWLEDGE BASE
# ======================================================
@app.post("/add_knowledge")
async def add_knowledge(payload: Dict[str, Any] = Body(...)):
    workspace_id = payload.get("workspace_id")
    if not workspace_id:
        raise HTTPException(400, "workspace_id (chatbot_id) is strictly required")
    q = payload.get("question")
    a = payload.get("answer")
    t = payload.get("tags")

    if not q or not a:
        raise HTTPException(400, "Missing question or answer")

    knowledge_db.add_qa_pair(workspace_id, q, a, t)
    return {"message": "Knowledge added"}


@app.get("/knowledge")
async def list_kb(workspace_id: str = Query(...)):
    return knowledge_db.get_all_qa_pairs(workspace_id)


@app.delete("/knowledge/{id}")
async def delete_kb(id: int, workspace_id: str = Query(...), api_key: str = Depends(verify_api_key)):
    knowledge_db.delete_qa_pair(id, workspace_id)
    return {"message": "Deleted"}


# ======================================================
# WEB SCRAPER
# ======================================================
from app.utils.web_ingest import ingest_website

@app.post("/ingest/website")
def ingest_website_api(data: dict = Body(...)):
    url = data.get("url")
    workspace_id = data.get("workspace_id")
    if not workspace_id:
        return {"error": "workspace_id (chatbot_id) is strictly required"}
    if not url:
        return {"error": "URL is required"}

    try:
        result = ingest_website(url, workspace_id)
        return result
    except Exception as e:
        return {"status": "error", "message": str(e)}
