import streamlit as st
from .base import PageBase


class FAQ(PageBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def render(self):
        super().render()
        st.markdown("## FAQ")
        FAQS = [
            ("How do I upload a file?", "Use the sidebar uploader to add .xlsx or .csv files to the workspace."),
            ("What data formats are supported?", "We support Excel (.xlsx) and CSV files for Opex data ingestion."),
            ("How do I use the chatbot?", "Navigate to the 'Chatbot' page and ask natural language questions about your financial data."),
        ]
        query = st.text_input("Search FAQs...")
        for q, a in FAQS:
            if query.lower() in q.lower() or query.lower() in a.lower() or not query:
                st.markdown(f"**Q:** {q}  \n  **A:** {a}")