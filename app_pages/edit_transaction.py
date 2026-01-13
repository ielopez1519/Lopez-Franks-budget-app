import streamlit as st
from db import get_transaction_by_id, update_transaction, get_accounts
from utils.navigation import safe_rerun


def show_edit_transaction():
    tx_id = st.session_state.get("edit_tx_id")
    if not tx_id:
        st.error("No transaction selected.")
        return

    tx = get_transaction_by_id(tx_id)
    if not tx:
        st.error("Transaction not found.")
        return

    st.header("Edit transaction")

    accounts = get_accounts()
    account_names = [a["name"] for a in accounts]
    account_map = {a["name"]: a["id"] for a in accounts}

    # Pre-fill fields
    date = st.date_input("Date", tx["date"])
    amount = st.number_input("Amount", value=float(tx["amount"]), step=1.0)
    description = st.text_input("Description", tx.get("description", ""))
    category_input = st.text_input("Category", tx.get("category", ""))
    notes = st.text_area("Notes", tx.get("notes", ""))

    account_name = next(
        (a["name"] for a in accounts if a["id"] == tx["account_id"]),
        account_names[0]
    )
    account_name = st.selectbox("Account", account_names, index=account_names.index(account_name))

    col1, col2 = st.columns(2)

    if col1.button("Save changes"):
        category = (category_input or "").strip().lower()

        income_categories = {"income", "paycheck", "deposit", "net paycheck"}
        tx_type = "income" if category in income_categories else "expense"

        update_transaction(
            tx_id,
            {
                "date": date.isoformat(),
                "amount": amount,
                "description": description,
                "category": category,
                "type": tx_type,
                "account_id": account_map[account_name],
                "notes": notes,
            },
        )

        st.success("Transaction updated.")
        st.session_state.page = "transactions"
        safe_rerun()

    if col2.button("Cancel"):
        st.session_state.page = "transactions"
        safe_rerun()
