"""
Extraktion von Metadaten – robuste Muster für D7-Newsletter.
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class DeadlineExtractor:
    MONTHS_DE = {"januar": 1, "februar": 2, "märz": 3, "april": 4, "mai": 5, "juni": 6,
                 "juli": 7, "august": 8, "september": 9, "oktober": 10, "november": 11, "dezember": 12}
    MONTHS_EN = {"january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
                 "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12}

    PATTERNS = [
        (r"(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})", "DMY"),
        (r"(\d{1,2})\.\s*([a-zA-Zäöüß]+)\s*(\d{4})", "DMy"),
        (r"(\d{4})-(\d{1,2})-(\d{1,2})", "YMD"),
        (r"(\d{1,2})/(\d{1,2})/(\d{4})", "MDY"),
        (r"([a-zA-Z]+)\s+(\d{1,2}),?\s*(\d{4})", "MDY_en"),
    ]

    CONTEXT = ["frist", "einreich", "deadline", "bis zum", "stichtag", "submission", "due date"]

    @classmethod
    def extract(cls, text: str) -> Optional[str]:
        if not text:
            return None
        # Header-Bereich
        header = re.search(r"(\d{2}\.\d{2}\.\d{4})\s*[-–]\s*(\d{2}\.\d{2}\.\d{4})", text)
        if header:
            return cls._parse_date_str(header.group(2))

        text_lower = text.lower()
        dates = []
        for pat, style in cls.PATTERNS:
            for m in re.finditer(pat, text_lower):
                date = cls._parse_match(m, style)
                if date:
                    ctx = text_lower[max(0, m.start()-150):m.end()+150]
                    if any(w in ctx for w in cls.CONTEXT):
                        dates.append((date, m.start()))
        if dates:
            dates.sort(key=lambda x: x[1])
            return dates[0][0]
        return None

    @classmethod
    def _parse_match(cls, m, style):
        g = m.groups()
        try:
            if style == "DMY":
                d, mo, y = int(g[0]), int(g[1]), int(g[2])
                return f"{y:04d}-{mo:02d}-{d:02d}"
            if style == "DMy":
                d, mon, y = int(g[0]), g[1].lower(), int(g[2])
                if mon in cls.MONTHS_DE:
                    return f"{y:04d}-{cls.MONTHS_DE[mon]:02d}-{d:02d}"
                if mon in cls.MONTHS_EN:
                    return f"{y:04d}-{cls.MONTHS_EN[mon]:02d}-{d:02d}"
            if style == "YMD":
                y, mo, d = int(g[0]), int(g[1]), int(g[2])
                return f"{y:04d}-{mo:02d}-{d:02d}"
            if style == "MDY":
                mo, d, y = int(g[0]), int(g[1]), int(g[2])
                return f"{y:04d}-{mo:02d}-{d:02d}"
            if style == "MDY_en":
                mon, d, y = g[0].lower(), int(g[1]), int(g[2])
                if mon in cls.MONTHS_EN:
                    return f"{y:04d}-{cls.MONTHS_EN[mon]:02d}-{d:02d}"
        except:
            pass
        return None

    @classmethod
    def _parse_date_str(cls, s):
        m = re.match(r"(\d{2})\.(\d{2})\.(\d{4})", s)
        if m:
            return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
        return None


class FundingExtractor:
    """
    Extrahiert die projektbezogene Förderhöhe (ignoriert Gesamtbudgets).
    """
    PATTERNS = [
        r"Funding\s*(?:up\s+to\s+)?\d{1,3}%\s+of\s+(?:the\s+)?eligible\s+(?:project-?related\s+)?expenses(?:\s+as\s+well\s+as\s+a\s+project\s+lump\s+sum\s+of\s+\d{1,2}%)?",
        r"Förderhöhe\s*(?:bis\s+zu\s+)?\d{1,3}%\s+der\s+zuwendungsfähigen\s+(?:projektbezogenen\s+)?Ausgaben(?:\s+sowie\s+eine\s+Projektpauschale\s+in\s+Höhe\s+von\s+\d{1,2}%)?",
        r"Funding\s*:?\s*up\s+to\s+€?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)\s*(?:Euro|€|EUR)?(?:\s*\([^)]+\))?",
        r"Förderhöhe\s*:?\s*bis\s+zu\s+(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)\s*(?:Euro|€|EUR)?",
        r"Zuwendung\s+von\s+(\d{1,3}(?:\s\d{3})*(?:[.,]\d+)?)\s+Euro",
    ]

    IGNORE = ["insgesamt stehen", "Gesamtbudget", "total budget", "Maßnahme stehen"]

    @classmethod
    def extract(cls, text: str) -> Optional[str]:
        if not text:
            return None
        text_lower = text.lower()
        # Ignorieren wir nicht komplett, aber priorisieren projektbezogene Angaben
        for pat in cls.PATTERNS:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                if m.groups():
                    return m.group(1).strip()
                return m.group(0).strip()
        return None


class InstitutionExtractor:
    INDICATORS = [
        r"Bundesministerium\s+für\s+(?:Bildung\s+und\s+Forschung|Forschung,\s+Technologie\s+und\s+Raumfahrt|Wirtschaft\s+und\s+Energie|Umwelt)[^,\n]*",
        r"Federal\s+Ministry\s+of\s+(?:Research,\s+Technology\s+and\s+Space|Education\s+and\s+Research|Economic\s+Affairs\s+and\s+Energy)[^,\n]*",
        r"BMBF|BMFTR|BMWE|BMWK|BMUV",
        r"Deutsche\s+Forschungsgemeinschaft|DFG",
        r"European\s+Research\s+Council|ERC",
    ]

    @classmethod
    def extract(cls, text: str) -> Optional[str]:
        if not text:
            return None
        head = text[:1500]
        for pat in cls.INDICATORS:
            m = re.search(pat, head, re.I)
            if m:
                return m.group(0).strip()
        return None


class AimExtractor:
    PATTERNS = [
        r"Aim\s*(?:of\s+the\s+funding\s+measure\s+is\s+to\s+)?([^\n]{50,300})",
        r"Ziel\s+der\s+Förderung\s+ist\s+es,?\s+([^\n]{50,300})",
        r"The\s+purpose\s+of\s+this\s+funding\s+measure\s+is\s+to\s+([^\n]{50,300})",
    ]

    @classmethod
    def extract(cls, text: str) -> Optional[str]:
        if not text:
            return None
        for pat in cls.PATTERNS:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        return None


class TargetGroupExtractor:
    PATTERNS = [
        r"Target\s+group\s*:?\s*([^\n]{20,200})",
        r"Zielgruppe\s*:?\s*([^\n]{20,200})",
        r"Antragsberechtigt\s+sind\s+([^\n]{20,200})",
    ]

    @classmethod
    def extract(cls, text: str) -> Optional[str]:
        if not text:
            return None
        for pat in cls.PATTERNS:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        return None


class DurationExtractor:
    PATTERNS = [
        r"(?:Duration|Dauer)\s*(?:up\s+to\s+|bis\s+zu\s+)?(\d+(?:\s*[-–]\s*\d+)?\s*(?:years?|months?|Jahre?|Monate?))",
        r"(\d+\s*(?:years?|Jahre?))\s+(?:funding\s+period|Laufzeit)",
    ]

    @classmethod
    def extract(cls, text: str) -> Optional[str]:
        if not text:
            return None
        for pat in cls.PATTERNS:
            m = re.search(pat, text, re.I)
            if m:
                return m.group(1).strip()
        return None


# Wrapper-Funktionen für einfachen Import
def extract_deadline(text: str) -> Optional[str]:
    return DeadlineExtractor.extract(text)

def extract_funding(text: str) -> Optional[str]:
    return FundingExtractor.extract(text)

def extract_institution(text: str) -> Optional[str]:
    return InstitutionExtractor.extract(text)

def extract_aim(text: str) -> Optional[str]:
    return AimExtractor.extract(text)

def extract_target_group(text: str) -> Optional[str]:
    return TargetGroupExtractor.extract(text)

def extract_duration(text: str) -> Optional[str]:
    return DurationExtractor.extract(text)
