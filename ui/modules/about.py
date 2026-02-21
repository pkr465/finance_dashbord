import streamlit as st
from .base import PageBase


class About(PageBase):
    def render(self):
        super().render()
        st.info("Financials Dashboard powered by Genie.")