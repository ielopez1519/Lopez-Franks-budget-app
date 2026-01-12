import streamlit as st
from utils.navigation import safe_rerun
from db import get_accounts, get_account_balance


def show_accounts():
    st.header("Accounts")

    accounts = get_accounts()
    if not accounts:
        st.info("No accounts yet. Add some in Supabase or your setup flow.")
        return

    st.subheader("Account balances")

    total_balance = 0.0
    for acc in accounts:
        balance = get_account_balance(acc["id"])
        total_balance += balance

        col1, col2 = st.columns([3, 1])
        col1.write(acc["name"])
        col2.write(f"${balance:,.2f}")

    st.markdown("---")
    st.subheader("Total")
    st.write(f"Total balance: ${total_balance:,.2f}")

    st.markdown("---")
    if st.button("Go to transactions"):
        st.session_state.page = "transactions"
        safe_rerun()
