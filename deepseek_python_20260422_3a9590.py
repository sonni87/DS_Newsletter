import os
# ...

with st.sidebar:
    st.header("⚙️ Konfiguration")
    api_key_input = st.text_input(
        "KIConnect API-Key",
        type="password",
        placeholder="Aus Umgebungsvariable/Secrets",
        help="Wird automatisch aus Streamlit Secrets oder KICONNECT_API_KEY geladen."
    )

    # Modellname direkt aus Umgebungsvariable lesen
    model_name = os.environ.get("KICONNECT_MODEL", "llama3.2:latest")
    st.markdown(f"**Aktives Modell:** `{model_name}`")

    if st.button("🔌 API-Verbindung testen"):
        try:
            client = LLMClient(api_key=api_key_input if api_key_input else None)
            if client.check_connection():
                st.success("✅ Verbindung erfolgreich!")
            else:
                st.error("❌ Verbindung fehlgeschlagen. API-Key prüfen.")
        except Exception as e:
            st.error(f"❌ Fehler: {e}")

    st.divider()