"""
Streamlit Web-App für Beta-Newsletter Förderausschreibungen.
Mit Export-Funktion für die Analyse.
"""

import os
import logging
import sys
import io

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

# Session State für Ergebnisse und Modelle
if 'available_models' not in st.session_state:
    st.session_state.available_models = []
if 'selected_model' not in st.session_state:
    st.session_state.selected_model = None
if 'results' not in st.session_state:
    st.session_state.results = None
if 'processed_urls' not in st.session_state:
    st.session_state.processed_urls = []

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
    st.caption("Beta-Newsletter v0.4.0")

# Hauptbereich
url_input = st.text_area(
    "URLs (eine pro Zeile)",
    height=150,
    placeholder="https://www.foerderdatenbank.de/...\nhttps://..."
)

col1, col2, col3 = st.columns([1, 1, 3])
with col1:
    start_button = st.button("🚀 Zusammenfassungen erstellen", type="primary")
with col2:
    clear_button = st.button("🧹 Eingabe löschen")

if clear_button:
    st.session_state.results = None
    st.session_state.processed_urls = []
    st.rerun()

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
                st.session_state.results = results
                st.session_state.processed_urls = urls

            except KIConnectError as e:
                st.error(f"API-Fehler: {e}")
            except Exception as e:
                st.exception(e)
                st.error("Ein unerwarteter Fehler ist aufgetreten.")

# Ergebnisse anzeigen und Export-Button
if st.session_state.results:
    st.divider()
    st.subheader("📋 Ergebnisse")

    # Export-Button in der oberen rechten Ecke
    col_exp1, col_exp2 = st.columns([3, 1])
    with col_exp2:
        # Erstelle Markdown-Inhalt für Export
        md_content = "# Beta-Newsletter – Förderausschreibungen\n\n"
        md_content += f"Verarbeitete URLs: {len(st.session_state.processed_urls)}\n"
        md_content += f"Modell: {st.session_state.selected_model or 'Standard'}\n\n"
        md_content += "---\n\n"

        for i, res in enumerate(st.session_state.results):
            md_content += f"## {i+1}. {res.get('title', res['url'])}\n\n"
            if res["status"] == "success":
                md_content += res["summary"]
                md_content += f"\n\n**Quelle:** {res['url']}\n"
                if res.get("deadline") and res["deadline"] != "Keine Angabe":
                    md_content += f"**📅 Frist:** {res['deadline']}\n"
                if res.get("funding") and res["funding"] != "Keine Angabe":
                    md_content += f"**💰 Förderung:** {res['funding']}\n"
            else:
                md_content += f"**Fehler:** {res.get('error', 'Unbekannter Fehler')}\n"
                md_content += f"**Quelle:** {res['url']}\n"
            md_content += "\n---\n\n"

        # Download-Button
        st.download_button(
            label="📥 Ergebnisse als Markdown herunterladen",
            data=md_content,
            file_name=f"newsletter_export_{len(st.session_state.results)}_urls.md",
            mime="text/markdown"
        )

    # Ergebnisse einzeln anzeigen
    for res in st.session_state.results:
        with st.expander(f"**{res.get('title', res['url'])}**", expanded=False):
            if res["status"] == "success":
                st.markdown(res["summary"])
                st.caption(f"Quelle: {res['url']}")
                if res.get("deadline") and res["deadline"] != "Keine Angabe":
                    st.caption(f"📅 Frist: {res['deadline']}")
                if res.get("funding") and res["funding"] != "Keine Angabe":
                    st.caption(f"💰 Förderung: {res['funding']}")
            else:
                st.error(f"Fehler: {res.get('error', 'Unbekannter Fehler')}")

elif start_button:
    st.warning("Bitte URLs eingeben.")

st.sidebar.markdown("---")
st.sidebar.caption("Beta-Newsletter v0.4.0")
