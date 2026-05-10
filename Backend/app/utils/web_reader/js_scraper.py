def scrape_js_website(url: str) -> str:
    """
    Hybrid JS renderer:
    - Uses Playwright ONLY if installed
    - Returns empty string if not available
    - Never crashes the backend
    """

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        # Playwright not installed → skip JS rendering
        return ""

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=60000)
            page.wait_for_timeout(3000)

            content = page.inner_text("body")
            browser.close()
            return content

    except Exception:
        return ""
