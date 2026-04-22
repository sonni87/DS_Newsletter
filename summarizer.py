"""
Kernfunktion – Analyse eines Volltextes und Generierung des D7-Newsletter-Formats.
"""

import logging
from typing import Dict, Any, Optional

from extractors import (
    extract_deadline, extract_funding, extract_institution,
    extract_aim, extract_target_group, extract_duration
)
from llm_client import LLMClient, KIConnectError

logger = logging.getLogger(__name__)

# Prompt für Titel-Extraktion per LLM (falls nötig)
TITLE_PROMPT = """
Extrahiere den offiziellen Titel der Förderausschreibung aus folgendem Text.
Antworte NUR mit dem Titel.

TEXT:
{text}
"""

# Prompt für Aim und Target Group
CONTENT_PROMPT = """
Extrahiere aus dem folgenden Text einer Förderausschreibung zwei Informationen:

1. Aim: Das Hauptziel der Förderung. Was wird gefördert? (2-3 prägnante Sätze, auf Englisch wenn der Text englisch ist)
2. Target group: Wer ist antragsberechtigt? Welche Einrichtungen/Personen? (1-2 Sätze)

Antworte NUR im folgenden Format (keine zusätzlichen Erklärungen):
Aim: <Text>
Target group: <Text>

TEXT:
{text}
"""


def _extract_title(text: str, client: Optional[LLMClient] = None) -> str:
    """
    Versucht, den Titel per Regex zu finden, sonst per LLM.
    """
    import re
    # Suche nach typischen Titelmustern
    patterns = [
        r"Bekanntmachung\s*(?:der\s+)?(?:Richtlinie\s+)?(?:zur\s+Förderung\s+)?(?:von\s+)?([^\n]{30,200})",
        r"Richtlinie\s+(?:zur\s+Förderung\s+)?(?:von\s+)?([^\n]{30,200})",
        r"Call\s+for\s+Proposals\s*(?:[–-]\s*)?([^\n]{30,200})",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            title = m.group(1).strip()
            if len(title) > 20:
                return title

    # Fallback: erste Zeile, die wie ein Titel aussieht
    lines = text.split("\n")
    for line in lines[:10]:
        line = line.strip()
        if len(line) > 30 and any(w in line.lower() for w in ["bekanntmachung", "richtlinie", "förder", "call"]):
            return line

    # LLM-Fallback
    if client:
        try:
            prompt = TITLE_PROMPT.format(text=text[:3000])
            return client.generate(prompt, temperature=0.0, max_tokens=100).strip()
        except:
            pass
    return "Keine Angabe"


def _format_d7(title: str, institution: str, aim: str, target: str,
               duration: str, funding: str, deadline: str,
               internal: bool = False) -> str:
    """Formatiert streng nach D7-Newsletter-Standard."""
    lines = [f"## {title}\n"]
    if aim and aim != "Keine Angabe":
        lines.append(f"Aim {aim}\n")
    if target and target != "Keine Angabe":
        lines.append(f"Target group {target}\n")
    if duration and duration != "Keine Angabe":
        lines.append(f"Duration {duration}\n")
    if funding and funding != "Keine Angabe":
        lines.append(f"Funding {funding}\n")
    if deadline and deadline != "Keine Angabe":
        lines.append(f"Deadline {deadline}\n")
    lines.append("Further information website\n")
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


def summarize_text(text: str, client: Optional[LLMClient] = None) -> Dict[str, Any]:
    """
    Analysiert einen Volltext und gibt einen D7-Newsletter-Eintrag zurück.
    """
    if client is None:
        client = LLMClient()

    # API-Key prüfen (nur wenn LLM benötigt wird)
    try:
        client._ensure_api_key()
    except KIConnectError:
        # LLM ist optional, wir können trotzdem Regex-basiert weitermachen
        pass

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

    # Extraktion mit Regex
    deadline = extract_deadline(text) or "Keine Angabe"
    funding = extract_funding(text) or "Keine Angabe"
    institution = extract_institution(text) or "Keine Angabe"
    duration = extract_duration(text) or "Keine Angabe"
    aim = extract_aim(text) or "Keine Angabe"
    target = extract_target_group(text) or "Keine Angabe"

    # Titel extrahieren
    title = _extract_title(text, client)

    # Falls Aim oder Target Group "Keine Angabe" sind, LLM versuchen
    if (aim == "Keine Angabe" or target == "Keine Angabe") and client:
        try:
            prompt = CONTENT_PROMPT.format(text=text[:6000])
            llm_out = client.generate(prompt, temperature=0.1, max_tokens=400)
            for line in llm_out.split("\n"):
                if line.startswith("Aim:"):
                    aim = line[4:].strip()
                elif line.startswith("Target group:"):
                    target = line[13:].strip()
        except Exception as e:
            logger.warning(f"LLM-Fehler bei Content-Extraktion: {e}")

    internal = _needs_internal_procedure(institution)

    result["title"] = title
    result["deadline"] = deadline
    result["funding"] = funding
    result["institution"] = institution
    result["summary"] = _format_d7(
        title, institution, aim, target, duration, funding, deadline, internal
    )
    result["status"] = "success"
    return result
