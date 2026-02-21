import streamlit as st
from typing import Literal, Optional


class PageBase:
    def __init__(
        self,
        title: str,
        url: str,
        icon: str = "::",
        layout: Literal["centered", "wide"] = "wide",
        initial_sidebar_state: Literal["expanded", "collapsed", "auto"] = "expanded",
    ):
        self.title = title
        self.icon = icon
        self.layout: Literal["centered", "wide"] = layout
        self.initial_sidebar_state: Literal["expanded", "collapsed", "auto"] = initial_sidebar_state
        self.url = url

    def render(self):
        st.set_page_config(
            page_title=self.title,
            page_icon=self.icon,
            layout=self.layout,
            initial_sidebar_state=self.initial_sidebar_state,
        )
        st.query_params.clear()
        if self.url:
            st.query_params["page"] = self.url
        st.markdown(
            f"<h1 style='text-align:center; margin-top: -20px;'>{self.title}</h1>",
            unsafe_allow_html=True,
        )