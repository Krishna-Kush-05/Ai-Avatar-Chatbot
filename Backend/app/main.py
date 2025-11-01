# main.py
from fastapi import FastAPI, UploadFile, File, Body, HTTPException, Request, Query
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import shutil
import sqlite3
import re
import asyncio
import json
from typing import List, Dict, Any

from ollama import AsyncClient
from app.utils.loader import load_and_split
from app.utils.db_manager import ChromaDBManager
from app.utils.kb_manager import KnowledgeBaseManager
from cachetools import TTLCache

load_dotenv()
app = FastAPI()

cache = TTLCache(maxsize=100, ttl=3600)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

os.makedirs("./data/raw_docs", exist_ok=True)
os.makedirs("./data/chroma_db", exist_ok=True)

document_db = ChromaDBManager(persist_directory="./data/chroma_db")
knowledge_db = KnowledgeBaseManager(db_path="./data/knowledge_base.db")

@app.get("/")
async def root():
    return {"status": "API is running"}

# ✅ CORRECTED FUNCTION
def clean_llm_output(text: str) -> str:
    """
    This final version targets specific formatting issues while preserving newlines.
    """
    # Collapse multiple spaces/tabs into a single space, but leave newlines alone
    text = re.sub(r'[ \t]+', ' ', text)
    # Remove space before punctuation, including apostrophes
    text = re.sub(r'\s+([,.;!?\'"])', r'\1', text)
    # Fix contractions like "don ' t" -> "don't"
    text = re.sub(r"(\w)\s+'\s*(\w)", r"\1'\2", text)
    # Fixes cases like "B . T ech" -> "B.Tech"
    text = re.sub(r'\b([A-Z])\s\.\s', r'\1.', text)
    # Remove leading/trailing whitespace from each line
    text = "\n".join([line.strip() for line in text.splitlines()]).strip()
    return text
# --- UPDATED: More consistent SSE formatting ---
def format_sse(data: str, event: str) -> str:
    """
    Formats data for Server-Sent Events.
    Consistently wraps the data in a JSON object for easier client-side parsing.
    """
    payload = json.dumps({"text": data})
    return f"event: {event}\ndata: {payload}\n\n"

@app.post("/query")
async def query(payload: Dict[str, Any] = Body(...)):
    question = payload.get("question", "").strip().lower()
    if not question:
        raise HTTPException(400, "Missing question.")

    # 1. Check Cache
    if question in cache:
        cached_answer = cache[question]
        async def cached_stream():
            # For cache/kb hits, we send a single 'final_response' event
            yield format_sse(cached_answer, event="final_response")
        return StreamingResponse(cached_stream(), media_type="text/event-stream", headers={"X-Response-Source": "cache"})

    # 2. Check Knowledge Base
    kb_ans, score = knowledge_db.get_best_answer(question)
    if kb_ans and score >= 0.95:
        cache[question] = kb_ans
        async def kb_exact_stream():
            yield format_sse(kb_ans, event="final_response")
        return StreamingResponse(kb_exact_stream(), media_type="text/event-stream", headers={"X-Response-Source": "knowledge"})

    # 3. Fallback to LLM + RAG with "Stream-and-Replace"
    docs = document_db.similarity_search(question, top_k=4)
    context = "\n\n".join(d.page_content for d in docs)
    
    kb_context_injection = ""
    if kb_ans and score > 0.70:
        try:
            similar_question_record = next(item for item in knowledge_db._cache if item[1] == kb_ans)
            similar_question = similar_question_record[0]
            kb_context_injection = f"A similar question was '{similar_question}' with the answer '{kb_ans}'. Use this as a guide.\n\n"
        except StopIteration:
            kb_context_injection = ""

    # In main.py, inside the @app.post("/query") endpoint

    system_message = {
        "role": "system",
        "content": (
            "You are a helpful, friendly, and expert AI assistant for the MIT Academy of Engineering (MITAOE). "
            "Your responses must be professional, accurate, and based *only* on the context provided. "
            "Follow these instructions precisely:\n\n"
            
            "1.  Analyze the user's question provided inside the <question> tags.\n"
            "2.  Formulate your answer using *only* the information contained within the <context> tags.\n"
            "3.  You are allowed to perform simple reasoning based on the context. For example, you can count items in a list, identify the most recent date from data, or synthesize information from multiple sentences to answer a question.\n"
            "4.  **Crucially, if the context still does not contain the necessary information even after reasoning, you must respond with: 'I'm sorry...'**\n"
            "5.  If the user engages in small talk (e.g., 'hello', 'how are you'), provide a brief, friendly reply without mentioning the college.\n"
            "6.  Format your answers clearly using Markdown (headings, lists, bold text) for readability. Keep answers concise."
        )
    }

    user_message = {
        "role": "user",
        "content": f"<context>\n{context}\n</context>\n\n<question>\n{question}\n</question>"
    }

    try:
        client = AsyncClient()
    except Exception:
        return JSONResponse({"error": "LLM client (ollama) is not available on the server."}, status_code=500)
    
    # --- "Stream-and-Replace" Logic ---
    async def llm_stream_and_replace():
        full_response_buffer = []
        stream = await client.chat(
            model=os.getenv("OLLAMA_MODEL", "mistral"),
            messages=[system_message, user_message],
            stream=True
        )
        # First, stream the raw tokens for speed
        async for chunk in stream:
            token = chunk.get("message", {}).get("content", "")
            if token:
                yield format_sse(token, event="token")
                full_response_buffer.append(token)
        
        # Now, create the final, clean version
        complete_message = "".join(full_response_buffer)
        cleaned_message = clean_llm_output(complete_message)
        
        if cleaned_message:
            cache[question] = cleaned_message
            # Finally, send the clean version to the frontend to replace the raw one
            yield format_sse(cleaned_message, event="final_response")

    return StreamingResponse(llm_stream_and_replace(), media_type="text/event-stream", headers={"X-Response-Source": "llm"})

# --- Other endpoints remain unchanged ---
# ... (rest of your endpoints: /upload, /db_stats, etc.)
@app.post("/upload")
async def upload(files: List[UploadFile] = File(...)):
    chunks: List = []
    qa_count = 0
    raw_doc_dir = "./data/raw_docs"
    for file in files:
        dst = os.path.join(raw_doc_dir, file.filename)
        with open(dst, "wb") as f:
            shutil.copyfileobj(file.file, f)
        if dst.lower().endswith(".md"):
            with open(dst, encoding="utf-8") as f:
                text = f.read()
            for q, a in re.findall(r"Q:\s*(.*?)\nA:\s*(.*?)(?:\n{1,}|$)", text, re.DOTALL):
                knowledge_db.add_qa_pair(q.strip(), a.strip(), "")
                qa_count += 1
        file_chunks = load_and_split(dst)
        chunks.extend(file_chunks)
    if not chunks and qa_count == 0:
        raise HTTPException(400, "No processable content found in files.")
    if chunks:
        document_db.add_documents(chunks)
    return {"message": f"Uploaded {len(files)} files, indexed {len(chunks)} chunks.", "qa_indexed": qa_count}

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
    chunks: List = []
    source_dir = "./data/raw_docs"
    for fname in os.listdir(source_dir):
        full_path = os.path.join(source_dir, fname)
        chunks.extend(load_and_split(full_path))
    if chunks:
        document_db.add_documents(chunks)
    return {"message": "Vector DB reset and re-indexed"}

@app.delete("/raw_docs")
async def delete_raw(filename: str = Query(...)):
    source_dir = "./data/raw_docs"
    path = os.path.join(source_dir, filename)
    if not os.path.exists(path):
        raise HTTPException(404, f"File not found: {filename}")
    document_db.delete_documents_by_source(path)
    os.remove(path)
    return {"message": f"Deleted {filename} and its associated vectors"}

@app.post("/add_knowledge")
async def add_knowledge(payload: Dict[str, Any] = Body(...)):
    q, a, t = payload.get("question"), payload.get("answer"), payload.get("tags")
    if not q or not a:
        raise HTTPException(400, "Question & answer required")
    knowledge_db.add_qa_pair(q, a, t)
    return {"message": "Knowledge added"}

@app.get("/knowledge")
async def list_kb():
    return knowledge_db.get_all_qa_pairs()

@app.delete("/knowledge/{id}")
async def delete_kb(id: int):
    knowledge_db.delete_qa_pair(id)
    return {"message": "Deleted"}   