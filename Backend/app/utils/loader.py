# app/utils/loader.py
import os
import re
from typing import List
from langchain_community.document_loaders import PyPDFLoader, TextLoader, CSVLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


def normalize_text(text: str) -> str:
    """
    - Rejoin hyphenated line breaks (e.g. "exam-\nple" -> "example")
    - Collapse multiple whitespace/newlines into single spaces
    - Trim leading/trailing whitespace
    """
    if not text:
        return text
    # Remove soft hyphen and zero-width spaces if present
    text = text.replace("\u00AD", "")
    text = text.replace("\u200B", "")
    # Remove hyphen + newline (word broken across lines)
    text = re.sub(r'-\n\s*', '', text)
    # Collapse all whitespace characters into single spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


class SimpleMarkdownLoader:
    def __init__(self, path: str):
        self.path = path

    def load(self) -> List[Document]:
        with open(self.path, encoding="utf-8", errors="ignore") as fh:
            raw = fh.read()
        clean = normalize_text(raw)
        return [Document(page_content=clean, metadata={"source": self.path})]


def _ensure_list(docs):
    # Ensure the loader output is a list of Document objects
    if docs is None:
        return []
    if isinstance(docs, Document):
        return [docs]
    if isinstance(docs, list):
        return docs
    # Some loaders may return generator-like objects; try to coerce
    try:
        return list(docs)
    except Exception:
        return []


def load_and_split(path: str) -> List[Document]:
    """
    Load a file into Document(s), normalize text, then split into chunks.
    Returns a list of Document objects (chunks).
    """
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        loader = PyPDFLoader(path)
        docs = loader.load() if hasattr(loader, "load") else loader.load_and_split()
    elif ext == ".txt":
        loader = TextLoader(path, encoding="utf-8")
        docs = loader.load()
    elif ext == ".csv":
        loader = CSVLoader(file_path=path)
        docs = loader.load()
    elif ext == ".docx":
        loader = Docx2txtLoader(path)
        docs = loader.load()
    elif ext == ".md":
        loader = SimpleMarkdownLoader(path)
        docs = loader.load()
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    docs = _ensure_list(docs)

    # Normalize each doc's text defensively
    for d in docs:
        if getattr(d, "page_content", None) is not None:
            d.page_content = normalize_text(d.page_content)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ". ", "? ", "! ", " ", ""]
    )

    return splitter.split_documents(docs)
