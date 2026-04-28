# 🎓 Newsletteranalyse-Tools · D7 Forschungsmanagement

**Universität zu Köln – Dezernat 7 Forschungsmanagement**

Eine Streamlit-Webanwendung zur Analyse von Förderausschreibungen. Die App kombiniert zwei Werkzeuge: einen **Call Screener** zur automatischen Erkennung von Antragsbeschränkungen und einen **Call Summarizer** zur KI-gestützten Zusammenfassung von Ausschreibungstexten für den Fördernewsletter.

---

## Features

### 📋 Call Screener
- Automatische Prüfung von Förderausschreibungen auf Beschränkungen bei der Anzahl von Anträgen bzw. Skizzen pro Einrichtung
- Unterstützt Batch-Analyse mehrerer URLs gleichzeitig
- Erkennt HTML-Seiten und PDF-Dokumente automatisch
- Regex-basierte Mustererkennung für deutsche und englische Ausschreibungstexte
- Ergebnisübersicht mit Detailansicht und CSV-Export

### 📰 Call Summarizer
- KI-gestützte Zusammenfassung von Förderausschreibungen in strukturierte Felder (Titel, Ziel, Zielgruppe, Laufzeit, Förderhöhe, Fristende, Website)
- Anbindung an die **KI:connect API** der Universität zu Köln / NRW
- Anpassbarer Prompt-Template mit Platzhalter `{text}`
- Automatische Spracherkennung (Deutsch/Englisch)
- Übersetzungsfunktion (Deutsch → Englisch)
- Export als Markdown oder Text
- Token-Verbrauchsanzeige mit Kontextfenster-Monitoring

---

## Tech-Stack

| Komponente | Technologie |
|---|---|
| Frontend / UI | [Streamlit](https://streamlit.io/) |
| LLM-Backend | [KI:connect API](https://chat.kiconnect.nrw/) (OpenAI-kompatibel) |
| Web Scraping | requests, BeautifulSoup4 |
| PDF-Extraktion | pdfplumber |
| Datenverarbeitung | pandas |
| Design | Uni Köln Corporate Design (Albert Sans, UzK-Farbpalette) |

---

## Projektstruktur

```
Newsletter-App-D7/
├── app.py              # Hauptanwendung (Streamlit UI, Call Screener & Summarizer)
├── llm_client.py       # Client für die KI:connect LLM API
├── requirements.txt    # Python-Abhängigkeiten
└── README.md
```

---

## Installation & Setup

### Voraussetzungen
- Python 3.9+
- Ein gültiger **KI:connect API-Key** (Universität zu Köln / NRW)

### Installation

```bash
# Repository klonen
git clone https://github.com/sonni87/Newsletter-App-D7.git
cd Newsletter-App-D7

# Abhängigkeiten installieren
pip install -r requirements.txt
```

### Konfiguration

Der API-Key kann auf drei Wegen bereitgestellt werden:

1. **In der App** – direkt in der Seitenleiste eingeben
2. **Umgebungsvariable** – `export KICONNECT_API_KEY="dein-key"`
3. **Streamlit Secrets** – in `.streamlit/secrets.toml`:
   ```toml
   KICONNECT_API_KEY = "dein-key"
   ```

Optional konfigurierbare Umgebungsvariablen:

| Variable | Standard | Beschreibung |
|---|---|---|
| `KICONNECT_API_KEY` | – | API-Schlüssel (erforderlich) |
| `KICONNECT_BASE_URL` | `https://chat.kiconnect.nrw/api` | API-Basis-URL |
| `KICONNECT_MODEL` | `mistral-small-4-119b-2603` | Standard-Modell |
| `KICONNECT_TIMEOUT` | `60` | Timeout in Sekunden |

---

## Verwendung

```bash
streamlit run app.py
```

Die App öffnet sich im Browser unter `http://localhost:8501`.

### Call Screener
1. URLs von Förderausschreibungen eingeben (eine pro Zeile)
2. **Analyse starten** klicken
3. Ergebnisse in der Tabelle prüfen und optional als CSV exportieren

### Call Summarizer
1. API-Key in der Seitenleiste eingeben und verbinden
2. Ausschreibungstext einfügen und optional die URL angeben
3. **Ausschreibung zusammenfassen** klicken
4. Ergebnis prüfen, ggf. ins Englische übersetzen und als Markdown/Text exportieren

---

## Verfügbare LLM-Modelle

Die App unterstützt die folgenden Modelle über KI:connect (sortiert nach Empfehlung):

| Modell | Empfehlung |
|---|---|
| `mistral-small-4-119b-2603` | ⭐ Empfohlen – bestes Modell für strukturierte Analyse |
| `gpt-oss-120b` | ✅ Gute Alternative |
| `mistral-small-3.2-24b-instruct-2506` | ⚡ Schneller, aber weniger präzise |

---

## Lizenz

Dieses Projekt wurde im Rahmen der Arbeit des Dezernats 7 (Forschungsmanagement) der Universität zu Köln entwickelt.

---

<p align="center"><em>Universität zu Köln · D7 Forschungsmanagement · Newsletteranalyse-Tools v1.5</em></p>
