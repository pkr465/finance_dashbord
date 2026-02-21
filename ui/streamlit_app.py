import streamlit as st
import logging
from typing import Optional

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import Existing Modules
from ui.modules.chatbot import ChatBot
from ui.modules.summary import Summary
from ui.modules.faq import FAQ
from ui.modules.about import About
from ui.modules.chat_history import ChatHistory

# Import New Analytic Modules
from ui.modules.metrics_financial_trends import FinancialTrends
from ui.modules.metrics_dept_rollup import DeptRollup
from ui.modules.metrics_resource_allocation import ResourceAllocation
from ui.modules.metrics_geo_org import GeoOrgMetrics
from ui.modules.plotting_sandbox import SandboxPage

# Define Pages
PAGES = {
    "Summary": Summary(title="Project Summary", url="summary"),
    "Financial Trends": FinancialTrends(title="Financial Trends", url="financial_trends"),
    "Resource Alloc": ResourceAllocation(title="Resource Allocation", url="resource_allocation"),
    "Dept Rollup": DeptRollup(title="Dept Rollup", url="department_rollup"),
    "Geo & Org": GeoOrgMetrics(title="Geo & Org Analytics", url="geo_org"),
    "Sandbox": SandboxPage(title="Plotting Sandbox", url="sandbox"),
    "ChatBot": ChatBot(title="Opex Chat", url="chatbot"),
    "FAQ": FAQ(title="FAQ", url="faq"),
    "About": About(title="About", url="about"),
    "History": ChatHistory(title="Chat History (Admin)", url="history"),
}

# Default Page
DEFAULT_PAGE = PAGES["ChatBot"].url
DEFAULT_PAGE_URL = DEFAULT_PAGE

def canonical(slug: Optional[str]) -> str:
    """Validate and return the canonical slug for a page."""
    if slug is None:
        return DEFAULT_PAGE_URL
    
    # Check if slug matches any page URL
    for page in PAGES.values():
        if slug == page.url:
            return slug
    
    return DEFAULT_PAGE_URL

def main():
    # Must be the first Streamlit command
    st.set_page_config(layout="wide", page_title="Opex Dashboard")
    
    # 1. Router Logic
    query_params = st.query_params
    current_page_slug = query_params.get("page", DEFAULT_PAGE_URL)
    
    # Validate slug
    valid_slug = canonical(current_page_slug)
    
    # Find the page object
    current_page = None
    for page in PAGES.values():
        if page.url == valid_slug:
            current_page = page
            break
            
    if not current_page:
        current_page = PAGES["ChatBot"]

    # 2. Sidebar Navigation
    with st.sidebar:
        st.title("Navigation")
        
        # Iterating through pages to create navigation buttons
        for key, page in PAGES.items():
            # Highlight the active button
            button_type = "primary" if page == current_page else "secondary"
            if st.button(key, use_container_width=True, type=button_type):
                st.query_params["page"] = page.url
                st.rerun()

    # 3. Render Page
    try:
        current_page.render()
    except Exception as e:
        st.error(f"An error occurred rendering the page: {e}")
        logger.exception(e)

if __name__ == "__main__":
    main()