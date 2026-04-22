"""
Extraktion von Metadaten aus Webseiten-Texten.
Enthält Funktionen für Deadline, Förderbetrag, Institution etc.
"""

import re
import logging
from datetime import datetime
from typing import Optional, List, Tuple

logger = logging.getLogger(__name__)


class DeadlineExtractor:
    """Extrahiert Einreichungsfristen aus Text."""

    # Deutsche Monatsnamen
    MONTHS_DE = {
        "januar": 1, "februar": 2, "märz": 3, "april": 4, "mai": 5, "juni": 6,
        "juli": 7, "august": 8, "september": 9, "oktober": 10, "november": 11, "dezember": 12
    }

    # Patterns für verschiedene Datumsformate
    PATTERNS = [
        # 31.12.2025 oder 31. Dezember 2025
        r"(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})",
        r"(\d{1,2})\.\s*([a-zA-Zäöüß]+)\s*(\d{4})",
        # 2025-12-31
        r"(\d{4})-(\d{1,2})-(\d{1,2})",
        # 31/12/2025
        r"(\d{1,2})/(\d{1,2})/(\d{4})",
    ]

    # Indikatoren für Deadline-Kontext
    CONTEXT_WORDS = [
        "frist", "einreich", "bewerbungsschluss", "abgab", "einzureichen",
        "bis zum", "bis spätestens", "deadline", "stichtag", "ende der",
        "teilnahmeschluss", "antragsfrist"
    ]

    @classmethod
    def extract(cls, text: str) -> Optional[str]:
        """
        Extrahiert das wahrscheinlichste Deadline-Datum aus dem Text.

        Args:
            text: HTML-bereinigter Text der Webseite

        Returns:
            Datum als String im Format YYYY-MM-DD oder None
        """
        if not text:
            return None

        # Text normalisieren
        text_lower = text.lower()
        dates_found = []

        # Nach Datumsmustern suchen
        for pattern in cls.PATTERNS:
            for match in re.finditer(pattern, text_lower):
                date_str = cls._parse_match(match)
                if date_str:
                    # Kontext-Prüfung: Ist das Datum in der Nähe eines Frist-Wortes?
                    start = max(0, match.start() - 150)
                    end = min(len(text_lower), match.end() + 150)
                    context = text_lower[start:end]
                    if any(word in context for word in cls.CONTEXT_WORDS):
                        dates_found.append((date_str, match.start()))

        if not dates_found:
            return None

        # Das erste (früheste im Text) gefundene Datum mit Kontext zurückgeben
        dates_found.sort(key=lambda x: x[1])
        return dates_found[0][0]

    @classmethod
    def _parse_match(cls, match: re.Match) -> Optional[str]:
        """Parst ein Regex-Match in YYYY-MM-DD."""
        groups = match.groups()
        try:
            if len(groups) == 3:
                # Fall 1: Tag.Monat.Jahr (als Zahlen)
                if groups[0].isdigit() and groups[1].isdigit() and groups[2].isdigit():
                    day, month, year = int(groups[0]), int(groups[1]), int(groups[2])
                    if 1 <= day <= 31 and 1 <= month <= 12:
                        return f"{year:04d}-{month:02d}-{day:02d}"

                # Fall 2: Tag. Monatsname Jahr
                if groups[0].isdigit() and groups[2].isdigit():
                    day = int(groups[0])
                    year = int(groups[2])
                    month_name = groups[1].lower()
                    if month_name in cls.MONTHS_DE:
                        month = cls.MONTHS_DE[month_name]
                        return f"{year:04d}-{month:02d}-{day:02d}"

                # Fall 3: Jahr-Monat-Tag
                if groups[0].isdigit() and len(groups[0]) == 4:
                    year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                    if 1 <= month <= 12 and 1 <= day <= 31:
                        return f"{year:04d}-{month:02d}-{day:02d}"

        except ValueError:
            pass
        return None


class FundingExtractor:
    """Extrahiert Förderbeträge aus Text."""

    # Pattern für Geldbeträge mit Einheiten
    AMOUNT_PATTERN = re.compile(
        r"(\d+(?:[.,]\d+)?)\s*(?:€|EUR|Euro|Mio\.?\s*€|Millionen?\s*Euro|Mrd\.?\s*€|Milliarden?\s*Euro)",
        re.IGNORECASE
    )

    @classmethod
    def extract(cls, text: str) -> Optional[str]:
        """
        Extrahiert den Förderbetrag als bereinigten String.

        Returns:
            Z.B. "500.000 €" oder "2,5 Mio. €"
        """
        if not text:
            return None

        matches = list(cls.AMOUNT_PATTERN.finditer(text))
        if not matches:
            return None

        # Den ersten Betrag im Text nehmen (meist der relevanteste)
        match = matches[0]
        amount_str = match.group(0)
        # Normalisieren
        amount_str = amount_str.replace("EUR", "€").replace("Euro", "€")
        amount_str = re.sub(r"\s+", " ", amount_str).strip()
        return amount_str


class InstitutionExtractor:
    """Extrahiert den Namen der fördernden Institution."""

    # Typische Indikatoren für Institutionen
    INDICATORS = [
        "ministerium", "stiftung", "fonds", "agentur", "institut", "zentrum",
        "förder", "projektträger", "bundesamt", "landesamt", "gmbh", "e.v.", "e. v."
    ]

    @classmethod
    def extract(cls, text: str) -> Optional[str]:
        """Extrahiert die wahrscheinlichste Institution."""
        # Einfache Heuristik: Suche nach typischen Begriffen im ersten Drittel des Textes
        if not text:
            return None

        first_part = text[: len(text) // 3]
        lines = first_part.split("\n")

        for line in lines:
            line_lower = line.lower()
            if any(ind in line_lower for ind in cls.INDICATORS):
                # Bereinigen
                clean = re.sub(r"\s+", " ", line).strip()
                if len(clean) < 100:  # plausible Länge
                    return clean
        return None


# Wrapper-Funktionen für einfache Nutzung
def extract_deadline(text: str) -> Optional[str]:
    return DeadlineExtractor.extract(text)


def extract_funding(text: str) -> Optional[str]:
    return FundingExtractor.extract(text)


def extract_institution(text: str) -> Optional[str]:
    return InstitutionExtractor.extract(text)