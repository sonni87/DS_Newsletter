"""
Streamlit App – Einfacher Prompt-Client für KI:connect mit Markdown-Export.
"""

import streamlit as st
from llm_client import LLMClient, KIConnectError

st.set_page_config(page_title="KI:connect Prompt", page_icon="🤖", layout="wide")
st.title("🤖 KI:connect – Flexibler Prompt‑Client")
st.markdown("Gib deinen Prompt und den Ausschreibungstext ein. Die Antwort wird im Markdown‑Format ausgegeben und kann exportiert werden.")

# Session State
if "response" not in st.session_state:
    st.session_state.response = ""
if "available_models" not in st.session_state:
    st.session_state.available_models = []
if "selected_model" not in st.session_state:
    st.session_state.selected_model = None

# Sidebar
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

    st.divider()
    temperature = st.slider("Temperature", 0.0, 1.0, 0.1, 0.05)
    max_tokens = st.number_input("Max Tokens", 100, 4096, 2048, 100)

# Standard-Prompt (vorausgefüllt)
default_prompt = """Du bist Experte für Forschungsförderung und erstellst Einträge für einen Fördernewsletter (D7-Format).
Analysiere den folgenden Text einer Förderausschreibung und erstelle eine kurze, strukturierte Zusammenfassung mit diesen Feldern:

**Förderung:** (1-2 Sätze: Was wird gefördert?)
**Zielgruppe:** (Wer ist antragsberechtigt?)
**Dauer:** (Projektlaufzeit, falls nicht genannt "Keine Angabe")
**Förderhöhe:** (Maximale Fördersumme oder Prozentangabe, sonst "Keine Angabe")
**Fristende:** (Einreichungsfrist, sonst "Keine Angabe")
**Website:** (URL oder Kontakt, sonst "Keine Angabe")

Text der Ausschreibung:
{text}

Antworte NUR mit den formatierten Feldern. Keine zusätzlichen Erklärungen."""

col1, col2 = st.columns([1, 1])
with col1:
    st.subheader("📝 Prompt (Platzhalter `{text}` wird ersetzt)")
    prompt_template = st.text_area("Prompt", value=default_prompt, height=300)
with col2:
    st.subheader("📄 Ausschreibungstext")
    user_text = st.text_area("Text einfügen", height=300, placeholder="Volltext der Ausschreibung hier einfügen...")

if st.button("🚀 Prompt senden", type="primary"):
    if not user_text.strip():
        st.warning("Bitte Ausschreibungstext eingeben.")
    else:
        with st.spinner("Anfrage an KI:connect ..."):
            try:
                client = LLMClient(api_key=api_key_input if api_key_input else None)
                if st.session_state.selected_model:
                    client.model = st.session_state.selected_model
                # Platzhalter ersetzen
                final_prompt = prompt_template.replace("{text}", user_text)
                response = client.generate(final_prompt, temperature=temperature, max_tokens=max_tokens)
                st.session_state.response = response
            except KIConnectError as e:
                st.error(f"API-Fehler: {e}")
            except Exception as e:
                st.exception(e)

if st.session_state.response:
    st.divider()
    st.subheader("📋 Antwort")
    st.markdown(st.session_state.response)

    # Export-Buttons
    col_down1, col_down2 = st.columns(2)
    with col_down1:
        st.download_button(
            label="📥 Als Markdown (.md)",
            data=st.session_state.response,
            file_name="ki_antwort.md",
            mime="text/markdown"
        )
    with col_down2:
        st.download_button(
            label="📄 Als Text (.txt)",
            data=st.session_state.response,
            file_name="ki_antwort.txt",
            mime="text/plain"
        )
