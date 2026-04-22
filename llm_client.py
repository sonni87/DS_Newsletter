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


class LLMClient:
    """Client für die KI:connect LLM API (OpenAI-kompatibler Endpunkt)."""

    AVAILABLE_MODELS = [
        "gpt-oss-120b",
        "mistral-small-3.2-24b-instruct-2506",
        "mistral-small-4-119b-2603",
    ]

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self._api_key = api_key
        self.base_url = base_url or os.environ.get(
            "KICONNECT_BASE_URL", "https://chat.kiconnect.nrw/api"
        ).rstrip("/")
        self.model = os.environ.get("KICONNECT_MODEL", self.AVAILABLE_MODELS[0])
        self.timeout = int(os.environ.get("KICONNECT_TIMEOUT", "60"))

    def _get_api_key(self) -> str:
        if self._api_key:
            return self._api_key
        try:
            import streamlit as st
            if hasattr(st, "secrets") and "KICONNECT_API_KEY" in st.secrets:
                return st.secrets["KICONNECT_API_KEY"]
        except (ImportError, AttributeError):
            pass
        key = os.environ.get("KICONNECT_API_KEY")
        if key:
            return key
        raise KIConnectError("KICONNECT_API_KEY nicht gefunden.")

    def _ensure_api_key(self) -> str:
        if not self._api_key:
            self._api_key = self._get_api_key()
        return self._api_key

    def list_models(self) -> List[str]:
        api_key = self._ensure_api_key()
        headers = {"Authorization": f"Bearer {api_key}"}
        try:
            response = requests.get(f"{self.base_url}/v1/models", headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            models = [m.get("id", "") for m in data.get("data", [])]
            if models:
                return models
        except Exception as e:
            logger.warning(f"Modellliste nicht abrufbar: {e}")
        return self.AVAILABLE_MODELS

    def check_connection(self) -> bool:
        try:
            api_key = self._ensure_api_key()
            response = requests.get(
                f"{self.base_url}/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10
            )
            response.raise_for_status()
            return True
        except Exception:
            return False

    def generate(self, prompt: str, system_prompt: Optional[str] = None,
                 temperature: float = 0.1, max_tokens: int = 2048) -> str:
        api_key = self._ensure_api_key()
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_completion_tokens": max_tokens,
            "stream": False
        }

        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

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
        except Exception as e:
            raise KIConnectError(f"API-Fehler: {e}")
