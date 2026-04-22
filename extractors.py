import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class DeadlineExtractor:
    MONTHS_DE = {"januar": 1, "februar": 2, "märz": 3, "april": 4, "mai": 5, "juni": 6,
                 "juli": 7, "august": 8, "september": 9, "oktober": 10, "november": 11, "dezember": 12}
    PATTERNS = [
        (r"(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})", "DMY"),
        (r"(\d{1,2})\.\s*([a-zA-Zäöüß]+)\s*(\d{4})", "DMy"),
        (r"(\d{4})-(\d{1,2})-(\d{1,2})", "YMD"),
    ]
    CONTEXT = ["frist", "einreich", "deadline", "bis zum", "stichtag"]

    @classmethod
    def extract(cls, text: str) -> Optional[str]:
        if not text:
            return None
        # Header-Bereich priorisieren
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
            if style == "YMD":
                y, mo, d = int(g[0]), int(g[1]), int(g[2])
                return f"{y:04d}-{mo:02d}-{d:02d}"
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
    # Priorität: Projekt-Fördersumme, nicht Gesamtbudget
    PATTERNS = [
        r"(?:Zuwendung|Förderung|Zuschuss)\s+(?:in\s+Höhe\s+von|von|beträgt)\s+[^\d]*(\d{1,3}(?:[.,\s]?\d{3})*(?:[.,]\d+)?)\s*(?:Euro|€)",
        r"Förderhöhe\s*(?:beträgt\s*)?(?:bis\s+zu\s+)?(\d{1,3}(?:[.,\s]?\d{3})*(?:[.,]\d+)?)\s*(?:Euro|€)",
        r"(\d{1,3}(?:[.,\s]?\d{3})*(?:[.,]\d+)?)\s*(?:Mio\.?|Million)\s*(?:Euro|€)?\s*(?:pro\s+(?:Projekt|Vorhaben))?",
    ]

    @classmethod
    def extract(cls, text: str) -> Optional[str]:
        if not text:
            return None
        text_lower = text.lower()

        # Ignoriere offensichtliche Gesamtbudgets
        if "insgesamt stehen" in text_lower or "gesamthöhe" in text_lower:
            # Suche trotzdem nach projektspezifischer Angabe
            pass

        for pat in cls.PATTERNS:
            m = re.search(pat, text_lower, re.I)
            if m:
                amount = m.group(1)
                full = m.group(0)
                # Wenn "Mio" vorkommt, als Mio. € formatieren
                if re.search(r"Mio|Million", full, re.I):
                    return f"{cls._clean_number(amount)} Mio. €"
                return f"{cls._clean_number(amount)} €"
        return None

    @staticmethod
    def _clean_number(s):
        return s.replace(" ", "").replace(".", "").replace(",", ".")


class InstitutionExtractor:
    INDICATORS = [
        "Bundesministerium für Bildung und Forschung", "BMBF",
        "Bundesministerium für Forschung, Technologie und Raumfahrt", "BMFTR",
        "Bundesministerium für Wirtschaft", "BMWE", "BMWK",
        "Deutsche Forschungsgemeinschaft", "DFG",
    ]

    @classmethod
    def extract(cls, text: str) -> Optional[str]:
        if not text:
            return None
        head = text[:1500]
        for ind in cls.INDICATORS:
            if ind.lower() in head.lower():
                match = re.search(rf"({ind}[^\n]*)", head, re.I)
                if match:
                    return match.group(1).strip()
        return None


def extract_deadline(text): return DeadlineExtractor.extract(text)
def extract_funding(text): return FundingExtractor.extract(text)
def extract_institution(text): return InstitutionExtractor.extract(text)
