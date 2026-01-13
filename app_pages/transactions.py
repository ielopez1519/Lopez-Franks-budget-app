import streamlit as st
from db import get_all_transactions, get_accounts
from utils.navigation import safe_rerun


def show_transactions():
    st.header("Transactions")

    accounts = {a["id"]: a["name"] for a in get_accounts()}
    txs = [
        t for t in get_all_transactions()
        if not t.get("deleted")
    ]

    if not txs:
        st.info("No transactions yet.")
        return

    st.subheader("All transactions")

    for t in sorted(txs, key=lambda x: x["date"], reverse=True):
        tx_id = t["id"]
        date = t["date"]
        desc = t.get("description", "")
        category = (t.get("category") or "").lower()
        amount = float(t["amount"])
        tx_type = t.get("type", "expense")
        account_name = accounts.get(t.get("account_id"), "Unknown")

        # Display row
        col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])

        col1.write(date)
        col2.write(desc)
        col3.write(category)
        col4.write(f"${amount:,.2f}")

        if col5.button("Edit", key=f"edit_{tx_id}"):
            st.session_state.edit_tx_id = tx_id
            st.session_state.page = "edit_transaction"
            safe_rerun()

        # Optional: Delete button
        if col5.button("Delete", key=f"delete_{tx_id}"):
            from db import delete_transaction
            delete_transaction(tx_id)
            safe_rerun()
            safe_rerun()
