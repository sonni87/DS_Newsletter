"""
Streamlit Web-App für Beta-Newsletter Förderausschreibungen.
"""

import os
import logging
import sys

import streamlit as st

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

from summarizer import summarize_urls
from llm_client import LLMClient, KIConnectError

st.set_page_config(
    page_title="Beta-Newsletter",
    page_icon="📰",
    layout="wide"
)

st.title("📰 Beta-Newsletter – Förderausschreibungen")
st.markdown("Gib URLs zu Förderausschreibungen ein und erhalte KI-generierte Zusammenfassungen.")

# Session State für Modelle
if 'available_models' not in st.session_state:
    st.session_state.available_models = []
if 'selected_model' not in st.session_state:
    st.session_state.selected_model = None

with st.sidebar:
    st.header("⚙️ Konfiguration")

    api_key_input = st.text_input(
        "KIConnect API-Key",
        type="password",
        placeholder="Aus Umgebungsvariable/Secrets",
        help="API-Key hier eingeben oder als KICONNECT_API_KEY setzen."
    )

    if st.button("🔌 API-Verbindung testen & Modelle laden"):
        try:
            client = LLMClient(api_key=api_key_input if api_key_input else None)
            if client.check_connection():
                st.success("✅ Verbindung erfolgreich!")
                models = client.list_models()
                st.session_state.available_models = models
                st.success(f"✅ {len(models)} Modelle geladen!")
            else:
                st.error("❌ Verbindung fehlgeschlagen.")
        except Exception as e:
            st.error(f"❌ Fehler: {e}")

    if st.session_state.available_models:
        st.divider()
        st.subheader("🤖 Modellauswahl")
        if st.session_state.selected_model not in st.session_state.available_models:
            st.session_state.selected_model = st.session_state.available_models[0]

        st.session_state.selected_model = st.selectbox(
            "Wähle ein Modell:",
            options=st.session_state.available_models,
            index=st.session_state.available_models.index(st.session_state.selected_model)
        )
        st.markdown(f"**Aktives Modell:** `{st.session_state.selected_model}`")
    else:
        st.divider()
        st.markdown("**Keine Modelle geladen. Bitte Verbindung testen.**")

    st.divider()
    st.markdown("---")
    st.caption("Beta-Newsletter v0.3.0")

# Hauptbereich
url_input = st.text_area(
    "URLs (eine pro Zeile)",
    height=150,
    placeholder="https://www.foerderdatenbank.de/...\nhttps://..."
)

col1, col2 = st.columns([1, 5])
with col1:
    start_button = st.button("🚀 Zusammenfassungen erstellen", type="primary")

if start_button and url_input:
    urls = [url.strip() for url in url_input.splitlines() if url.strip()]

    if not urls:
        st.warning("Bitte mindestens eine URL eingeben.")
    else:
        with st.spinner("Verarbeite URLs... Dies kann einige Minuten dauern."):
            try:
                client = LLMClient(api_key=api_key_input if api_key_input else None)
                if st.session_state.selected_model:
                    client.model = st.session_state.selected_model

                results = summarize_urls(urls, client=client)

                for res in results:
                    with st.expander(f"**{res.get('title', res['url'])}**", expanded=True):
                        if res["status"] == "success":
                            st.markdown(res["summary"])
                            st.caption(f"Quelle: {res['url']}")
                            if res.get("deadline"):
                                st.caption(f"📅 Frist: {res['deadline']}")
                            if res.get("funding"):
                                st.caption(f"💰 Förderung: {res['funding']}")
                        else:
                            st.error(f"Fehler: {res.get('error', 'Unbekannter Fehler')}")

            except KIConnectError as e:
                st.error(f"API-Fehler: {e}")
            except Exception as e:
                st.exception(e)
                st.error("Ein unerwarteter Fehler ist aufgetreten.")

elif start_button:
    st.warning("Bitte URLs eingeben.")
