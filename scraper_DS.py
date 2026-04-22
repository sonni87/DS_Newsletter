"""
Web-Scraper mit Retry-Logik und HTML-Bereinigung.
"""

import logging
import time
import re
from typing import Optional, Dict, Any
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

# Standard-Header für realistischere Anfragen
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "de,en-US;q=0.7,en;q=0.3",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# Elemente, die beim Text-Cleaning entfernt werden
REMOVE_SELECTORS = [
    "script", "style", "nav", "header", "footer", "aside",
    ".navigation", ".menu", ".sidebar", ".advertisement", ".cookie",
    '[role="navigation"]', '[role="banner"]', '[role="contentinfo"]'
]


def create_session_with_retries(
    retries: int = 3,
    backoff_factor: float = 0.5,
    status_forcelist: tuple = (500, 502, 503, 504)
) -> requests.Session:
    """
    Erstellt eine requests Session mit automatischer Wiederholung bei Fehlern.
    """
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update(DEFAULT_HEADERS)
    return session


def fetch_html(url: str, timeout: int = 30) -> Optional[str]:
    """
    Lädt HTML-Inhalt einer URL mit Retry-Logik.

    Returns:
        HTML als String oder None bei Fehler
    """
    session = create_session_with_retries()
    try:
        response = session.get(url, timeout=timeout)
        response.raise_for_status()

        # Encoding erkennen
        if response.encoding is None:
            response.encoding = "utf-8"

        return response.text

    except requests.exceptions.RequestException as e:
        logger.error(f"Fehler beim Abrufen von {url}: {e}")
        return None


def clean_html(html: str) -> str:
    """
    Bereinigt HTML und extrahiert den Haupttext.

    Args:
        html: Roher HTML-String

    Returns:
        Bereinigter Text ohne Navigation, Header, Footer etc.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Unerwünschte Elemente entfernen
    for selector in REMOVE_SELECTORS:
        for element in soup.select(selector):
            element.decompose()

    # Text extrahieren und säubern
    text = soup.get_text(separator="\n", strip=True)

    # Mehrfache Zeilenumbrüche reduzieren
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    text = re.sub(r" +", " ", text)

    return text.strip()


def scrape_url(url: str) -> Dict[str, Any]:
    """
    Hauptfunktion: Scraped eine URL und liefert bereinigten Text + Metadaten.

    Returns:
        Dictionary mit 'url', 'title', 'text', 'status'
    """
    result = {
        "url": url,
        "title": None,
        "text": None,
        "status": "error",
        "error": None
    }

    html = fetch_html(url)
    if html is None:
        result["error"] = "HTML konnte nicht geladen werden"
        return result

    try:
        soup = BeautifulSoup(html, "html.parser")
        if soup.title:
            result["title"] = soup.title.string.strip() if soup.title.string else None

        result["text"] = clean_html(html)
        result["status"] = "success"
        logger.info(f"Erfolgreich gescraped: {url}")

    except Exception as e:
        logger.exception(f"Fehler beim Parsen von {url}")
        result["error"] = str(e)

    return result