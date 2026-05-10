from urllib.parse import urlparse


def validate_url(url: str) -> bool:
    """
    Lightweight URL validation for web ingestion.
    Do NOT block real websites like Wikipedia or docs.
    """
    if not url:
        return False

    try:
        parsed = urlparse(url)

        # Must be http or https
        if parsed.scheme not in ("http", "https"):
            return False

        # Must have domain
        if not parsed.netloc:
            return False

        # Block obvious non-web links
        if url.startswith(("mailto:", "tel:", "javascript:", "#")):
            return False

        return True

    except Exception:
        return False
