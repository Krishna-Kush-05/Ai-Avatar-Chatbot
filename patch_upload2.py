file_path = r'd:\Git Desk\Ai-Avatar-Chatbot\backend\app\main.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

new_helper = '''def _process_uploaded_files_sync(filepaths, workspace_id):
    import re
    from app.utils.docs_processor import load_and_split
    chunks = []
    qa_count = 0
    print(f"[{workspace_id}] Starting heavy processing for {len(filepaths)} files...")
    
    for dst in filepaths:
        print(f"[{workspace_id}] Processing file: {dst}")
        if dst.lower().endswith(".md"):
            with open(dst, encoding="utf-8") as f:
                text = f.read()
            for q, a in re.findall(r"Q:\s*(.*?)\\nA:\s*(.*?)(?:\\n{1,}|$)", text, re.DOTALL):
                knowledge_db.add_qa_pair(workspace_id, q.strip(), a.strip(), "")
                qa_count += 1
        
        file_chunks = load_and_split(dst)
        chunks.extend(file_chunks)
        print(f"[{workspace_id}] Extracted {len(file_chunks)} chunks from {dst}")
        
    if chunks:
        print(f"[{workspace_id}] Embedding and indexing {len(chunks)} total chunks...")
        document_db.add_documents(chunks, workspace_id)
        print(f"[{workspace_id}] Indexing complete!")
        
    return len(chunks), qa_count

@app.post("/upload")
async def upload(
    files: List[UploadFile] = File(...),
    workspace_id: str = Form(...)
):
    ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx"}
    MAX_FILE_SIZE = 100* 1024 * 1024  # 100 MB

    # Validation pass
    for file in files:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(400, f"Unsupported file type: {ext}")

        file_size = getattr(file, "size", None)
        if file_size is None:
            await file.seek(0, __import__('os').SEEK_END)
            file_size = file.file.tell()
            await file.seek(0)
            
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(400, f"File {file.filename} exceeds the 100MB limit.")

    raw_dir = f"./data/raw_docs/{workspace_id}"
    os.makedirs(raw_dir, exist_ok=True)
    
    saved_paths = []
    for file in files:
        dst = os.path.join(raw_dir, file.filename)
        with open(dst, "wb") as f:
            import shutil
            shutil.copyfileobj(file.file, f)
        saved_paths.append(dst)

    try:
        import asyncio
        chunks_len, qa_count = await asyncio.wait_for(
            asyncio.to_thread(_process_uploaded_files_sync, saved_paths, workspace_id),
            timeout=180.0
        )
    except asyncio.TimeoutError:
        print(f"[{workspace_id}] Timeout error during file processing.")
        raise HTTPException(504, "File processing timed out. Files were saved but might not be fully indexed.")
    except Exception as e:
        print(f"[{workspace_id}] Error during file processing: {e}")
        raise HTTPException(500, f"Error processing files: {str(e)}")

    return {
        "message": f"Uploaded {len(files)} file(s), indexed {chunks_len} chunks",
        "qa_indexed": qa_count
    }'''

start_idx = content.find('@app.post("/upload")')
end_idx = content.find('# ======================================================', start_idx)

# Replace the block
content = content[:start_idx] + new_helper + "\n\n\n" + content[end_idx:]

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
