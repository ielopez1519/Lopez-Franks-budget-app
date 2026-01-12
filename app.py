"""
app.py

Single entry point for the Streamlit app.
Handles:
- Page routing via session_state.page
- Top navigation bar
"""

import streamlit as st
from utils.navigation import safe_rerun

from app_pages.dashboard import show_dashboard
from app_pages.accounts import show_accounts
from app_pages.transactions import show_transactions
from app_pages.add_transaction import show_add_transaction
from app_pages.edit_transaction import show_edit_transaction
from app_pages.budget_planner import show_budget_planner
from app_pages.debug_splits import show_debug_splits
from config import APP_VERSION

st.set_page_config(
    page_title="Lopez-Franks Budget App",
    layout="wide",
)

# Initialize session state keys
if "page" not in st.session_state:
    st.session_state.page = "dashboard"

if "transaction_id" not in st.session_state:
    st.session_state.transaction_id = None

def navigate_to(page_name: str, **kwargs):
    """
    Centralized navigation helper.
    - Sets any extra session_state keys passed via kwargs.
    - Sets the current page.
    - Triggers a safe rerun.
    """
    for key, value in kwargs.items():
        st.session_state[key] = value
    st.session_state.page = page_name
    safe_rerun()

def render_navbar():
    """
    Simple top navbar with four main sections.
    """
    st.markdown("### Lopez-Franks Budget App")

    col1, col2, col3, col4 = st.columns(4)

    if col1.button("Dashboard", key="nav_dashboard"):
        navigate_to("dashboard")
    if col2.button("Accounts", key="nav_accounts"):
        navigate_to("accounts")
    if col3.button("Transactions", key="nav_transactions"):
        navigate_to("transactions")
    if col4.button("Budgets", key="nav_budgets"):
        navigate_to("budgets")

    # 🔥 Version label (this is the only addition)
    st.caption(f"Version {APP_VERSION}")

def main():
    render_navbar()

    page = st.session_state.page

    if page == "dashboard":
        show_dashboard()
    elif page == "accounts":
        show_accounts()
    elif page == "transactions":
        show_transactions()
    elif page == "add_transaction":
        show_add_transaction()
    elif page == "edit_transaction":
        show_edit_transaction()
    elif page == "budgets":
        show_budget_planner()
    else:
        st.error(f"Unknown page: {page}")

if __name__ == "__main__":
    main()
