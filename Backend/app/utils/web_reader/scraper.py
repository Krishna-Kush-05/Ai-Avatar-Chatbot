import hashlib
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

from app.utils.web_reader.validator import validate_url
from app.utils.web_reader.js_scraper import scrape_js_website


# -------------------------
# Text Cleaning Utilities
# -------------------------

BLACKLIST_PREFIXES = (
    "navigation", "contents", "tools",
    "edit", "jump to", "privacy", "terms",
    "cookie", "sign in", "log in", "subscribe",
    "contact", "follow us"
)


def clean_paragraph(text: str) -> str | None:
    text = text.strip()

    if len(text) < 50:
        return None

    lower = text.lower()
    if lower.startswith(BLACKLIST_PREFIXES):
        return None

    return text


def hash_text(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


# -------------------------
# Chunking
# -------------------------

def chunk_text(text: str, chunk_size: int = 700, overlap: int = 100):
    words = text.split()
    i = 0
    while i < len(words):
        yield " ".join(words[i:i + chunk_size])
        i += chunk_size - overlap


# -------------------------
# Core Scraper
# -------------------------

def scrape_to_markdown(url: str, max_pages: int = 5):
    visited = set()
    seen_blocks = set()   # deduplication
    markdown_blocks = []

    base_domain = urlparse(url).netloc

    def scrape_page(page_url: str):
        if page_url in visited or len(visited) >= max_pages:
            return

        visited.add(page_url)

        html = ""
        try:
            resp = requests.get(
                page_url,
                timeout=12,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            if resp.status_code == 200:
                html = resp.text
        except Exception:
            pass

        # JS fallback if static failed
        if not html or len(html) < 1000:
            js_html = scrape_js_website(page_url)
            html = js_html or html

        if not html:
            return

        soup = BeautifulSoup(html, "html.parser")

        # Remove junk containers
        for tag in soup(["script", "style", "nav", "footer", "aside", "noscript"]):
            tag.decompose()

        page_title = soup.title.string.strip() if soup.title else page_url

        content_blocks = []

        # Extract headings + paragraphs
        for element in soup.find_all(["h1", "h2", "h3", "p", "li"]):
            text = element.get_text(" ", strip=True)
            cleaned = clean_paragraph(text)
            if cleaned:
                content_blocks.append(cleaned)

        if not content_blocks:
            return

        full_text = "\n\n".join(content_blocks)

        # Chunk + deduplicate
        for chunk in chunk_text(full_text):
            h = hash_text(chunk)
            if h in seen_blocks:
                continue
            seen_blocks.add(h)

            markdown_blocks.append(
                f"## {page_title}\n\n{chunk}\n\n---\n"
            )

        # Follow internal links (restricted)
        for link in soup.find_all("a", href=True):
            next_url = urljoin(page_url, link["href"])
            parsed = urlparse(next_url)

            if (
                parsed.netloc == base_domain
                and not any(
                    bad in parsed.path.lower()
                    for bad in ("login", "signup", "contact", "privacy", "terms")
                )
            ):
                scrape_page(next_url)

    scrape_page(url)
    return markdown_blocks


# -------------------------
# Public API
# -------------------------

def scrape_website(url: str) -> str:
    """
    Public API used by web_ingest.py
    """
    if not validate_url(url):
        raise ValueError("Invalid URL")

    blocks = scrape_to_markdown(url, max_pages=3)
    return "\n".join(blocks)
