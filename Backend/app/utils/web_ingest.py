import os
import hashlib
from typing import List
from urllib.parse import urlparse

from langchain_core.documents import Document

from app.utils.web_reader.scraper import scrape_website
from app.utils.db_manager import ChromaDBManager


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(__file__)
    )
)

RAW_DOCS_DIR = os.path.join(BASE_DIR, "data", "raw_docs")


def _chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> List[str]:
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = words[i:i + chunk_size]
        chunks.append(" ".join(chunk))
        i += chunk_size - overlap
    return chunks


def ingest_website(url: str, workspace_id: str = "default"):
    """
    Scrapes a website and stores its content in the Chroma vector DB
    under the given workspace_id.
    """
    # Validate URL format
    if not url.startswith(('http://', 'https://')):
        raise ValueError("Invalid URL. Must start with http:// or https://")

    # Scrape with specific error handling
    try:
        content = scrape_website(url)
    except Exception as e:
        raise ValueError(f"Failed to reach the website: {str(e)}. Check the URL and your internet connection.")

    # Validate scraped content
    if not content:
        raise ValueError("Could not scrape the website. The site may be blocking automated access or requires JavaScript.")
    if len(content) < 100:
        raise ValueError(f"Scraped content too short ({len(content)} characters). The page may require login, be empty, or block scrapers. Try a different URL.")

    parsed = urlparse(url)
    site_name = parsed.netloc.replace(".", "_")
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    filename = f"web_{site_name}_{url_hash}.md"

    # Save to workspace-specific folder
    workspace_dir = os.path.join(RAW_DOCS_DIR, workspace_id)
    os.makedirs(workspace_dir, exist_ok=True)
    file_path = os.path.join(workspace_dir, filename)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(f"# Source: {url}\n\n")
        f.write(content)

    chunks = _chunk_text(content)

    docs = [
        Document(
            page_content=chunk,
            metadata={
                "source": file_path,
                "type": "website",
                "url": url,
                "domain": parsed.netloc,
                "workspace_id": workspace_id
            }
        )
        for chunk in chunks
    ]

    db = ChromaDBManager()
    db.add_documents(docs, workspace_id)

    return {
        "status": "success",
        "message": f"Website ingested successfully. {len(docs)} chunks added.",
        "chunks_added": len(docs),
        "source": file_path
    }