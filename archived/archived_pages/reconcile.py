import streamlit as st
from utils.navigation import safe_rerun
from db import get_transactions_for_account, toggle_cleared


def show_reconcile():
    st.header("Reconcile Account")

    account = st.selectbox("Account", ["Checking", "Savings"])

    txs = get_transactions_for_account(account)

    cleared = [t for t in txs if t["cleared"]]
    uncleared = [t for t in txs if not t["cleared"]]

    cleared_balance = sum(t["amount"] for t in cleared)
    uncleared_balance = sum(t["amount"] for t in uncleared)
    total_balance = cleared_balance + uncleared_balance

    st.subheader("Balances")
    st.write(f"**Cleared Balance:** ${cleared_balance:.2f}")
    st.write(f"**Uncleared Balance:** ${uncleared_balance:.2f}")
    st.write(f"**Total Balance:** ${total_balance:.2f}")

    st.subheader("Uncleared Transactions")

    for t in uncleared:
        col1, col2, col3 = st.columns([4, 2, 1])
        col1.write(f"{t['date']} — {t['description']}")
        col2.write(f"${t['amount']:.2f}")
        if col3.checkbox("Clear", key=f"clear_{t['id']}"):
            toggle_cleared(t["id"], True)
            safe_rerun()  # rerun required to refresh cleared list
