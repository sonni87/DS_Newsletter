"""
LLM Client für die KI:connect API (Universität zu Köln / NRW).
API-Dokumentation: https://chat.kiconnect.nrw/app/api-docs/
"""

import os
import logging
from typing import Optional, List

import requests

logger = logging.getLogger(__name__)


class KIConnectError(Exception):
    """Basisklasse für API-Fehler."""
    pass


OllamaError = KIConnectError


class LLMClient:
    """Client für die KI:connect LLM API (OpenAI-kompatibler Endpunkt)."""

    # Verfügbare Modelle laut KI:connect Dokumentation (Fallback)
    AVAILABLE_MODELS = [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-o3-mini",
        "llama-3.3-70b",
        "mistral-large",
    ]

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialisiert den Client. Der API-Key wird erst bei Bedarf geladen.

        Args:
            api_key: API-Schlüssel (wenn None, wird aus Umgebungsvariable/Secrets gelesen)
            base_url: Basis-URL der API (wenn None, wird Standard verwendet)
        """
        self._api_key = api_key
        # Standard-Basis-URL ist die KI:connect API
        self.base_url = base_url or os.environ.get(
            "KICONNECT_BASE_URL", "https://chat.kiconnect.nrw/api"
        ).rstrip("/")
        # Standardmodell: GPT-4o (kann per Umgebungsvariable überschrieben werden)
        self.model = os.environ.get("KICONNECT_MODEL", "gpt-4o")
        self.timeout = int(os.environ.get("KICONNECT_TIMEOUT", "60"))

    def _get_api_key(self) -> str:
        """Liest API-Key aus Umgebungsvariable oder Streamlit-Secrets."""
        if self._api_key:
            return self._api_key

        # Für Streamlit-Umgebung
        try:
            import streamlit as st
            if hasattr(st, "secrets") and "KICONNECT_API_KEY" in st.secrets:
                return st.secrets["KICONNECT_API_KEY"]
        except (ImportError, AttributeError):
            pass

        # Für Umgebungsvariable
        key = os.environ.get("KICONNECT_API_KEY")
        if key:
            return key

        raise KIConnectError(
            "KICONNECT_API_KEY nicht gefunden. "
            "Bitte in der Seitenleiste eingeben oder als Umgebungsvariable setzen.\n"
            "API-Key kann im KI:connect Administrations-Backend generiert werden.\n"
            "Bei Fragen: servicedesk@itc.rwth-aachen.de"
        )

    def _ensure_api_key(self) -> str:
        """Gibt den API-Key zurück; lädt ihn bei Bedarf nach."""
        if not self._api_key:
            self._api_key = self._get_api_key()
        return self._api_key

    def list_models(self) -> List[str]:
        """
        Ruft die Liste der verfügbaren Modelle von der API ab.

        Returns:
            Liste von Modellnamen

        Raises:
            KIConnectError: Bei API-Fehlern
        """
        api_key = self._ensure_api_key()
        headers = {"Authorization": f"Bearer {api_key}"}

        try:
            response = requests.get(
                f"{self.base_url}/v1/models",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            models = [m.get("id", "") for m in data.get("data", [])]
            return models
        except Exception as e:
            logger.warning(f"Konnte Modellliste nicht abrufen: {e}")
            # Fallback auf statische Liste
            return self.AVAILABLE_MODELS

    def check_connection(self) -> bool:
        """
        Prüft, ob die API erreichbar und der API-Key gültig ist.

        Returns:
            True wenn Verbindung erfolgreich, sonst False
        """
        try:
            api_key = self._ensure_api_key()
            # Testaufruf an den Models-Endpunkt
            response = requests.get(
                f"{self.base_url}/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10
            )
            response.raise_for_status()
            logger.info("KI:connect API-Verbindung erfolgreich getestet.")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"API-Verbindungstest fehlgeschlagen: {e}")
            return False
        except KIConnectError:
            return False

    def generate(self, prompt: str, system_prompt: Optional[str] = None,
                 temperature: float = 0.1, max_tokens: int = 2048) -> str:
        """
        Sendet einen Prompt an die KI:connect API und gibt die Antwort zurück.

        Args:
            prompt: Der Benutzer-Prompt
            system_prompt: Optionaler System-Prompt
            temperature: Kreativitätsparameter (0.0 - 2.0)
            max_tokens: Maximale Anzahl der Ausgabetoken

        Returns:
            Generierter Text

        Raises:
            KIConnectError: Bei API-Fehlern oder Timeout
        """
        api_key = self._ensure_api_key()
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_completion_tokens": max_tokens,  # KI:connect verwendet max_completion_tokens
            "stream": False
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

        except requests.exceptions.Timeout:
            logger.error(f"API-Timeout nach {self.timeout}s")
            raise KIConnectError(f"API-Anfrage Timeout nach {self.timeout} Sekunden")
        except requests.exceptions.HTTPError as e:
            error_detail = ""
            try:
                error_detail = response.json()
            except:
                error_detail = response.text
            logger.error(f"API-Fehler {response.status_code}: {error_detail}")
            raise KIConnectError(f"API-Fehler {response.status_code}: {error_detail}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Netzwerkfehler: {e}")
            raise KIConnectError(f"Netzwerkfehler: {e}")
        except KeyError as e:
            logger.error(f"Unerwartete API-Antwortstruktur: {e}")
            raise KIConnectError(f"Unerwartete API-Antwort: {e}")
        except Exception as e:
            logger.exception("Unbekannter Fehler bei API-Anfrage")
            raise KIConnectError(f"Unbekannter Fehler: {e}")


def generate_summary(prompt: str, client: Optional[LLMClient] = None) -> str:
    """Wrapper-Funktion für einfache Nutzung."""
    if client is None:
        client = LLMClient()
    return client.generate(prompt)
