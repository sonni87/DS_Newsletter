"""
Streamlit Web-App für Beta-Newsletter Förderausschreibungen.
Volltext-Analyse mit LLM (KI:connect).
"""

import logging
import sys
import streamlit as st

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

from summarizer import summarize_text
from llm_client import LLMClient, KIConnectError

st.set_page_config(
    page_title="Beta-Newsletter",
    page_icon="📰",
    layout="wide"
)

st.title("📰 Beta-Newsletter – Förderausschreibungen")
st.markdown("Volltext der Ausschreibung einfügen – die KI generiert eine Zusammenfassung im D7‑Format.")

# Session State für Modelle und Ergebnis
if 'available_models' not in st.session_state:
    st.session_state.available_models = []
if 'selected_model' not in st.session_state:
    st.session_state.selected_model = None
if 'last_result' not in st.session_state:
    st.session_state.last_result = None

# Sidebar mit Konfiguration
with st.sidebar:
    st.header("⚙️ Konfiguration")

    api_key_input = st.text_input(
        "KIConnect API-Key",
        type="password",
        placeholder="Aus Umgebungsvariable/Secrets",
        help="Wird automatisch aus Streamlit Secrets oder KICONNECT_API_KEY geladen."
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
    st.caption("Beta-Newsletter v0.6.1 – LLM-Textanalyse")

# Hauptbereich: Texteingabe
text_input = st.text_area(
    "Volltext der Ausschreibung hier einfügen:",
    height=400,
    placeholder="Den kompletten Bekanntmachungstext einfügen..."
)

col1, col2 = st.columns([1, 5])
with col1:
    analyze_btn = st.button("🔍 Text analysieren", type="primary")
with col2:
    if st.button("🧹 Eingabe löschen"):
        st.session_state.last_result = None
        st.rerun()

if analyze_btn and text_input:
    with st.spinner("Analysiere Text mit KI ..."):
        try:
            client = LLMClient(api_key=api_key_input if api_key_input else None)
            if st.session_state.selected_model:
                client.model = st.session_state.selected_model
            result = summarize_text(text_input.strip(), client=client)
            st.session_state.last_result = result
        except KIConnectError as e:
            st.error(f"API-Fehler: {e}")
        except Exception as e:
            st.exception(e)

# Ergebnis anzeigen
if st.session_state.last_result:
    st.divider()
    st.subheader("📋 D7-Newsletter-Eintrag")
    res = st.session_state.last_result
    if res["status"] == "success":
        st.markdown(res["summary"])
        # Sicherer Dateiname – auch bei None
        title = res.get('title') or "ausschreibung"
        safe_title = str(title)[:30]
        st.download_button(
            label="📥 Als Markdown herunterladen",
            data=res["summary"],
            file_name=f"{safe_title}.md",
            mime="text/markdown"
        )
    else:
        st.error(f"Fehler: {res.get('error', 'Unbekannter Fehler')}")

elif analyze_btn:
    st.warning("Bitte Text einfügen.")
