"""
Kernfunktion – Sendet Volltext an LLM und formatiert die Antwort.
"""

import logging
from typing import Dict, Any, Optional

from extractors import extract_deadline, extract_institution
from llm_client import LLMClient, KIConnectError

logger = logging.getLogger(__name__)

# Der Prompt ist exakt an Ihren erfolgreichen manuellen Prompt angelehnt
LLM_PROMPT = """
Du bist Experte für Forschungsförderung und erstellst Einträge für einen Fördernewsletter einer Universität (D7-Format).
Analysiere den folgenden Text einer Förderausschreibung und erstelle eine kurze, strukturierte Zusammenfassung.

TEXT:
{text}

Die Zusammenfassung MUSS folgende Felder enthalten (verwende GENAU diese Feldbezeichnungen):

**Förderung:** (1-2 Sätze: Was wird gefördert? Welche Kosten sind förderfähig? Gibt es Personalkostenregelungen?)
**Zielgruppe:** (Wer ist antragsberechtigt? Welche Einrichtungen/Personen?)
**Dauer:** (Projektlaufzeit. Falls nicht explizit genannt, schreibe "Keine Angabe".)
**Förderhöhe:** (Maximale Fördersumme oder Prozentangabe. Falls nicht genannt, schreibe "Keine Angabe".)
**Fristende:** (Einreichungsfrist. Falls nicht genannt, schreibe "Keine Angabe".)
**Website / Kontakt:** (URL oder E-Mail, falls vorhanden. Sonst "Keine Angabe".)

Antworte NUR mit den formatierten Feldern. Keine zusätzlichen Erklärungen.
"""


def _format_d7(llm_output: str, institution: str, deadline: str, internal: bool) -> str:
    """Formatiert die LLM-Ausgabe mit zusätzlichen Metadaten."""
    lines = []
    # Titel wird vom LLM nicht explizit verlangt, kann aber im Prompt ergänzt werden.
    # Wir setzen hier einen Platzhalter – oder Sie erweitern den Prompt um **Titel:**.
    lines.append("## Förderausschreibung\n")
    lines.append(llm_output.strip())
    lines.append("")  # Leerzeile
    if institution and institution != "Keine Angabe":
        lines.append(f"**Förderinstitution:** {institution}")
    if deadline and deadline != "Keine Angabe":
        lines.append(f"**Fristende (extrahiert):** {deadline}")
    if internal:
        lines.append("\n**INTERNES VERFAHREN:** Bitte beachten Sie, dass das Antragsformular von einer bevollmächtigten Vertretung der Universität unterschrieben werden muss („rechtsverbindliche Unterschrift“). Wenden Sie sich daher bitte an die Abteilung 73 – Nationale Förderung, sobald Sie sich für eine Antragstellung entschieden haben (a73_Antrag@verw.uni-koeln.de).")
    return "\n".join(lines)


def _needs_internal_procedure(institution: str) -> bool:
    if not institution:
        return False
    inst_lower = institution.lower()
    return any(x in inst_lower for x in ["bmbf", "bmftr", "bmwe", "bmwk", "bundesministerium"])


def summarize_text(text: str, client: Optional[LLMClient] = None) -> Dict[str, Any]:
    if client is None:
        client = LLMClient()

    try:
        client._ensure_api_key()
    except KIConnectError as e:
        raise KIConnectError("Kein API-Key konfiguriert.") from e

    if not client.check_connection():
        raise KIConnectError("Keine Verbindung zur LLM-API möglich.")

    result = {
        "title": None,
        "summary": None,
        "deadline": None,
        "funding": None,
        "institution": None,
        "status": "error",
        "error": None
    }

    if not text or len(text) < 200:
        result["error"] = "Text ist zu kurz (min. 200 Zeichen)."
        return result

    # 1. Deadline und Institution per Regex (zuverlässiger als LLM für diese Felder)
    deadline = extract_deadline(text) or "Keine Angabe"
    institution = extract_institution(text) or "Keine Angabe"

    # 2. LLM-Aufruf für den Inhalt
    try:
        prompt = LLM_PROMPT.format(text=text[:8000])  # Längenbeschränkung für API
        llm_output = client.generate(prompt, temperature=0.1, max_tokens=600)
        internal = _needs_internal_procedure(institution)
        result["summary"] = _format_d7(llm_output, institution, deadline, internal)
        result["status"] = "success"
    except Exception as e:
        logger.exception("LLM-Fehler")
        result["error"] = f"LLM-Fehler: {e}"

    result["deadline"] = deadline
    result["institution"] = institution
    return result
