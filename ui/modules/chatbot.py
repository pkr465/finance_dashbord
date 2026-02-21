import logging
import streamlit as st
import json
import io
import pandas as pd
import re
import uuid

# Keep the existing base class import
from .base import PageBase

# Updated: Import the Opex ChatService
from chat.chat_service import ChatService
import streamlit_tools as st_tools

logger = logging.getLogger(__name__)


class ChatBot(PageBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orchestrator: ChatService = self._get_orchestrator()
        self.PLACEHOLDER = "🤖 _Generating response..._"

    @st.cache_resource
    def _get_orchestrator(_self):
        # Initialize the Opex Chat Service
        return ChatService()

    def _render_markdown_table(self, markdown_str):
        """
        Parses a Markdown table string into a clean Streamlit dataframe.
        """
        try:
            # Read markdown table using pipe separator
            df = pd.read_csv(io.StringIO(markdown_str), sep='|', engine='python')
            
            # Clean up column names (remove whitespace)
            df.columns = df.columns.str.strip()
            
            # Drop empty columns often created by leading/trailing pipes in Markdown
            # (Pandas often names these 'Unnamed: 0', 'Unnamed: N')
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            
            # Drop columns that are completely empty (all NaNs)
            df = df.dropna(axis=1, how='all')
            
            # Render interactive table
            st.dataframe(df, use_container_width=True, hide_index=True)
        except Exception as e:
            logger.warning(f"Table parsing failed: {e}")
            # Fallback to raw markdown if parsing fails
            st.markdown(markdown_str)

    def display_formatted_response(self, response_text):
        """
        Intelligently renders the LLM response.
        Handles both standard text and structured JSON from SQL Agents.
        """
        data = response_text
        
        # 1. Try to parse JSON if it's a string
        if isinstance(response_text, str):
            try:
                # specific check to avoid parsing simple text as JSON
                if response_text.strip().startswith("{"):
                    data = json.loads(response_text)
            except json.JSONDecodeError:
                pass # It's just a regular string

        # 2. Check for Structured Agent Response (SQL/Results schema)
        if isinstance(data, dict) and ('sql' in data or 'results' in data):
            
            # A. Render Explanation (Human Readable)
            if 'explanation' in data:
                st.markdown(data['explanation'])
            
            # B. Render Results (Data)
            results = data.get('results')
            if results:
                if isinstance(results, str):
                    if "No results found" in results:
                        st.warning(results)
                    elif "|" in results and "---" in results:
                        # Render as DataFrame
                        self._render_markdown_table(results)
                    else:
                        st.markdown(results)
                elif isinstance(results, list):
                    # Render List of Dicts as DataFrame
                    st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)
                else:
                    st.json(results)

            # C. Render SQL (Hidden in Expander)
            if 'sql' in data:
                with st.expander("🔍 View Generated SQL Query"):
                    st.code(data['sql'], language='sql')
            return

        # 3. Handle Standard Content Wrapper
        if isinstance(data, dict) and "content" in data:
            response_text = data["content"]
        
        # 4. Fallback: Standard Markdown Text (with Table Detection)
        # Split text by markdown table syntax to render tables properly
        parts = re.split(r'(\n\|.*\|\n(?:\|[:\-]+\|(?:\n\|.*\|)+)+)', str(response_text))
        
        for part in parts:
            if not part.strip():
                continue
            # Check if this part looks like a table
            if "|" in part and "---" in part and "\n" in part:
                self._render_markdown_table(part)
            else:
                st.markdown(part)

    def render(self):
        super().render()
        
        # 1. Session Management
        if "chat_session_id" not in st.session_state:
            st.session_state.chat_session_id = str(uuid.uuid4())
            logger.info(f"Created new chat session: {st.session_state.chat_session_id}")
        
        # Sync session
        self.orchestrator.set_session_id(st.session_state.chat_session_id)
        
        # Display Session ID
        st.markdown(
            f"<div style='text-align: right; font-size: 0.7em; color: #888; margin-bottom: 10px;'>"
            f"Session: {st.session_state.chat_session_id[:8]}...</div>",
            unsafe_allow_html=True
        )

        # 2. Welcome Message
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown(
                "<b>Welcome to <span style='color:#FFD700;'>Opex Financial Assistant</span>!</b><br>"
                "Ask me about operational expenses, project budgets, cost centers, or financial documents.",
                unsafe_allow_html=True
            )

        # 3. Example Queries
        sample_queries = [
            {"title": "Total Spend", "prompt": "What is the total spend for the Austin site in Q1?"},
            {"title": "Project Details", "prompt": "Show me the budget breakdown for project 'Orion'."},
            {"title": "Dept Leads", "prompt": "List all unique department leads."},
        ]

        with st.expander("Example Queries"):
            for q in sample_queries:
                st.markdown(f"- **{q['title']}**: \"{q['prompt']}\"")

        # 4. History Initialization
        if "chat_history_chat" not in st.session_state:
            st.session_state.chat_history_chat = []
        if "chat_history_chat_summary" not in st.session_state:
            st.session_state.chat_history_chat_summary = ""

        # 5. Render Chat History
        for idx, (speaker, text) in enumerate(st.session_state.chat_history_chat):
            role = "user" if speaker == "You" else "assistant"
            avatar = "🧑" if role == "user" else "🤖"
            
            with st.chat_message(role, avatar=avatar):
                if role == "assistant":
                    self.display_formatted_response(text)
                else:
                    st.markdown(text)
                
                # Feedback Widget
                if role == "assistant":
                    user_msg = ""
                    if idx > 0 and st.session_state.chat_history_chat[idx - 1][0] == "You":
                        user_msg = st.session_state.chat_history_chat[idx - 1][1]
                    feedback = st_tools.feedback_widget(idx, user_msg, text)
                    if feedback:
                        if "all_feedback" not in st.session_state:
                            st.session_state["all_feedback"] = []
                        st.session_state["all_feedback"].append(feedback)

        # 6. Summarization Logic
        max_turns = 25
        history = st.session_state.chat_history_chat
        if len(history) > max_turns:
            old_messages = history[:-max_turns]
            prev_summary = st.session_state.chat_history_chat_summary
            new_summary = st_tools.summarize_chat(old_messages, prev_summary)
            st.session_state.chat_history_chat_summary = new_summary
            st.session_state.chat_history_chat = history[-max_turns:]           

        # 7. Input Handling
        user_input = st.chat_input("Ask about Opex data...")
        if user_input:
            st.session_state.chat_history_chat.append(("You", user_input))
            st.session_state.chat_history_chat.append(("Assistant", self.PLACEHOLDER))
            st.rerun()

        # 8. Response Generation
        if (
            st.session_state.chat_history_chat and
            st.session_state.chat_history_chat[-1] == ("Assistant", self.PLACEHOLDER)
        ):
            user_message = st.session_state.chat_history_chat[-2][1]
            
            with st.spinner("Assistant is analyzing financial data..."):
                try: 
                    # Call Orchestrator
                    answer = self.orchestrator.ask(user_message)
                except Exception as e:
                    st.error(f"Error: {e}")
                    logger.exception(e)
                    answer = "I encountered an error processing your request."
            
            st.session_state.chat_history_chat[-1] = ("Assistant", answer)
            st.rerun()

        # 9. Footer Controls
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.session_state.get('chat_history_chat'):
                st.download_button(
                    "Download Chat History",
                    "\n".join(f"{speaker}: {text}" for speaker, text in st.session_state['chat_history_chat']),
                    file_name="opex_chat_history.txt",
                )
        with col2:
            with st.expander("Session Info"):
                st.text(f"Session ID:\n{st.session_state.chat_session_id}")
                if st.button("Start New Session"):
                    st.session_state.chat_session_id = str(uuid.uuid4())
                    st.session_state.chat_history_chat = []
                    st.session_state.chat_history_chat_summary = ""
                    st.rerun()