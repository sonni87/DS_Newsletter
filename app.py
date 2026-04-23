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

/* Roter Haupt-Button (Uni Köln Rot #BE0A26) */
div[data-testid="stButton"]:has(button[kind="primary"]) > button {
    background-color: #BE0A26 !important;
    color: white !important;
    font-weight: bold !important;
}

div[data-testid="stButton"]:has(button[kind="primary"]) > button:hover {
    background-color: #99071E !important;
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
# text_area_key wird hochgezählt, um das Widget neu zu erzeugen (= leeren)
if "text_area_key" not in st.session_state:
    st.session_state.text_area_key = 0

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
    st.subheader("🖥️ Systemauslastung")
    try:
        import psutil
        ram = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=0.5)
        ram_used = ram.used / (1024 ** 3)
        ram_total = ram.total / (1024 ** 3)
        ram_pct = ram.percent
        st.progress(int(cpu), text=f"CPU: {cpu:.0f}%")
        st.progress(int(ram_pct), text=f"RAM: {ram_used:.1f} / {ram_total:.1f} GB ({ram_pct:.0f}%)")
    except ImportError:
        # Fallback: /proc direkt lesen (funktioniert auf jedem Linux ohne Pakete)
        try:
            # RAM aus /proc/meminfo
            mem = {}
            with open("/proc/meminfo") as f:
                for line in f:
                    parts = line.split()
                    mem[parts[0].rstrip(":")] = int(parts[1])
            ram_total_gb = mem["MemTotal"] / (1024 ** 2)
            ram_avail_gb = mem["MemAvailable"] / (1024 ** 2)
            ram_used_gb = ram_total_gb - ram_avail_gb
            ram_pct = int(ram_used_gb / ram_total_gb * 100)

            # CPU aus /proc/stat (zwei Messungen mit 0.5s Pause)
            import time
            def _cpu_times():
                with open("/proc/stat") as f:
                    vals = f.readline().split()[1:]
                return [int(v) for v in vals]
            t1 = _cpu_times()
            time.sleep(0.5)
            t2 = _cpu_times()
            idle1, idle2 = t1[3], t2[3]
            total1, total2 = sum(t1), sum(t2)
            cpu_pct = int(100 * (1 - (idle2 - idle1) / (total2 - total1)))

            st.progress(cpu_pct, text=f"CPU: {cpu_pct}%")
            st.progress(ram_pct, text=f"RAM: {ram_used_gb:.1f} / {ram_total_gb:.1f} GB ({ram_pct}%)")
        except Exception as e:
            st.caption(f"Systeminfo nicht verfügbar: {e}")

    if st.button("🔄 Aktualisieren"):
        st.rerun()

    st.markdown("---")
    st.caption("Beta-Newsletter – Prompt Client v1.1")

# ========== DEFAULT PROMPT (an echten Newslettereinträgen orientiert) ==========
default_prompt = """Du bist Redakteur des Fördernewsletters der Universität zu Köln (Division 7 Research
Management). Du fasst Förderausschreibungen so zusammen, wie sie im Newsletter erscheinen:
kompakt, sachlich, ohne Einleitungssätze oder Marketingsprache, direkt auf die
strukturierten Felder beschränkt.

Analysiere die folgende Förderausschreibung und gib NUR die strukturierten Felder aus –
keine Einleitung, kein Kommentar, keine abschließenden Bemerkungen.

REGELN:

1. SPRACHE: Formuliere auf Englisch. Ausnahme: Die Ausschreibung ist ausschließlich auf
   Deutsch verfügbar und kann nur auf Deutsch beantragt werden – dann auf Deutsch mit
   deutschen Feldbezeichnungen (Förderung / Zielgruppe / Dauer / Förderhöhe / Fristende
   / Website).

2. FÖRDERHÖHE – KRITISCH:
   Nenne IMMER die Fördersumme PRO PROJEKT oder PRO ANTRAG, nie das Gesamtbudget der
   Förderlinie. Zeige immer den Bezugspunkt:
   - "for each German partner" / "for all German partners" / "per project"
   - Förderlinien/Phasen separat: z.B. "up to € 600,000 (funding line A) | up to
     € 1.2 million (funding line B)" oder "exploratory phase: € 100,000 | feasibility
     phase: € 500,000 (+overhead)"
   - Hochschulen: Förderquote ergänzen wenn relevant, z.B.
     "up to 100% of eligible project-related expenses + 20% project lump sum for universities"
   - Ist nur das Gesamtprogrammbudget genannt und keine Einzelprojektförderung:
     schreibe "not specified per project"

3. ZIELGRUPPE: Präzise – Antragstyp (Einzel-/Verbundprojekt, internationale Kooperation)
   UND Antragsteller (Institutionen, Karrierestufen, Mindestpartnerzahl, Länder).
   Orientiere dich an Newsletter-Einträgen wie: "transnational pre-competitive R&D
   projects with at least three partners from three participating countries" – nicht
   nur allgemein "Forschende".

4. FRISTENDE: Datum + Verfahrensart in Klammern.
   Beispiel: "5 December 2025 (submission of a project outline, two-stage procedure)"
   Bei dauerhaft offenen Calls: "continuously open"

5. FEHLENDE INFORMATIONEN: "not specified" (EN) / "Keine Angabe" (DE)

6. EIGENANTEIL: Nur wenn explizit gefordert als eigenes Feld ergänzen, sonst weglassen.

<ausschreibung>
{text}
</ausschreibung>

Ausgabe NUR in diesem Format (keine zusätzlichen Felder, keine Umsortierung):

**Title:** (Name der Ausschreibung)

**Aim:** (3–5 sachliche Sätze: Was wird gefördert? Ziel? Thematische Schwerpunkte oder
Förderbereiche? Direkt zur Sache – kein "The programme aims to" als Einstieg.)

**Target group:** (Antragstyp + antragsberechtigt Institutionen/Personen + relevante
Einschränkungen, kompakt in einem Satz oder präzisen Stichwörtern)

**Duration:** (Projektlaufzeit; bei Phasen alle nennen)

**Funding:** (Fördersumme PRO PROJEKT mit Bezugspunkt; Phasen/Varianten alle auflisten)

**Deadline:** (Datum + Verfahrensart in Klammern)

**Further information:** (URL oder "website of [Fördergeber]")"""

# ========== ZWEI SPALTEN: PROMPT | AUSSCHREIBUNGSTEXT ==========
col1, col2 = st.columns(2)

with col1:
    st.subheader("📝 Prompt")
    prompt_template = st.text_area(
        "Prompt bearbeiten (Platzhalter `{text}`)",
        value=default_prompt,
        height=400
    )

with col2:
    # Header-Zeile mit Titel links und "Textfeld leeren"-Button rechts
    col2_header, col2_btn = st.columns([3, 1])
    with col2_header:
        st.subheader("📄 Ausschreibungstext")
    with col2_btn:
        st.write("")  # vertikales Alignment
        if st.button("🧹 Textfeld leeren"):
            st.session_state.text_area_key += 1
            st.session_state.user_text = ""
            st.session_state.url_input = ""
            st.rerun()

    user_text = st.text_area(
        "Volltext der Ausschreibung einfügen",
        value="",
        height=350,
        placeholder="Den kompletten Ausschreibungstext hier einfügen...",
        key=f"user_text_input_{st.session_state.text_area_key}"
    )
    st.session_state.user_text = user_text

    url_input = st.text_input(
        "🔗 Website / URL des Ausschreibungstextes",
        value=st.session_state.get("url_input", ""),
        placeholder="https://...",
        key=f"url_input_{st.session_state.text_area_key}"
    )
    st.session_state.url_input = url_input

# --- Großer roter Button zentriert ---
col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
with col_btn2:
    summarize_clicked = st.button(
        "🚀 Ausschreibung zusammenfassen",
        use_container_width=True,
        type="primary"  # Damit der rote CSS-Selector greift
    )

if summarize_clicked:
    if not st.session_state.user_text.strip():
        st.warning("Bitte Ausschreibungstext eingeben.")
    else:
        with st.spinner("Anfrage an KI:connect ..."):
            try:
                client = LLMClient(api_key=api_key_input if api_key_input else None)
                if st.session_state.selected_model:
                    client.model = st.session_state.selected_model
                final_prompt = prompt_template.replace("{text}", st.session_state.user_text)
                # URL in den Prompt injizieren, damit sie in "Further information" landet
                url = st.session_state.get("url_input", "").strip()
                if url:
                    final_prompt += f"\n\nDie URL der Ausschreibung lautet: {url}\nTrage diese URL exakt so unter 'Further information' ein."
                response = client.generate(final_prompt, temperature=0.1, max_tokens=2048)
                st.session_state.response = response
                st.session_state.translated_response = ""
                # Kein automatisches Leeren – nur über "Textfeld leeren"-Button
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
