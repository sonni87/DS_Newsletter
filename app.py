"""
Streamlit App – Simple Prompt Client for KI:connect with Markdown Export.
"""

import streamlit as st
from llm_client import LLMClient, KIConnectError

st.set_page_config(page_title="KI:connect Prompt", page_icon="🤖", layout="wide")
st.title("🤖 KI:connect – Flexible Prompt Client")
st.markdown("Enter your prompt and the call text. The response is displayed in Markdown and can be exported.")

# Session State
if "response" not in st.session_state:
    st.session_state.response = ""
if "available_models" not in st.session_state:
    st.session_state.available_models = []
if "selected_model" not in st.session_state:
    st.session_state.selected_model = None

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key_input = st.text_input(
        "KIConnect API Key",
        type="password",
        placeholder="From environment / secrets",
        help="Automatically loaded from Streamlit secrets or KICONNECT_API_KEY."
    )

    if st.button("🔌 Test Connection & Load Models"):
        try:
            client = LLMClient(api_key=api_key_input if api_key_input else None)
            if client.check_connection():
                st.success("✅ Connection successful!")
                models = client.list_models()
                st.session_state.available_models = models
                st.success(f"✅ {len(models)} models loaded!")
            else:
                st.error("❌ Connection failed.")
        except Exception as e:
            st.error(f"❌ Error: {e}")

    if st.session_state.available_models:
        st.divider()
        st.subheader("🤖 Model Selection")
        if st.session_state.selected_model not in st.session_state.available_models:
            st.session_state.selected_model = st.session_state.available_models[0]
        st.session_state.selected_model = st.selectbox(
            "Choose a model:",
            options=st.session_state.available_models,
            index=st.session_state.available_models.index(st.session_state.selected_model)
        )
        st.markdown(f"**Active model:** `{st.session_state.selected_model}`")

    st.divider()
    temperature = st.slider("Temperature", 0.0, 1.0, 0.1, 0.05)
    max_tokens = st.number_input("Max Tokens", 100, 4096, 2048, 100)

# Default prompt (English, 4–6 sentences for Funding)
default_prompt = """You are an expert in research funding and create entries for a funding newsletter (D7 format).
Analyze the following text of a call for proposals and create a short, structured summary with these fields:

**Funding:** (4-6 sentences: What is funded? What is the aim? What costs are eligible?)
**Target group:** (Who is eligible to apply? Which institutions/persons?)
**Duration:** (Project duration, if not stated write "Not specified")
**Funding amount:** (Maximum funding amount or percentage, otherwise "Not specified")
**Deadline:** (Submission deadline, otherwise "Not specified")
**Website:** (URL of the call)

Text of the call:
{text}

Answer ONLY with the formatted fields. No additional explanations."""

# Two columns with equal height
col1, col2 = st.columns(2)
with col1:
    st.subheader("📝 Prompt")
    prompt_template = st.text_area(
        "Edit your prompt (use `{text}` as placeholder)",
        value=default_prompt,
        height=400
    )
with col2:
    st.subheader("📄 Call Text")
    user_text = st.text_area(
        "Paste the full text of the call here",
        height=400,
        placeholder="Paste the complete call text..."
    )

if st.button("🚀 Send Prompt", type="primary"):
    if not user_text.strip():
        st.warning("Please enter the call text.")
    else:
        with st.spinner("Requesting KI:connect ..."):
            try:
                client = LLMClient(api_key=api_key_input if api_key_input else None)
                if st.session_state.selected_model:
                    client.model = st.session_state.selected_model
                final_prompt = prompt_template.replace("{text}", user_text)
                response = client.generate(final_prompt, temperature=temperature, max_tokens=max_tokens)
                st.session_state.response = response
            except KIConnectError as e:
                st.error(f"API Error: {e}")
            except Exception as e:
                st.exception(e)

if st.session_state.response:
    st.divider()
    st.subheader("📋 Response")
    st.markdown(st.session_state.response)

    col_down1, col_down2 = st.columns(2)
    with col_down1:
        st.download_button(
            label="📥 Download as Markdown (.md)",
            data=st.session_state.response,
            file_name="ki_response.md",
            mime="text/markdown"
        )
    with col_down2:
        st.download_button(
            label="📄 Download as Text (.txt)",
            data=st.session_state.response,
            file_name="ki_response.txt",
            mime="text/plain"
        )
