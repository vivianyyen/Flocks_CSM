"""
utils/chatbot.py
AI analyst chatbot powered by Claude claude-sonnet-4-20250514 via Anthropic API.
Receives the filtered dashboard DataFrame as context.
"""

import streamlit as st
import google.generativeai as genai
import pandas as pd
import json


def _build_system_prompt(df: pd.DataFrame) -> str:
    """Summarise the current dashboard data for the LLM context."""
    summary_lines = [
        "You are an expert cybersecurity and incident intelligence analyst.",
        "You are embedded in a live incident monitoring dashboard.",
        "Answer questions concisely and accurately using the data context below.",
        "If asked to analyse trends, patterns, or predictions, reason step-by-step.",
        "",
        "=== CURRENT DASHBOARD DATA SUMMARY ===",
        f"Total incidents loaded: {len(df)}",
    ]

    if "category" in df.columns:
        cats = df["category"].value_counts().head(5).to_dict()
        summary_lines.append(f"Top categories: {json.dumps(cats)}")

    if "incident_type" in df.columns:
        types = df["incident_type"].value_counts().head(5).to_dict()
        summary_lines.append(f"Top incident types: {json.dumps(types)}")

    if "country" in df.columns:
        countries = df["country"].value_counts().head(5).to_dict()
        summary_lines.append(f"Top affected countries: {json.dumps(countries)}")

    if "impact" in df.columns:
        impacts = df["impact"].value_counts().to_dict()
        summary_lines.append(f"Impact breakdown: {json.dumps(impacts)}")

    if "source" in df.columns:
        sources = df["source"].value_counts().head(5).to_dict()
        summary_lines.append(f"Top sources: {json.dumps(sources)}")

    if "incident_date" in df.columns:
        df_dated = df.dropna(subset=["incident_date"])
        if not df_dated.empty:
            summary_lines.append(
                f"Date range: {df_dated['incident_date'].min().date()} to {df_dated['incident_date'].max().date()}"
            )

    summary_lines += [
        "===",
        "",
        "Respond in clear, concise English. Use bullet points for lists.",
        "If asked about predictions or future trends, clarify these are analytical estimates.",
    ]
    return "\n".join(summary_lines)


def _get_client():
    try:
        genai.configure(api_key=st.secrets["google"]["api_key"])
        return genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            system_instruction=None   # set per-call below
        )
    except Exception:
        return None


def chatbot_ui(df: pd.DataFrame):
    """Render the chatbot UI at the bottom of the dashboard."""

    # Session state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Suggested prompts
    suggestions = [
        "What are the top 3 most critical incidents?",
        "Which country has the most incidents?",
        "Summarise the main threat categories this period.",
        "Are there any emerging trends in the data?",
        "Which incident type appears most frequently?",
    ]

    st.markdown("""
    <style>
    .chat-container {
        background: #161b22;
        border: 1px solid #21262d;
        border-radius: 12px;
        padding: 16px 20px;
        max-height: 420px;
        overflow-y: auto;
        margin-bottom: 12px;
    }
    .chat-msg-user {
        background: #1f3349;
        border-left: 3px solid #388bfd;
        padding: 10px 14px;
        border-radius: 0 8px 8px 0;
        margin: 8px 0;
        font-size: 14px;
        color: #c9d1d9;
    }
    .chat-msg-bot {
        background: #1a1f2e;
        border-left: 3px solid #3fb950;
        padding: 10px 14px;
        border-radius: 0 8px 8px 0;
        margin: 8px 0;
        font-size: 14px;
        color: #c9d1d9;
        line-height: 1.6;
    }
    .chat-role {
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.08em;
        margin-bottom: 4px;
        text-transform: uppercase;
    }
    .user-role { color: #388bfd; }
    .bot-role  { color: #3fb950; }
    </style>
    """, unsafe_allow_html=True)

    # Suggestion chips
    st.markdown("<p style='font-size:12px;color:#484f58;margin-bottom:6px'>Suggested questions:</p>", unsafe_allow_html=True)
    cols = st.columns(len(suggestions))
    for i, (col, s) in enumerate(zip(cols, suggestions)):
        if col.button(s, key=f"suggest_{i}", use_container_width=True):
            st.session_state.chat_history.append({"role": "user", "content": s})
            st.session_state._pending_question = s

    # Chat history display
    if st.session_state.chat_history:
        chat_html = "<div class='chat-container'>"
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                chat_html += f"<div class='chat-msg-user'><div class='chat-role user-role'>You</div>{msg['content']}</div>"
            else:
                content = msg["content"].replace("\n", "<br>")
                chat_html += f"<div class='chat-msg-bot'><div class='chat-role bot-role'>AI Analyst</div>{content}</div>"
        chat_html += "</div>"
        st.markdown(chat_html, unsafe_allow_html=True)

    # Input
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input(
            "Ask the AI analyst…",
            placeholder="e.g. What are the most affected entities this month?",
            label_visibility="collapsed"
        )
        submitted = st.form_submit_button("Send →", use_container_width=False)

    question = None
    if submitted and user_input.strip():
        question = user_input.strip()
        st.session_state.chat_history.append({"role": "user", "content": question})
    elif hasattr(st.session_state, "_pending_question"):
        question = st.session_state._pending_question
        del st.session_state._pending_question

    # Generate response
    if question:
    client = _get_client()
    if client is None:
        st.warning("Gemini API key not configured. Add [gemini] block to secrets.toml.")
    else:
        with st.spinner("AI analyst is thinking…"):
            try:
                # Build history in Gemini format (roles: "user" / "model")
                history = []
                # Inject system prompt as first user/model exchange
                history.append({"role": "user",  "parts": [_build_system_prompt(df)]})
                history.append({"role": "model", "parts": ["Understood. I'm ready to analyse the incident data."]})

                for m in st.session_state.chat_history[:-1]:  # all except latest
                    role = "model" if m["role"] == "assistant" else "user"
                    history.append({"role": role, "parts": [m["content"]]})

                model = genai.GenerativeModel("gemini-2.0-flash")
                chat  = model.start_chat(history=history)
                response = chat.send_message(question)
                answer = response.text

                st.session_state.chat_history.append({"role": "assistant", "content": answer})
                st.rerun()
            except Exception as e:
                st.error(f"Chatbot error: {e}")

    # Clear button
    if st.session_state.chat_history:
        if st.button("Clear conversation", type="secondary"):
            st.session_state.chat_history = []
            st.rerun()
