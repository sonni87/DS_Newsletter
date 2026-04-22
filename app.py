"""
Streamlit App – Prompt-Client für KI:connect mit Übersetzungsoption.
Layout angepasst an das Corporate Design der Universität zu Köln.
"""

import streamlit as st
from llm_client import LLMClient, KIConnectError

# --- Seiteneinstellungen & Uni-Köln-Farben ---
st.set_page_config(
    page_title="KI:connect Prompt",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS für Uni-Köln-Design
st.markdown("""
<style>
    /* Hauptüberschrift in Uni-Blau */
    h1 {
        color: #005176 !important;
    }
    
    /* Sidebar-Hintergrund */
    section[data-testid="stSidebar"] {
        background-color: #F0F4F7;
    }
    
    /* Standard-Buttons in Uni-Türkis */
    .stButton > button {
        background-color: #009DCC;
        color: white;
        border: none;
    }
    .stButton > button:hover {
        background-color: #007BA1;
        color: white;
    }
    
    /* Roter Haupt-Button */
    div[data-testid="stButton"]:has(button:contains("Ausschreibung zusammenfassen")) > button {
        background-color: #EF7872 !important;
        color: white !important;
        font-weight: bold !important;
    }
    div[data-testid="stButton"]:has(button:contains("Ausschreibung zusammenfassen")) > button:hover {
        background-color: #D9655F !important;
    }
    
    /* Download-Buttons in Uni-Korall */
    .stDownloadButton > button {
        background-color: #EF7872;
        color: white;
        border: none;
    }
    .stDownloadButton > button:hover {
        background-color: #D9655F;
        color: white;
    }
    
    /* Links */
    a {
        color: #009DCC !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("🤖 KI:connect – Prompt Client zur Zusammenfassung von Ausschreibungstexten")
st.markdown("Gib deinen Prompt und den Ausschreibungstext ein. Die Antwort wird im Markdown‑Format ausgegeben und kann exportiert werden.")

# Session State
if "response" not in st.session_state:
    st.session_state.response = ""
if "translated_response" not in st.session_state:
    st.session_state.translated_response = ""
if "available_models" not in st.session_state:
    st.session_state.available_models = []
if "selected_model" not in st.session_state:
    st.session_state.selected_model = None
if "user_text" not in st.session_state:
    st.session_state.user_text = ""

# Sidebar
with st.sidebar:
    st.header("⚙️ Konfiguration")
    api_key_input = st.text_input(
        "KIConnect API-Key",
        type="password",
        placeholder="Aus Umgebungsvariable/Secrets",
        help="Wird automatisch aus Streamlit Secrets oder KICONNECT_API_KEY geladen."
    )

    if st.button("🔌 Verbinde mich mit KI:connect"):
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
    st.markdown("---")
    st.caption("Beta-Newsletter – Prompt Client v1.0")

# ========== PROMPT (mit Titel-Feld) ==========
default_prompt = """Du bist Redakteur eines Fördernewsletters für Forschende und Verwaltungsmitarbeiter 
an deutschen Hochschulen und Forschungseinrichtungen. Deine Aufgabe ist es, 
Förderausschreibungen präzise und verständlich zusammenzufassen, damit die Leser 
schnell einschätzen können, ob eine Ausschreibung für sie relevant ist.

Analysiere die folgende Förderausschreibung und erstelle eine strukturierte 
Zusammenfassung. Halte dich exakt an die vorgegebenen Felder und gib ausschließlich 
die strukturierten Felder aus – ohne Einleitung, Kommentar oder abschließende 
Bemerkungen.

Regeln:
- Ist eine Information nicht im Text enthalten, schreibe "Keine Angabe".
- Bei Spannen oder Varianten (z.B. unterschiedliche Förderhöhen je nach Projekttyp) 
  nenne den maximalen Wert und ergänze den Kontext in Klammern.
- Formuliere sachlich und präzise, vermeide Marketingsprache aus der Ausschreibung.
- Verwende deutsche Fachbegriffe, die im Hochschul- und Forschungskontext üblich sind.

<ausschreibung>
{text}
</ausschreibung>

Erstelle die Zusammenfassung in folgendem Format:

**Titel:** (Titel oder Name der Ausschreibung)

**Förderung:** (4–6 Sätze: Was wird gefördert? Was ist das Ziel des Programms? 
Welche Kosten sind förderfähig?)

**Zielgruppe:** (Wer ist antragsberechtigt? Welche Einrichtungen oder Personen 
können einen Antrag stellen?)

**Dauer:** (Projektlaufzeit)

**Förderhöhe:** (Maximale Fördersumme oder Förderquote)

**Eigenanteil:** (Wird von antragstellenden Einrichtungen ein Eigenanteil gefordert? 
Wenn ja: Höhe oder Form des Eigenanteils)

**Fristende:** (Einreichungsfrist)

**Website:** (URL der Ausschreibung)"""

# Zwei Spalten für Prompt und Ausschreibungstext
col1, col2 = st.columns(2)
with col1:
    st.subheader("📝 Prompt")
    prompt_template = st.text_area(
        "Prompt bearbeiten (Platzhalter `{text}`)",
        value=default_prompt,
        height=400
    )
with col2:
    st.subheader("📄 Ausschreibungstext")
    user_text = st.text_area(
        "Volltext der Ausschreibung einfügen",
        value=st.session_state.user_text,
        height=400,
        placeholder="Den kompletten Ausschreibungstext hier einfügen...",
        key="user_text_input"
    )
    # Synchronisiere Session State
    st.session_state.user_text = user_text

# --- Button-Zeile: Textfeld leeren (rechts) ---
col_empty1, col_empty2 = st.columns([5, 1])
with col_empty2:
    if st.button("🧹 Textfeld leeren"):
        st.session_state.user_text = ""
        st.rerun()

# --- Großer roter Button zentriert ---
col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
with col_btn2:
    if st.button("🚀 Ausschreibung zusammenfassen", use_container_width=True):
        if not st.session_state.user_text.strip():
            st.warning("Bitte Ausschreibungstext eingeben.")
        else:
            with st.spinner("Anfrage an KI:connect ..."):
                try:
                    client = LLMClient(api_key=api_key_input if api_key_input else None)
                    if st.session_state.selected_model:
                        client.model = st.session_state.selected_model
                    final_prompt = prompt_template.replace("{text}", st.session_state.user_text)
                    response = client.generate(final_prompt, temperature=0.1, max_tokens=2048)
                    st.session_state.response = response
                    st.session_state.translated_response = ""
                except KIConnectError as e:
                    st.error(f"API-Fehler: {e}")
                except Exception as e:
                    st.exception(e)

# Ergebnis anzeigen
if st.session_state.response:
    st.divider()
    st.subheader("📋 Antwort (Deutsch)")
    st.markdown(st.session_state.response)

    col_down1, col_down2 = st.columns(2)
    with col_down1:
        st.download_button(
            label="📥 Als Markdown (.md)",
            data=st.session_state.response,
            file_name="antwort_de.md",
            mime="text/markdown"
        )
    with col_down2:
        st.download_button(
            label="📄 Als Text (.txt)",
            data=st.session_state.response,
            file_name="antwort_de.txt",
            mime="text/plain"
        )

# --- Übersetzungsbereich ---
st.divider()
st.subheader("🌐 Übersetzung (Deutsch → Englisch)")
st.markdown("Füge hier einen deutschen Text ein, um ihn ins Englische übersetzen zu lassen.")

col_trans1, col_trans2 = st.columns([3, 1])
with col_trans1:
    text_to_translate = st.text_area(
        "Zu übersetzender Text",
        height=150,
        placeholder="Deutschen Text hier einfügen...",
        key="translate_input"
    )
with col_trans2:
    st.write("")
    st.write("")
    translate_btn = st.button("🔄 Übersetzen")

if translate_btn and text_to_translate.strip():
    with st.spinner("Übersetze ..."):
        try:
            client = LLMClient(api_key=api_key_input if api_key_input else None)
            if st.session_state.selected_model:
                client.model = st.session_state.selected_model
            translation_prompt = f"""Übersetze den folgenden deutschen Text präzise und professionell ins Englische.
WICHTIG: Behalte die **exakte Formatierung** bei, insbesondere **Fettdruck** (z.B. `**Förderung:**` → `**Funding:**`).
Die Feldbezeichnungen MÜSSEN fett sein.
Antworte NUR mit der Übersetzung, ohne zusätzliche Erklärungen.

Deutscher Text:
{text_to_translate}

Englische Übersetzung:"""
            translated = client.generate(translation_prompt, temperature=0.1, max_tokens=2048)
            st.session_state.translated_response = translated
        except Exception as e:
            st.error(f"Übersetzungsfehler: {e}")

if st.session_state.translated_response:
    st.subheader("📋 Übersetzung (Englisch)")
    st.markdown(st.session_state.translated_response)

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.download_button(
            label="📥 Übersetzung als Markdown (.md)",
            data=st.session_state.translated_response,
            file_name="antwort_en.md",
            mime="text/markdown"
        )
    with col_t2:
        st.download_button(
            label="📄 Übersetzung als Text (.txt)",
            data=st.session_state.translated_response,
            file_name="antwort_en.txt",
            mime="text/plain"
        )
