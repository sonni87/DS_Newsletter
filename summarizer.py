"""
Kernfunktion – generiert Ausgabe im D7-Newsletter-Format.
"""

import logging
from typing import List, Dict, Any, Optional

from scraper import scrape_url
from extractors import (
    extract_deadline, extract_funding, extract_institution,
    extract_aim, extract_target_group, extract_duration
)
from llm_client import LLMClient, KIConnectError

logger = logging.getLogger(__name__)


def _format_d7(title: str, institution: str, aim: str, target: str,
               duration: str, funding: str, deadline: str, url: str,
               internal: bool = False) -> str:
    """Formatiert nach D7-Newsletter-Standard."""
    lines = [f"## {title}\n"]
    if aim:
        lines.append(f"Aim {aim}\n")
    if target:
        lines.append(f"Target group {target}\n")
    if duration:
        lines.append(f"Duration {duration}\n")
    if funding:
        lines.append(f"Funding {funding}\n")
    if deadline:
        lines.append(f"Deadline {deadline}\n")
    lines.append(f"Further information website\n")
    if internal:
        lines.append("\nINTERNAL PROCEDURE: Please note that the application form must be signed "
                     "by an authorised representative of the university (in German: \"rechtsverbindliche Unterschrift\"). "
                     "Therefore, please contact Department 73 - National Funding as soon as you decide to write a proposal "
                     "(a73_Antrag@verw.uni-koeln.de) to arrange an appointment for support in the preparation of the proposal.\n")
    lines.append("\n---")
    return "\n".join(lines)


def _needs_internal_procedure(institution: str) -> bool:
    if not institution:
        return False
    inst_lower = institution.lower()
    return any(x in inst_lower for x in ["bmbf", "bmftr", "bmwe", "bmwk", "bundesministerium"])


def summarize_urls(urls: List[str], client: Optional[LLMClient] = None) -> List[Dict[str, Any]]:
    if client is None:
        client = LLMClient()

    try:
        client._ensure_api_key()
    except KIConnectError as e:
        raise KIConnectError("Kein API-Key konfiguriert.") from e

    if not client.check_connection():
        raise KIConnectError("Keine Verbindung zur LLM-API möglich.")

    results = []
    for url in urls:
        logger.info(f"Verarbeite {url}")
        result = {"url": url, "title": None, "summary": None, "deadline": None,
                  "funding": None, "institution": None, "status": "error", "error": None}

        scraped = scrape_url(url)
        if scraped["status"] != "success":
            result["error"] = scraped.get("error", "Scraping fehlgeschlagen")
            results.append(result)
            continue

        text = scraped["text"]
        title = scraped["title"]
        if len(text) < 200:
            result["error"] = "Zu wenig Textinhalt"
            results.append(result)
            continue

        deadline = extract_deadline(text) or "Keine Angabe"
        funding = extract_funding(text) or "Keine Angabe"
        institution = extract_institution(text) or "Keine Angabe"
        aim = extract_aim(text) or "Keine Angabe"
        target = extract_target_group(text) or "Keine Angabe"
        duration = extract_duration(text) or "Keine Angabe"

        result["deadline"] = deadline
        result["funding"] = funding
        result["institution"] = institution

        internal = _needs_internal_procedure(institution)

        result["summary"] = _format_d7(
            title, institution, aim, target, duration, funding, deadline, url, internal
        )
        result["status"] = "success"
        results.append(result)

    return results
