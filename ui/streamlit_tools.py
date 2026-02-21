"""
streamlit_tools.py

Authors : Pavan R, Badri Ramesh
"""

import re
import logging
import streamlit as st
import pandas as pd

logger = logging.getLogger(__name__)


# -------- App-wide CSS ---------
def app_css():
    st.markdown(
        """
    <style>
    /* --- Global Typography & Body --- */
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
        color: #1D1D1F !important; /* Apple text dark grey */
        background-color: #FFFFFF !important;
        -webkit-font-smoothing: antialiased;
        font-feature-settings: "liga" on, "kern" on;
    }

    /* Force light background on main container */
    .stApp {
        background-color: #FFFFFF !important;
    }

    /* --- Headings --- */
    h1, h2, h3, h4, h5, h6 {
        color: #1D1D1F !important;
        font-weight: 600 !important;
        letter-spacing: -0.01em;
    }
    h1 {
        /* Subtle Apple-style gradient text for main title if desired, or just solid */
        background: linear-gradient(135deg, #1D1D1F 0%, #434344 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.8em;
    }

    /* --- Tables & DataFrames (Clean, Apple-like) --- */
    .stDataFrame, .stTable {
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", sans-serif !important;
    }

    /* Table Container */
    table {
        border-collapse: separate !important; 
        border-spacing: 0;
        width: 100% !important;
        border: 1px solid #E5E5E5 !important;
        border-radius: 12px !important;
        overflow: hidden !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04) !important;
        margin-bottom: 1.5em !important;
        background-color: #FFFFFF !important;
    }

    /* Header */
    thead tr th {
        background-color: #F5F5F7 !important; /* Apple light gray header */
        color: #86868B !important; /* Secondary label color */
        font-weight: 600 !important;
        font-size: 13px !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        border-bottom: 1px solid #D2D2D7 !important;
        padding: 12px 16px !important;
        text-align: left !important;
    }

    /* Body Rows */
    tbody tr td {
        background-color: #FFFFFF !important;
        color: #1D1D1F !important;
        font-size: 14px !important;
        border-bottom: 1px solid #F2F2F7 !important;
        padding: 12px 16px !important;
    }

    /* Hover Effect */
    tbody tr:hover td {
        background-color: #FAFAFC !important; /* Extremely subtle hover */
    }

    /* Remove last border for clean look */
    tbody tr:last-child td {
        border-bottom: none !important;
    }

    /* --- UI Elements --- */
    hr {
        border: 0;
        border-top: 1px solid #E5E5E5 !important;
        margin-top: 24px;
        margin-bottom: 24px;
    }

    /* Buttons (Native Streamlit buttons) - Optional override to match */
    div.stButton > button {
        border-radius: 8px !important;
        font-weight: 500 !important;
        border: 1px solid #E5E5E5 !important;
        background-color: #FFFFFF !important;
        color: #007AFF !important; /* Apple Blue */
        transition: all 0.2s ease;
    }
    div.stButton > button:hover {
        border-color: #007AFF !important;
        background-color: #F0F8FF !important;
    }

    /* --- Feedback Widget Styling --- */
    .feedback-row {
        background-color: #FBFBFD;
        border: 1px solid #E5E5E5;
        border-radius: 12px;
        padding: 12px 16px;
        display: flex; 
        align-items: center; 
        gap: 16px; 
        margin-top: 12px; 
        margin-bottom: 16px;
    }
    .feedback-label { 
        font-weight: 600; 
        font-size: 14px; 
        color: #1D1D1F;
    }
    /* Note: Streamlit buttons inside columns are hard to style via global CSS class alone, 
       so we rely on the container style above. */

    .feedback-summary {
        background-color: #E3F2FD; /* Light Blue Pill */
        border: 1px solid #CEE5FF;
        border-radius: 20px; /* Pill shape */
        padding: 4px 12px;
        color: #007AFF;
        font-size: 13px;
        font-weight: 500;
        margin-left: 10px;
        display: inline-block;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )


def extract_answer(agent_response):
    """
    Extracts the assistant's answer from a response, for both legacy and orchestrator responses.

    For orchestrator: typically a string is passed (preferred); fallback to dict with 'content'.
    """
    try:
        if isinstance(agent_response, str):
            return agent_response
        if isinstance(agent_response, dict) and "content" in agent_response:
            return agent_response["content"]
        if hasattr(agent_response, "content"):
            return agent_response.content
        if isinstance(agent_response, list) and agent_response:
            # Rare, legacy case: list of messages or dicts
            assistant_msgs = []
            for msg in agent_response:
                if isinstance(msg, dict) and msg.get("role") == "assistant":
                    assistant_msgs.append(msg)
                elif hasattr(msg, "role") and msg.role == "assistant":
                    assistant_msgs.append(msg)
            if assistant_msgs:
                last = assistant_msgs[-1]
                if isinstance(last, dict):
                    return last.get("content", "No response.")
                elif hasattr(last, "content"):
                    return last.content
                else:
                    return str(last)
            last = agent_response[-1]
            if isinstance(last, dict):
                return last.get("content", str(last))
            elif hasattr(last, "content"):
                return last.content
            else:
                return str(last)
        elif agent_response is None:
            return "No response."
        else:
            return f"Unknown response type: {type(agent_response)}"
    except Exception as e:
        return f"Error extracting answer: {str(e)}"


# Show how-to-connect instructions only in the About tab
def get_local_ip():
    import socket

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = "localhost"
    finally:
        s.close()
    return ip


# ------------- SIDEBAR --------------
# ------------- IMPROVEMENTS --------------
# ------------- PROMPT SUMMARY --------------
def get_limited_chat_context(history, summary, max_turns=25):
    """
    Returns system+chat message list for LLM:
    - summary goes in a single system message (if any)
    - then up to last `max_turns` user+bot messages
    """
    context = []
    if summary:
        context.append({"role": "system", "content": f"Summary of earlier conversation: {summary}"})
    # Convert (speaker, text) to OpenAI/chat format:
    for speaker, text in history[-max_turns:]:
        if speaker == "You":
            context.append({"role": "user", "content": text})
        else:
            context.append({"role": "assistant", "content": text})
    return context


@st.cache_resource
def process_uploaded_file(uploaded_file):
    # Extract, index, and prepare for question answering. Pre-index uploaded files for faster vector DB integration.
    ...
    # return processed_data


def summarize_chat(messages, prev_summary=""):
    """
    Summarizes a list of (speaker, text) chat tuples using the agent.
    Replace this with a real agent call for ideal results.
    """
    chat_text = "\n".join([f"{speaker}: {text}" for speaker, text in messages])
    # use your agent's summarize capability.
    if not chat_text:
        return prev_summary  # No new content to summarize
    # Simple fallback: concatenate summaries
    return (prev_summary + "\n" + chat_text).strip()[:1000]  # Clip to reasonable length


# ------------- FEEDBACK --------------
def feedback_toggle_sidebar():
    """
    Displays a sidebar toggle for user feedback participation.
    Returns the toggle value (True/False).
    """
    return st.sidebar.toggle(
        "Participate in Feedback? (optional)",
        help=(
            "If enabled, you'll be shown feedback options after each response. All feedback is voluntary. "
            "Feedback and input may be recorded to improve this tool."
        ),
    )


def feedback_widget(response_id, user_message, bot_response):
    if not st.session_state.get("feedback_mode", False):
        return None

    # Use st.columns() with small gaps for each control
    col1, col2, col3, col4, col5 = st.columns([4, 3, 4, 4, 10])

    with col1:
        st.markdown(
            "<span class='feedback-label'>Feedback:</span>",
            unsafe_allow_html=True,
        )
    with col2:
        liked = st.button("👍 Like", key=f"like_{response_id}")
    with col3:
        disliked = st.button("👎 Dislike", key=f"dislike_{response_id}")
    with col4:
        halluc = st.checkbox("🤔 Hallucinated", key=f"halluc_{response_id}")
    with col5:
        # Summary logic
        selection = []
        if liked:
            selection.append("Prefer")
        if disliked:
            selection.append("Don't prefer")
        if halluc:
            selection.append("Hallucination")
        if selection:
            st.markdown(
                f"<span class='feedback-summary'><b>Selected:</b> {' | '.join(selection)}</span>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<span style='color: #86868B; font-size:13px; margin-left:10px;'>No selection</span>",
                unsafe_allow_html=True,
            )

    if liked or disliked or halluc:
        st.success("Thank you for your feedback!")
        feedback = {
            "user_message": user_message,
            "bot_response": bot_response,
            "liked": liked,
            "disliked": disliked,
            "hallucination": halluc,
            "timestamp": pd.Timestamp.now().isoformat(),
        }
        return feedback
    return None