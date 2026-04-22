"""
Web-Scraper mit optimierter Titel-Extraktion.
"""

import logging
import re
from typing import Optional, Dict, Any

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "de,en-US;q=0.7,en;q=0.3",
}

REMOVE_SELECTORS = [
    "script", "style", "nav", "header", "footer", "aside",
    ".navigation", ".menu", ".sidebar", '[role="navigation"]'
]


def create_session_with_retries(retries=3, backoff=0.5):
    session = requests.Session()
    retry = Retry(total=retries, backoff_factor=backoff,
                  status_forcelist=[500, 502, 503, 504])
    session.mount("http://", HTTPAdapter(max_retries=retry))
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers.update(DEFAULT_HEADERS)
    return session


def fetch_html(url: str, timeout: int = 30) -> Optional[str]:
    if url.lower().endswith(".pdf"):
        return None
    try:
        resp = create_session_with_retries().get(url, timeout=timeout)
        resp.raise_for_status()
        if "application/pdf" in resp.headers.get("Content-Type", ""):
            return None
        return resp.text
    except Exception as e:
        logger.error(f"Fetch error {url}: {e}")
        return None


def extract_title_from_html(html: str) -> Optional[str]:
    """Extrahiert den Ausschreibungstitel aus HTML."""
    soup = BeautifulSoup(html, "html.parser")

    # 1. h1 mit Klasse "title", "headline", "bekanntmachung"
    for h1 in soup.find_all("h1", class_=re.compile(r"title|headline|bekanntmachung", re.I)):
        text = h1.get_text(strip=True)
        if len(text) > 20:
            return text

    # 2. erstes h1 mit relevantem Inhalt
    for h1 in soup.find_all("h1"):
        text = h1.get_text(strip=True)
        if len(text) > 30 and any(w in text.lower() for w in ["richtlinie", "bekanntmachung", "förder"]):
            return text

    # 3. h2 mit Schlüsselwörtern
    for h2 in soup.find_all("h2"):
        text = h2.get_text(strip=True)
        if len(text) > 30 and any(w in text.lower() for w in ["richtlinie", "bekanntmachung", "call"]):
            return text

    # 4. Aus Fließtext: erste Zeile mit "Bekanntmachung"
    text = soup.get_text(separator="\n", strip=True)
    for line in text.split("\n")[:30]:
        if re.search(r"Bekanntmachung|Richtlinie|Förderrichtlinie|Call for Proposals", line, re.I):
            if len(line) > 30:
                return line.strip()

    # 5. HTML-Title (bereinigt)
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
        title = re.sub(r"^Homepage\s*[-–]\s*", "", title)
        title = re.sub(r"^Navigation und Service\s*[-–]\s*", "", title)
        if len(title) > 20:
            return title

    return None


def clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for selector in REMOVE_SELECTORS:
        for el in soup.select(selector):
            el.decompose()
    text = soup.get_text(separator="\n", strip=True)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def scrape_url(url: str) -> Dict[str, Any]:
    result = {"url": url, "title": None, "text": None, "status": "error", "error": None}
    if url.lower().endswith(".pdf"):
        result["error"] = "PDF-Dateien werden derzeit nicht unterstützt."
        return result

    html = fetch_html(url)
    if not html:
        result["error"] = "HTML konnte nicht geladen werden."
        return result

    try:
        result["title"] = extract_title_from_html(html)  # kann None sein
        result["text"] = clean_html(html)
        if len(result["text"]) < 200:
            result["error"] = "Zu wenig Textinhalt"
        else:
            result["status"] = "success"
    except Exception as e:
        result["error"] = str(e)

    return result
