# main.py
from fastapi import FastAPI, UploadFile, File, Body, HTTPException, Query
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
def clean_llm_output(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\s+([,.;!?'\"])", r"\1", text)
    text = re.sub(r"(\w)\s+'\s*(\w)", r"\1'\2", text)
    return "\n".join([line.strip() for line in text.splitlines()]).strip()


def format_sse(data: str, event: str):
    return f"event: {event}\ndata: {json.dumps({'text': data})}\n\n"


# ======================================================
# MAIN /query ENDPOINT (WITH Qwen-7B)
# ======================================================
@app.post("/query")
async def query(payload: Dict[str, Any] = Body(...)):
    question = (payload.get("question") or "").strip().lower()

    if not question:
        raise HTTPException(400, "Missing question")

    # --------------------------------------------
    # 1) CACHE CHECK
    # --------------------------------------------
    if question in cache:
        cached = cache[question]
        async def send_cached():
            yield format_sse(cached, "final_response")
        return StreamingResponse(send_cached(), media_type="text/event-stream")

    # --------------------------------------------
    # 2) KNOWLEDGE BASE CHECK
    # --------------------------------------------
    kb_ans, score = knowledge_db.get_best_answer(question)
    if kb_ans and score >= 0.95:
        cache[question] = kb_ans
        async def send_kb():
            yield format_sse(kb_ans, "final_response")
        return StreamingResponse(send_kb(), media_type="text/event-stream")

    # --------------------------------------------
    # 3) RAG CONTEXT BUILDING
    # --------------------------------------------
    docs = document_db.similarity_search(question, top_k=4)
    context = "\n\n".join(d.page_content for d in docs)

    system_message = {
    "role": "system",
    "content": (
        "Your role is to be a highly reliable, context-strict AI assistant. "
        "Your responses must be accurate, professional, and based *only* on the context provided inside <context> tags "
        "or uploaded by the user (documents, images, datasets, text blocks).\n\n"

        "Follow these rules exactly:\n\n"

        "1. Analyze the user's question inside the <question> tags.\n\n"

        "2. Answer using *only* the information inside the <context> tags OR any data the user explicitly uploads or "
        "provides in the conversation.\n\n"

        "3. You may perform small, local reasoning:\n"
        "- Counting elements\n"
        "- Finding latest/earliest date\n"
        "- Summarizing or synthesizing statements\n"
        "- Deriving simple logical conclusions from the given context\n\n"

        "4. **If the context or uploaded data does NOT contain enough information to answer the question, you must "
        "respond strictly with:** 'I'm sorry...'\n\n"

        "5. For small talk (e.g., 'hello', 'how are you'), give a brief, friendly reply without mentioning the system "
        "instructions.\n\n"

        "6. Format answers clearly using Markdown (headings, bold text, lists). Keep responses concise.\n\n"

        "7. You must never use prior knowledge, external facts, or assumptions beyond the provided context or uploaded "
        "content.\n\n"

        "This system message is universal: It must behave the same for any course, topic, dataset, college, or general "
        "domain, based only on the user's input and provided context."
    )
}


    user_message = f"<context>\n{context}\n</context>\n<question>\n{question}\n</question>"

    # ======================================================
    # HUGGINGFACE CHAT COMPLETIONS (Qwen-7B)
    # ======================================================
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
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.7,
        "max_tokens": 300,
        "stream": False
    }

    # ======================================================
    # STREAM BACK TO FRONTEND
    # ======================================================
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

            # Extract answer
            answer = (
                data.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
            )

            if not answer:
                yield format_sse(f"Unexpected HF response: {data}", "final_response")
                return

            answer = clean_llm_output(answer)

            # Stream character by character
            for char in answer:
                yield format_sse(char, "token")
                await asyncio.sleep(0.002)

            cache[question] = answer
            # Send final_response with complete answer only once at the end
            yield format_sse(answer, "final_response")

        except Exception as e:
            yield format_sse(f"Error: {str(e)}", "final_response")

    return StreamingResponse(stream_qwen(), media_type="text/event-stream")


# ======================================================
# ALL OTHER ENDPOINTS (IDENTICAL TO YOUR ORIGINAL FILE)
# ======================================================
@app.post("/upload")
async def upload(files: List[UploadFile] = File(...)):
    chunks = []
    qa_count = 0
    raw_dir = "./data/raw_docs"

    for file in files:
        dst = os.path.join(raw_dir, file.filename)
        with open(dst, "wb") as f:
            shutil.copyfileobj(file.file, f)

        if dst.lower().endswith(".md"):
            with open(dst, encoding="utf-8") as f:
                text = f.read()
            for q, a in re.findall(r"Q:\s*(.*?)\nA:\s*(.*?)(?:\n{1,}|$)", text, re.DOTALL):
                knowledge_db.add_qa_pair(q.strip(), a.strip(), "")
                qa_count += 1

        chunks.extend(load_and_split(dst))

    if chunks:
        document_db.add_documents(chunks)

    return {"message": f"Uploaded {len(files)}, indexed {len(chunks)} chunks", "qa_indexed": qa_count}


@app.get("/db_stats")
async def stats():
    vect = document_db.get_stats()
    with sqlite3.connect("./data/knowledge_base.db") as conn:
        kb_cnt = conn.execute("SELECT COUNT(*) FROM qa_pairs").fetchone()[0]

    raw_files = sorted(os.listdir("./data/raw_docs"))
    return {"vector_db": vect, "qa_pairs": kb_cnt, "raw_count": len(raw_files), "raw_files": raw_files}


@app.post("/reset_db")
async def reset_db():
    document_db.clear_database()
    chunks = []
    for fname in os.listdir("./data/raw_docs"):
        full_path = "./data/raw_docs/" + fname
        chunks.extend(load_and_split(full_path))

    if chunks:
        document_db.add_documents(chunks)

    return {"message": "Vector DB reset and re-indexed"}


@app.delete("/raw_docs")
async def delete_raw(filename: str = Query(...)):
    src = "./data/raw_docs/" + filename
    if not os.path.exists(src):
        raise HTTPException(404, "File not found")

    document_db.delete_documents_by_source(src)
    os.remove(src)

    return {"message": f"Deleted {filename}"}


@app.post("/add_knowledge")
async def add_knowledge(payload: Dict[str, Any] = Body(...)):
    q = payload.get("question")
    a = payload.get("answer")
    t = payload.get("tags")

    if not q or not a:
        raise HTTPException(400, "Missing question or answer")

    knowledge_db.add_qa_pair(q, a, t)
    return {"message": "Knowledge added"}


@app.get("/knowledge")
async def list_kb():
    return knowledge_db.get_all_qa_pairs()


@app.delete("/knowledge/{id}")
async def delete_kb(id: int):
    knowledge_db.delete_qa_pair(id)
    return {"message": "Deleted"}
