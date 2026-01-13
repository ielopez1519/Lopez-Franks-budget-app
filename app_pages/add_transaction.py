import streamlit as st
import datetime
from utils.navigation import safe_rerun
from db import get_accounts, insert_transaction


def show_add_transaction():
    st.header("Add transaction")

    accounts = get_accounts()
    if not accounts:
        st.error("You must create an account first.")
        return

    date = st.date_input("Date", datetime.date.today())
    amount = st.number_input("Amount", value=0.0, step=1.0)
    description = st.text_input("Description")
    category_input = st.text_input("Category")
    notes = st.text_area("Notes", "")

    account_names = [a["name"] for a in accounts]
    account_name = st.selectbox("Account", account_names)
    account_id = next(a["id"] for a in accounts if a["name"] == account_name)

    col1, col2 = st.columns(2)

    if col1.button("Save", key="add_tx_save"):
        if not description:
            st.error("Description is required.")
            return
        if amount == 0.0:
            st.error("Amount cannot be zero.")
            return

        # Normalize category
        category = (category_input or "").strip().lower() or None

        # Determine transaction type
        income_categories = {"income", "paycheck", "deposit", "net paycheck"}

        if category in income_categories:
            tx_type = "income"
        else:
            tx_type = "expense"

        insert_transaction(
            {
                "date": date.isoformat(),
                "amount": amount,
                "description": description,
                "category": category,
                "type": tx_type,  # NEW FIELD
                "account_id": account_id,
                "notes": notes,
                "deleted": False,
                "is_split_parent": False,
                "parent_id": None,
            }
        )

        st.success("Transaction added.")
        st.session_state.page = "transactions"
        safe_rerun()

    if col2.button("Cancel", key="add_tx_cancel"):
        st.session_state.page = "transactions"
        safe_rerun()
