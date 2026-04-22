"""
Kernfunktion: URLs scrapen, LLM-Zusammenfassung generieren.
"""

import logging
from typing import List, Dict, Any, Optional

from scraper import scrape_url
from extractors import extract_deadline, extract_funding, extract_institution
from llm_client import LLMClient, KIConnectError

logger = logging.getLogger(__name__)

SUMMARY_PROMPT_TEMPLATE = """
Du bist ein Experte für Fördermittel und erstellst präzise Zusammenfassungen von Ausschreibungen.

Analysiere den folgenden Text einer Förderausschreibung und extrahiere die wichtigsten Informationen.

TEXT:
{text}

Erstelle eine strukturierte Zusammenfassung im folgenden Format:

**Titel der Ausschreibung:** (falls erkennbar)
**Förderinstitution:** {institution}
**Einreichungsfrist:** {deadline}
**Fördersumme:** {funding}
**Zielgruppe:** (wer kann sich bewerben?)
**Fördergegenstand:** (was wird gefördert?)
**Wichtige Bedingungen:** (besondere Voraussetzungen)

Falls bestimmte Informationen nicht im Text enthalten sind, schreibe "Keine Angabe".

Antworte ausschließlich mit der formatierten Zusammenfassung, ohne zusätzliche Erklärungen.
"""


def summarize_urls(urls: List[str], client: Optional[LLMClient] = None) -> List[Dict[str, Any]]:
    if client is None:
        client = LLMClient()

    # API-Key prüfen
    try:
        client._ensure_api_key()
    except KIConnectError as e:
        raise KIConnectError(
            "Kein API-Key konfiguriert. Bitte in der Seitenleiste eingeben."
        ) from e

    if not client.check_connection():
        raise KIConnectError("Keine Verbindung zur LLM-API möglich.")

    results = []

    for url in urls:
        logger.info(f"Verarbeite {url}")
        result = {
            "url": url,
            "title": None,
            "summary": None,
            "deadline": None,
            "funding": None,
            "institution": None,
            "status": "error",
            "error": None
        }

        scraped = scrape_url(url)
        if scraped["status"] != "success":
            result["error"] = scraped.get("error", "Scraping fehlgeschlagen")
            results.append(result)
            continue

        text = scraped["text"]
        result["title"] = scraped["title"]

        if not text or len(text) < 200:
            result["error"] = "Zu wenig Textinhalt für Zusammenfassung"
            results.append(result)
            continue

        deadline = extract_deadline(text)
        funding = extract_funding(text)
        institution = extract_institution(text)

        result["deadline"] = deadline
        result["funding"] = funding
        result["institution"] = institution

        max_text_length = 8000
        text_snippet = text[:max_text_length] + ("..." if len(text) > max_text_length else "")

        prompt = SUMMARY_PROMPT_TEMPLATE.format(
            text=text_snippet,
            institution=institution or "Unbekannt",
            deadline=deadline or "Keine Angabe",
            funding=funding or "Keine Angabe"
        )

        try:
            summary = client.generate(prompt, temperature=0.2, max_tokens=1024)
            result["summary"] = summary.strip()
            result["status"] = "success"
        except KIConnectError as e:
            result["error"] = f"LLM-Fehler: {e}"
            logger.error(f"LLM-Fehler für {url}: {e}")
        except Exception as e:
            result["error"] = f"Unerwarteter Fehler: {e}"
            logger.exception(f"Unerwarteter Fehler bei {url}")

        results.append(result)

    return results
