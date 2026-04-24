"""
Kombinierte App – Förder-Screener + Newsletter Summarizer
Universität zu Köln · Dezernat 7 Forschungsmanagement
"""

import re
import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
from io import BytesIO
import pdfplumber
from llm_client import LLMClient, KIConnectError

# =============================================================================
# Seiteneinstellungen
# =============================================================================
st.set_page_config(
    page_title="Förder-Tools · Universität zu Köln",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# Uni-Köln Corporate Design
# =============================================================================
UZK_BLAU      = "#005176"
UZK_TUERKIS   = "#009dcc"
UZK_KORALL    = "#ea564f"
UZK_ROT       = "#BE0A26"
UZK_HELLGRAU  = "#f4f6f8"
UZK_DUNKELGRAU = "#1a1a1a"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Albert+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&display=swap');

/* Global font override – nur Text-Elemente, NICHT Icon-Ligaturen */
:root {{
    --font-sans-serif: 'Albert Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}}
html, body,
[class*="css"],
.stApp,
.stMarkdown p, .stMarkdown li,
.stTextArea textarea,
.stTextInput input, .stTextInput label,
.stSelectbox label,
.stMultiSelect label,
.stButton button,
.stDownloadButton button,
.stTabs [data-baseweb="tab"],
.stCaption p,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] button,
section[data-testid="stSidebar"] input,
[data-testid="stMetricLabel"] p,
[data-testid="stMetricValue"] div,
[data-testid="stExpander"] summary p,
h1, h2, h3, h4, h5, h6,
p, label, input, textarea, button, td, th {{
    font-family: 'Albert Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}}

/* Überschriften */
h1 {{
    color: {UZK_BLAU} !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em;
}}
h2, h3 {{
    color: {UZK_BLAU} !important;
    font-weight: 600 !important;
}}

/* Sidebar */
section[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, {UZK_HELLGRAU} 0%, #eaeff3 100%);
    border-right: 1px solid #dce3ea;
}}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {{
    color: {UZK_BLAU} !important;
}}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {{
    gap: 0;
    border-bottom: 2px solid #e0e5eb;
}}
.stTabs [data-baseweb="tab"] {{
    padding: 0.7rem 1.5rem;
    font-weight: 500;
    font-size: 0.95rem;
    color: #6b7b8d;
    border-bottom: 3px solid transparent;
    background: transparent;
}}
.stTabs [data-baseweb="tab"]:hover {{
    color: {UZK_BLAU};
    background: {UZK_HELLGRAU};
}}
.stTabs [aria-selected="true"] {{
    color: {UZK_BLAU} !important;
    font-weight: 700 !important;
    border-bottom: 3px solid {UZK_TUERKIS} !important;
    background: transparent !important;
}}

/* Standard-Buttons Türkis */
.stButton > button {{
    background-color: {UZK_TUERKIS};
    color: white;
    border: none;
    font-weight: 500;
    border-radius: 6px;
    transition: background-color 0.2s ease;
}}
.stButton > button:hover {{
    background-color: {UZK_BLAU} !important;
    color: white;
}}

/* Primär-Button Rot */
div[data-testid="stButton"]:has(button[kind="primary"]) > button {{
    background-color: {UZK_ROT} !important;
    color: white !important;
    font-weight: 600 !important;
    border-radius: 6px;
}}
div[data-testid="stButton"]:has(button[kind="primary"]) > button:hover {{
    background-color: #99071E !important;
}}

/* Download-Buttons */
.stDownloadButton > button {{
    background-color: white !important;
    color: {UZK_BLAU} !important;
    border: 1.5px solid {UZK_BLAU} !important;
    font-weight: 500;
    border-radius: 6px;
}}
.stDownloadButton > button:hover {{
    background-color: {UZK_BLAU} !important;
    color: white !important;
}}

/* Metric-Karten */
[data-testid="stMetric"] {{
    background: {UZK_HELLGRAU};
    padding: 1rem 1.2rem;
    border-radius: 6px;
    border-left: 4px solid {UZK_BLAU};
}}
[data-testid="stMetricValue"] {{
    color: {UZK_BLAU} !important;
    font-weight: 700 !important;
}}

/* Text-Eingabefelder */
.stTextArea textarea, .stTextInput input {{
    border: 1.5px solid #d0d8e0 !important;
    border-radius: 6px !important;
    font-size: 0.9rem !important;
}}
.stTextArea textarea:focus, .stTextInput input:focus {{
    border-color: {UZK_TUERKIS} !important;
    box-shadow: 0 0 0 2px rgba(0,157,204,0.15) !important;
}}
.stTextArea textarea::placeholder, .stTextInput input::placeholder {{
    font-family: 'Albert Sans', sans-serif !important;
}}

/* Links */
a {{ color: {UZK_TUERKIS} !important; }}
a:hover {{ color: {UZK_BLAU} !important; }}

/* Info-Leiste */
.uzk-info-bar {{
    border-left: 5px solid;
    padding: 0.5rem 0 0.5rem 1rem;
    margin-bottom: 1.2rem;
    border-radius: 0 6px 6px 0;
    background: {UZK_HELLGRAU};
    font-size: 0.92rem;
    color: {UZK_DUNKELGRAU};
}}

/* Footer */
.uzk-footer-line {{
    color: #8899aa;
    font-size: 0.78rem;
    margin-top: 2.5rem;
    padding-top: 1rem;
    border-top: 1px solid #e0e5eb;
    text-align: center;
}}

/* Expander */
.streamlit-expanderHeader {{
    font-weight: 500 !important;
    color: {UZK_BLAU} !important;
}}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# Session State
# =============================================================================
defaults = {
    "response": "",
    "translated_response": "",
    "available_models": [],
    "selected_model": None,
    "user_text": "",
    "text_area_key": 0,
    "tokens_session_prompt": 0,
    "tokens_session_completion": 0,
    "tokens_session_total": 0,
    "last_usage": None,
    "request_count": 0,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# =============================================================================
# Hilfsfunktionen Token
# =============================================================================
MODEL_CONTEXT_WINDOWS = {
    "mistral-small-4-119b-2603":           128_000,
    "mistral-small-4-119b":                128_000,
    "mistral-small-3.2-24b-instruct-2506": 128_000,
    "mistral-small-3-2-24b":               128_000,
    "gpt-oss-120b":                        128_000,
    "e5-mistral-7b-instruct":               32_000,
}
DEFAULT_CONTEXT = 128_000

def get_context_window(model_name: str) -> int:
    if not model_name:
        return DEFAULT_CONTEXT
    for key, val in MODEL_CONTEXT_WINDOWS.items():
        if key in model_name.lower() or model_name.lower() in key:
            return val
    return DEFAULT_CONTEXT

def update_token_stats(usage: dict):
    st.session_state.tokens_session_prompt     += usage.get("prompt_tokens", 0)
    st.session_state.tokens_session_completion += usage.get("completion_tokens", 0)
    st.session_state.tokens_session_total      += usage.get("total_tokens", 0)
    st.session_state.last_usage = usage
    st.session_state.request_count += 1

def fmt(n: int) -> str:
    return f"{n:,}".replace(",", ".")

# =============================================================================
# Förder-Screener Logik
# =============================================================================
UML_A = r"(ä|ae)"
UML_O = r"(ö|oe)"
UML_U = r"(ü|ue)"

SUBJ = (
    r"(Hochschule|Einrichtung|Institution|Universit" + UML_A + r"t|"
    r"antragstellende[rn]?\s+(Einrichtung|Hochschule|Institution)|"
    r"Antragsteller(in)?|Ausschreibung|Ausschreibungsrunde|"
    r"F" + UML_O + r"rderrunde|F" + UML_O + r"rderperiode|Runde|"
    r"Stichtag|Fakult" + UML_A + r"t|Standort)"
)
ADJ = r"(?:[\wäöüÄÖÜß\-]+\s+){0,3}?"
OBJ = (
    r"(Antrag|Antr" + UML_A + r"ge|Skizze|Skizzen|Projektskizze|Projektskizzen|"
    r"Projektbeteiligung|Vorhaben|Projekt|Projekte|Vorhabenbeschreibung|"
    r"Zuwendung|Absichtserkl" + UML_A + r"rung|Absichtserkl" + UML_A + r"rungen|"
    r"Verbundkoordination|Koordination)"
)
NUM = r"(ein|eine|einen|einem|einer|1|zwei|2|drei|3)"
QTY = (
    r"(" + NUM + r"|maximal|max\.|h" + UML_O + r"chstens|nur|"
    r"nicht mehr als|lediglich)"
)
MONEY_BLOCKLIST = (
    r"(Million|Mio\.?|Mrd\.?|Milliard|Euro|EUR|€|Tausend|T€|TEUR|"
    r"Prozent|%|Stunden|Monate|Jahre)"
)
ABBREV = r"(?:bzw|ggf|vgl|etc|usw|ca|Nr|Abs|d\.\s*h|z\.\s*B|u\.\s*a|bspw|max|min|Mio|Mrd)"
SAFE_CHAR = r"(?:[^.]|" + ABBREV + r"\.)"

PATTERNS = [
    (r"\b(pro|je)\s+" + ADJ + r"\b" + SUBJ + r"\b"
     r".{0,80}?\b" + QTY + r"\b.{0,40}?\b" + OBJ + r"\b",
     "pro/je Einrichtung"),
    (r"\b(nur|maximal|max\.|h" + UML_O + r"chstens|nicht mehr als|lediglich)\b"
     r".{0,60}?\b" + NUM + r"\b"
     r"(?!\s+" + MONEY_BLOCKLIST + r")"
     r".{0,20}?\b" + OBJ + r"\b",
     "Mengenbegrenzung"),
    (r"\b(Eine|Jede[rs]?|Je|Pro)\s+" + ADJ + r"\b" + SUBJ + r"\b"
     r".{0,60}?\b(darf|kann|soll|wird|k" + UML_O + r"nnen|d" + UML_U + r"rfen)\b"
     r".{0,80}?\b(nicht mehr als|maximal|max\.|nur|h" + UML_O + r"chstens)\b"
     r".{0,40}?\b" + NUM + r"\b.{0,40}?\b" + OBJ,
     "Einrichtung darf nur"),
    (r"\b(Eine|Pro|Je|Jede[rs]?)\s+" + ADJ + r"\b" + SUBJ + r"\b"
     r".{0,120}?\b(kann|darf|soll|k" + UML_O + r"nnen|d" + UML_U + r"rfen)\b"
     r".{0,80}?\b(ein|eine|einen|einem|einer|1)\s+" + OBJ + r"\b"
     + SAFE_CHAR + r"{0,200}?\b(stellen|einreichen|ein.?reichen|beantragen|"
     r"vorlegen|abgeben|" + UML_U + r"bernehmen)\b",
     "X kann einen stellen"),
    (r"\b(Mehrfachantrag|Mehrfachantragstellung|Mehrfacheinreichung|"
     r"mehrere\s+Antr" + UML_A + r"ge|mehrere\s+Skizzen|"
     r"mehr als eine\s+(Skizze|Antrag))\b"
     r".{0,80}?\b(nicht|aus(-?\s*)?geschlossen|unzul" + UML_A + r"ssig|"
     r"nicht zul" + UML_A + r"ssig|nicht m" + UML_O + r"glich|"
     r"nicht gestattet|ausgeschlossen)\b",
     "Mehrfachantragstellung"),
    (r"\b(beschr" + UML_A + r"nkt|begrenzt|Begrenzung|Beschr" + UML_A + r"nkung)\b"
     r".{0,40}?\bauf\s+" + NUM + r"\b.{0,40}?\b" + OBJ + r"\b",
     "Begrenzung auf Anzahl"),
    (r"\b(hochschulintern|institutionsintern|universit" + UML_A + r"tsintern)"
     r"(e|er|es|en)?\b"
     r".{0,40}?\b(Vorauswahl|Auswahlverfahren|Priorisierung|Abstimmung)\b",
     "Interne Vorauswahl"),
    (r"\b(Einrichtungen|Hochschulen|Universit" + UML_A + r"ten)\b"
     r".{0,40}?\b(k" + UML_O + r"nnen|d" + UML_U + r"rfen)\b"
     r".{0,60}?\b(nicht mehr als|maximal|max\.|nur|h" + UML_O + r"chstens)\b"
     r".{0,40}?\b" + NUM + r"\b.{0,40}?\b" + OBJ,
     "Plural Einrichtungen"),
    (r"\b(only one|maximum of one|at most one|one)\b\s+"
     r"(proposal|application|submission)\b"
     r".{0,40}?\b(per|by each)\s+"
     r"(institution|university|applicant|organisation|organization)\b",
     "EN: one per institution"),
    (r"\b(multiple|more than one)\b\s+(proposals|applications|submissions)\b"
     r".{0,40}?\b(not allowed|not permitted|excluded|prohibited)\b",
     "EN: multiple not allowed"),
]

def _clean_title(title, max_len=130):
    if not title:
        return ""
    t = re.sub(r"\s+", " ", title).strip()
    t = t.replace("„", '"').replace("\u201c", '"').replace("\u201d", '"')
    if len(t) > max_len:
        t = t[:max_len].rsplit(" ", 1)[0] + "…"
    return t

def _is_bad_title(t):
    if not t or len(t.strip()) < 5:
        return True
    t = t.strip()
    if t.startswith(("http://", "https://", "www.")):
        return True
    if t.lower() in {"pdf ohne titel", "index", "startseite", "home", "dokument"}:
        return True
    if re.match(r"^\d{1,2}\.\d{1,2}\.\d{2,4}$", t):
        return True
    return False

def extract_html_title(soup, url):
    h1 = soup.find("h1")
    if h1:
        h1_text = h1.get_text(" ", strip=True)
        if not _is_bad_title(h1_text):
            if h1_text.lower().strip() in ("bekanntmachung", "förderaufruf", "richtlinie", "merkblatt"):
                nxt = h1.find_next(["h2", "p", "strong", "div"])
                if nxt:
                    nxt_text = nxt.get_text(" ", strip=True)
                    if nxt_text and 10 < len(nxt_text) < 250:
                        return _clean_title(f"{h1_text}: {nxt_text}")
            return _clean_title(h1_text)
    og = soup.find("meta", property="og:title")
    if og and og.get("content") and not _is_bad_title(og["content"]):
        return _clean_title(og["content"])
    if soup.title and soup.title.string:
        t = soup.title.string.strip()
        if not _is_bad_title(t):
            return _clean_title(t)
    h2 = soup.find("h2")
    if h2:
        h2_text = h2.get_text(" ", strip=True)
        if not _is_bad_title(h2_text):
            return _clean_title(h2_text)
    m = re.match(r"https?://(?:www\.|www\d+\.)?([^/]+)", url)
    domain = m.group(1) if m else url
    return f"[Seite auf {domain}]"

def extract_pdf_title(text, max_search_chars=2500):
    head = text[:max_search_chars]
    lines = [ln.strip() for ln in re.split(r"[\n\r]+", head) if ln.strip()]
    for i, line in enumerate(lines[:40]):
        if re.match(
            r"^(bekanntmachung|f" + UML_O + r"rderaufruf|f" + UML_O + r"rderrichtlinie|merkblatt)\s*$",
            line, re.IGNORECASE
        ):
            following = []
            for j in range(i + 1, min(i + 5, len(lines))):
                nxt = lines[j]
                if re.match(r"^(vom\s+\d|\d+\.\s+[A-ZÄÖÜ]|\d{1,2}\.\d{1,2}\.\d{2,4}$)", nxt, re.IGNORECASE):
                    break
                if len(nxt) > 3 and not nxt.startswith("www"):
                    following.append(nxt)
                if len(following) >= 2 and len(" ".join(following)) > 40:
                    break
            if following:
                return _clean_title(f"{line}: {' '.join(following)}")
    for line in lines[:40]:
        if re.search(
            r"(Richtlinie zur F" + UML_O + r"rderung|F" + UML_O + r"rderrichtlinie|"
            r"F" + UML_O + r"rderaufruf|Programminformation|"
            r"Bekanntmachung\s+(der|des|der Richtlinie|zur|über))",
            line, re.IGNORECASE
        ):
            if len(line) > 25:
                return _clean_title(line)
    BOILERPLATE = re.compile(
        r"^(Bundesministerium|Ministerium für|Landesministerium|Seite \d|"
        r"www\.|Tel\.|\d{5}\s|Stand:|Version\s|Anlage)",
        re.IGNORECASE
    )
    for line in lines[:40]:
        if BOILERPLATE.match(line):
            continue
        if len(line) < 20 or len(line) > 250:
            continue
        if re.match(r"^\d{1,2}\.\d{1,2}\.\d{2,4}$", line):
            continue
        return _clean_title(line)
    return _clean_title(" ".join(lines[:3]) if lines else "PDF ohne erkennbaren Titel")

def transform_url(url: str) -> str:
    if "bmftr.bund.de/SharedDocs/Bekanntmachungen" in url:
        return url.split("?")[0] + "?view=renderNewsletterHtml"
    return url

def is_pdf_content(response) -> bool:
    ct = response.headers.get("content-type", "").lower()
    if "pdf" in ct:
        return True
    return response.content[:4] == b"%PDF"

def clean_pdf_text(text: str) -> str:
    cid_count = len(re.findall(r"\(cid:\d+\)", text))
    total_len = max(len(text), 1)
    if cid_count > 20 and (cid_count * 8) / total_len > 0.05:
        text = (
            "[⚠️ HINWEIS: Dieses PDF verwendet CID-kodierte Fonts. "
            "Textextraktion nur eingeschränkt möglich – bitte manuell prüfen.] " + text
        )
    text = re.sub(r"-\s*\n\s*", "", text)
    text = re.sub(r"\s+", " ", text)
    return text

def get_content(url: str, retries: int = 2):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/pdf,*/*;q=0.8",
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
    }
    url_fetch = transform_url(url)
    last_err = None
    for _ in range(retries + 1):
        try:
            r = requests.get(url_fetch, timeout=30, headers=headers, allow_redirects=True)
            r.raise_for_status()
            if is_pdf_content(r):
                with pdfplumber.open(BytesIO(r.content)) as pdf:
                    text = "\n".join((p.extract_text() or "") for p in pdf.pages)
                raw_text_for_title = text
                text = clean_pdf_text(text)
                title = extract_pdf_title(raw_text_for_title)
            else:
                soup = BeautifulSoup(r.text, "html.parser")
                title = extract_html_title(soup, url)
                for tag in soup(["nav", "footer", "header", "script", "style", "aside", "form"]):
                    tag.decompose()
                text = soup.get_text(" ")
                text = re.sub(r"\s+", " ", text)
            return text, title
        except Exception as e:
            last_err = e
            continue
    return f"ERROR: {last_err}", "Fehler beim Laden"

def extract_quotes(text: str):
    results = []
    taken_spans = []
    for pattern, label in PATTERNS:
        for m in re.finditer(pattern, text, re.IGNORECASE | re.DOTALL):
            span = (m.start(), m.end())
            if any(not (span[1] <= s[0] or span[0] >= s[1]) for s in taken_spans):
                continue
            taken_spans.append(span)
            snippet_start = max(0, m.start() - 120)
            snippet_end = min(len(text), m.end() + 120)
            snippet = text[snippet_start:snippet_end].strip()
            highlighted = re.sub(
                re.escape(m.group(0)),
                f">>>{m.group(0)}<<<",
                snippet, count=1, flags=re.IGNORECASE,
            )
            results.append(f"[{label}] {highlighted}")
    return "\n\n---\n\n".join(results)

# =============================================================================
# Sidebar – Konfiguration (nur für Newsletter Summarizer relevant)
# =============================================================================
with st.sidebar:
    st.header("⚙️ KI:connect Konfiguration")
    st.caption("Nur für den Newsletter Summarizer erforderlich.")
    api_key_input = st.text_input(
        "API-Key",
        type="password",
        placeholder="KI:connect API-Key eingeben",
    )

    if st.button("🔌 Verbinden"):
        try:
            client = LLMClient(api_key=api_key_input if api_key_input else None)
            if client.check_connection():
                st.success("✅ Verbunden!")
                models = client.list_models()
                st.session_state.available_models = models
                st.success(f"✅ {len(models)} Modelle geladen!")
            else:
                st.error("❌ Verbindung fehlgeschlagen.")
        except Exception as e:
            st.error(f"❌ {e}")

    if st.session_state.available_models:
        st.divider()
        st.subheader("🤖 Modell")
        models = st.session_state.available_models

        # Initialer Default: erstes Modell (= empfohlenes, da sortiert)
        if "model_select" not in st.session_state:
            st.session_state.model_select = models[0]
        elif st.session_state.model_select not in models:
            st.session_state.model_select = models[0]

        st.selectbox(
            "Modell wählen:",
            options=models,
            key="model_select",
        )
        st.session_state.selected_model = st.session_state.model_select

        # Empfehlung anzeigen
        sel = (st.session_state.selected_model or "").lower()
        if "119b" in sel:
            st.caption("⭐ Empfohlen – bestes Modell für strukturierte Analyse")
        elif "120b" in sel or "gpt-oss" in sel:
            st.caption("✅ Gute Alternative")
        elif "24b" in sel:
            st.caption("⚡ Schneller, aber weniger präzise")
        st.markdown(f"**Aktiv:** `{st.session_state.selected_model}`")

    # Token-Anzeige
    st.divider()
    st.subheader("🔢 Token-Verbrauch")
    if st.session_state.request_count == 0:
        st.caption("Noch keine Anfragen in dieser Session.")
    else:
        lu = st.session_state.last_usage
        last_total   = lu.get("total_tokens", 0) if lu else 0
        last_prompt  = lu.get("prompt_tokens", 0) if lu else 0
        last_compl   = lu.get("completion_tokens", 0) if lu else 0
        ctx_limit = get_context_window(st.session_state.selected_model or "")
        pct = min(last_total / ctx_limit, 1.0)

        st.markdown("**Letzte Anfrage – Kontextfenster**")
        st.progress(pct, text=f"{fmt(last_total)} / {fmt(ctx_limit)} Tokens")
        if pct >= 0.9:
            st.error("⚠️ Kontextfenster fast voll!")
        elif pct >= 0.7:
            st.warning("🟡 Kontextfenster zu 70 %+ ausgelastet.")

        with st.expander("Details letzte Anfrage"):
            st.caption(
                f"📨 Input:  {fmt(last_prompt)} Tokens\n\n"
                f"📩 Output: {fmt(last_compl)} Tokens\n\n"
                f"📊 Gesamt: {fmt(last_total)} Tokens"
            )

        st.divider()
        st.markdown("**Session-Gesamt**")
        st.metric("Anfragen", st.session_state.request_count)
        c1, c2 = st.columns(2)
        c1.metric("Input",  fmt(st.session_state.tokens_session_prompt))
        c2.metric("Output", fmt(st.session_state.tokens_session_completion))
        st.metric("Tokens gesamt", fmt(st.session_state.tokens_session_total))

        if st.button("🗑️ Zähler zurücksetzen"):
            for k in ["tokens_session_prompt", "tokens_session_completion",
                      "tokens_session_total", "last_usage", "request_count"]:
                st.session_state[k] = 0 if k != "last_usage" else None
            st.rerun()

    st.markdown("---")
    st.caption("Förder-Tools · Prompt Client v1.4")

# =============================================================================
# Hauptbereich – Zwei Tabs
# =============================================================================
st.title("🎓 Förder-Tools · Universität zu Köln")

tab1, tab2 = st.tabs(["📋 Förder-Screener", "📰 Newsletter Summarizer"])

# -----------------------------------------------------------------------------
# TAB 1 – FÖRDER-SCREENER
# -----------------------------------------------------------------------------
with tab1:
    st.markdown(
        f"<div class='uzk-info-bar' style='border-color:{UZK_KORALL}'>"
        "Prüft Ausschreibungstexte auf Beschränkungen bei der Anzahl von Anträgen bzw. Skizzen pro Einrichtung."
        "</div>",
        unsafe_allow_html=True,
    )

    urls = st.text_area(
        "URLs (eine pro Zeile)",
        height=200,
        placeholder="https://www.beispiel.de/foerderausschreibung-1\nhttps://www.beispiel.de/foerderausschreibung-2\n…",
    )

    start_clicked = st.button("🔍 Analyse starten", type="primary", key="screener_btn")

    if start_clicked:
        url_list = [u.strip() for u in urls.split("\n") if u.strip()]
        if not url_list:
            st.warning("Bitte mindestens eine URL eingeben.")
        else:
            progress = st.progress(0.0, text="Starte Analyse …")
            results = []
            for i, url in enumerate(url_list, 1):
                progress.progress(i / len(url_list), text=f"Prüfe {i}/{len(url_list)}: {url[:80]}")
                text, title = get_content(url)
                if text.startswith("ERROR"):
                    status = "Nicht prüfbar"
                    quote = text
                else:
                    quote = extract_quotes(text)
                    status = "JA – TREFFER" if quote else "Keine Beschränkung gefunden"
                results.append({"Nr": i, "Titel": title, "URL": url, "Status": status, "Zitat": quote})
            progress.empty()

            df = pd.DataFrame(results)
            n_total = len(df)
            n_hits  = int((df["Status"] == "JA – TREFFER").sum())
            n_none  = int((df["Status"] == "Keine Beschränkung gefunden").sum())
            n_err   = int((df["Status"] == "Nicht prüfbar").sum())

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Geprüfte URLs", n_total)
            c2.metric("Treffer", n_hits)
            c3.metric("Keine Beschränkung", n_none)
            c4.metric("Nicht prüfbar", n_err)

            st.subheader("Ergebnisübersicht")
            st.dataframe(
                df,
                width="stretch",
                height=min(650, 80 + len(df) * 90),
                column_config={
                    "Nr":     st.column_config.NumberColumn("Nr", width="small"),
                    "Titel":  st.column_config.TextColumn("Titel", width="large"),
                    "URL":    st.column_config.LinkColumn("URL", width="medium"),
                    "Status": st.column_config.TextColumn("Status", width="small"),
                    "Zitat":  st.column_config.TextColumn("Zitat", width="large"),
                },
                hide_index=True,
            )

            with st.expander("📋 Detailansicht pro URL", expanded=False):
                for _, row in df.iterrows():
                    icon = "✅" if row["Status"] == "JA – TREFFER" else ("⚠️" if row["Status"] == "Nicht prüfbar" else "➖")
                    st.markdown(f"**{icon} Nr. {row['Nr']} – {row['Status']}**")
                    st.markdown(f"🔗 [{row['URL']}]({row['URL']})")
                    if row["Titel"]:
                        st.caption(f"Titel: {row['Titel']}")
                    if row["Zitat"]:
                        st.text(row["Zitat"])
                    st.divider()

            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 CSV herunterladen", csv, "foerder_screening.csv", "text/csv")

# -----------------------------------------------------------------------------
# TAB 2 – NEWSLETTER SUMMARIZER
# -----------------------------------------------------------------------------
with tab2:
    st.markdown(
        f"<div class='uzk-info-bar' style='border-color:{UZK_TUERKIS}'>"
        "Fasst Förderausschreibungen strukturiert für den Newsletter zusammen. API-Key in der Sidebar eingeben."
        "</div>",
        unsafe_allow_html=True,
    )

    default_prompt = """Du bist Redakteur des Fördernewsletters der Universität zu Köln (Division 7 Research
Management). Du fasst Förderausschreibungen so zusammen, wie sie im Newsletter erscheinen:
kompakt, sachlich, ohne Einleitungssätze oder Marketingsprache, direkt auf die
strukturierten Felder beschränkt.

Analysiere die folgende Förderausschreibung und gib NUR die strukturierten Felder aus –
keine Einleitung, kein Kommentar, keine abschließenden Bemerkungen.

REGELN:

1. SPRACHE: Erkenne die Sprache der Ausschreibung automatisch und verfasse die gesamte
   Ausgabe in DERSELBEN Sprache.
   - Englisch → englische Feldbezeichnungen (Title / Aim / Target group / Duration / Funding / Deadline / Further information)
   - Deutsch → deutsche Feldbezeichnungen (Titel / Ziel / Zielgruppe / Laufzeit / Förderhöhe / Fristende / Website)
   - Bei gemischten Texten: dominante Sprache verwenden.

2. FÖRDERHÖHE – KRITISCH:
   Nenne IMMER die Fördersumme PRO PROJEKT oder PRO ANTRAG, nie das Gesamtbudget.
   Zeige immer den Bezugspunkt (per project / je Projekt etc.).
   Phasen/Förderlinien separat auflisten.
   Nur Gesamtbudget bekannt: "not specified per project" / "Keine Angabe je Projekt"

3. ZIELGRUPPE: Antragstyp + antragsberechtigt Institutionen/Personen + relevante Einschränkungen.

4. FRISTENDE: Datum + Verfahrensart in Klammern.
   Bei dauerhaft offenen Calls: "continuously open" / "fortlaufend"

5. FEHLENDE INFORMATIONEN: "not specified" / "Keine Angabe"

6. EIGENANTEIL: Nur wenn explizit gefordert als eigenes Feld, sonst weglassen.

<ausschreibung>
{text}
</ausschreibung>

Ausgabe NUR in diesem Format:

**Title:** / **Titel:**
**Aim:** / **Ziel:** (3–5 sachliche Sätze)
**Target group:** / **Zielgruppe:**
**Duration:** / **Laufzeit:**
**Funding:** / **Förderhöhe:**
**Deadline:** / **Fristende:**
**Further information:** / **Website:**"""

    # Header-Zeile für beide Spalten
    head1, head2 = st.columns(2)
    with head1:
        st.subheader("📝 Prompt")
    with head2:
        h2a, h2b = st.columns([4, 1])
        with h2a:
            st.subheader("📄 Ausschreibungstext")
        with h2b:
            if st.button("🧹 Leeren", key="clear_btn", use_container_width=True):
                st.session_state.text_area_key += 1
                st.session_state.user_text = ""
                st.session_state.url_input = ""
                st.rerun()

    # Textfelder auf gleicher Höhe
    col1, col2 = st.columns(2)

    with col1:
        prompt_template = st.text_area(
            "Prompt bearbeiten (Platzhalter `{text}`)",
            value=default_prompt,
            height=400,
            key="prompt_template"
        )

    with col2:
        user_text = st.text_area(
            "Volltext der Ausschreibung einfügen",
            height=400,
            placeholder="Den kompletten Ausschreibungstext hier einfügen...",
            key=f"user_text_input_{st.session_state.text_area_key}"
        )
        st.session_state.user_text = user_text

        url_input = st.text_input(
            "🔗 URL der Ausschreibung",
            value=st.session_state.get("url_input", ""),
            placeholder="https://...",
            key=f"url_input_{st.session_state.text_area_key}"
        )
        st.session_state.url_input = url_input

    col_b1, col_b2, col_b3 = st.columns([1, 2, 1])
    with col_b2:
        summarize_clicked = st.button(
            "🚀 Ausschreibung zusammenfassen",
            use_container_width=True,
            type="primary",
            key="summarize_btn"
        )

    if summarize_clicked:
        if not st.session_state.user_text.strip():
            st.warning("Bitte Ausschreibungstext eingeben.")
        else:
            with st.spinner("Anfrage an KI:connect …"):
                try:
                    client = LLMClient(api_key=api_key_input if api_key_input else None)
                    if st.session_state.selected_model:
                        client.model = st.session_state.selected_model
                    final_prompt = prompt_template.replace("{text}", st.session_state.user_text)
                    url = st.session_state.get("url_input", "").strip()
                    if url:
                        final_prompt += (
                            f"\n\nDie URL der Ausschreibung lautet: {url}\n"
                            "Trage diese URL exakt so unter 'Further information' / 'Website' ein."
                        )
                    response_text, usage = client.generate(final_prompt, temperature=0.1, max_tokens=2048)
                    st.session_state.response = response_text
                    st.session_state.translated_response = ""
                    update_token_stats(usage)
                except KIConnectError as e:
                    st.error(f"API-Fehler: {e}")
                except Exception as e:
                    st.exception(e)

    if st.session_state.response:
        st.divider()
        st.subheader("📋 Analyse-Ergebnis")
        st.markdown(st.session_state.response)

        cd1, cd2 = st.columns(2)
        with cd1:
            st.download_button(
                "📥 Als Markdown (.md)",
                data=st.session_state.response,
                file_name="antwort.md",
                mime="text/markdown",
                key="dl_md"
            )
        with cd2:
            st.download_button(
                "📄 Als Text (.txt)",
                data=st.session_state.response,
                file_name="antwort.txt",
                mime="text/plain",
                key="dl_txt"
            )

        if st.button("🌐 Ins Englische übersetzen", key="translate_btn"):
            with st.spinner("Übersetze …"):
                try:
                    client = LLMClient(api_key=api_key_input if api_key_input else None)
                    if st.session_state.selected_model:
                        client.model = st.session_state.selected_model
                    translation_prompt = (
                        "Übersetze den folgenden Text präzise und professionell ins Englische.\n"
                        "WICHTIG: Behalte die **exakte Formatierung** bei (Fettdruck, Feldbezeichnungen).\n"
                        "Antworte NUR mit der Übersetzung, ohne Erklärungen.\n\n"
                        f"Text:\n{st.session_state.response}\n\nEnglische Übersetzung:"
                    )
                    translated_text, usage = client.generate(translation_prompt, temperature=0.1, max_tokens=2048)
                    st.session_state.translated_response = translated_text
                    update_token_stats(usage)
                except Exception as e:
                    st.error(f"Übersetzungsfehler: {e}")

    if st.session_state.translated_response:
        st.divider()
        st.subheader("📋 Übersetzung (Englisch)")
        st.markdown(st.session_state.translated_response)
        ct1, ct2 = st.columns(2)
        with ct1:
            st.download_button(
                "📥 Übersetzung als Markdown (.md)",
                data=st.session_state.translated_response,
                file_name="antwort_en.md",
                mime="text/markdown",
                key="dl_en_md"
            )
        with ct2:
            st.download_button(
                "📄 Übersetzung als Text (.txt)",
                data=st.session_state.translated_response,
                file_name="antwort_en.txt",
                mime="text/plain",
                key="dl_en_txt"
            )

# =============================================================================
# Footer
# =============================================================================
st.markdown(
    '<div class="uzk-footer-line">Universität zu Köln · Dezernat 7 Forschungsmanagement</div>',
    unsafe_allow_html=True,
)
