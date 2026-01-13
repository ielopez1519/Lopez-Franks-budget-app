import streamlit as st
from db import get_accounts, get_all_transactions


def show_accounts():
    st.header("Accounts")

    accounts = get_accounts()
    if not accounts:
        st.info("No accounts yet.")
        return

    # Fetch all non-deleted, non-split-parent transactions
    txs = [
        t for t in get_all_transactions()
        if not t.get("deleted")
        and not t.get("is_split_parent")
    ]

    # Build a balance map
    balances = {acc["id"]: 0.0 for acc in accounts}

    for t in txs:
        acc_id = t.get("account_id")
        amt = float(t["amount"])
        tx_type = t.get("type", "expense")

        # Transfers will be handled in v1.2
        if tx_type == "transfer":
            continue

        # Income increases the account balance
        if tx_type == "income":
            balances[acc_id] += amt

        # Expenses decrease the account balance
        else:
            balances[acc_id] -= amt

    # Display account balances
    st.subheader("Account balances")

    total_balance = 0.0
    for acc in accounts:
        bal = balances.get(acc["id"], 0.0)
        total_balance += bal
        st.write(f"**{acc['name']}**: ${bal:,.2f}")

    st.markdown("---")
    st.write(f"**Total balance:** ${total_balance:,.2f}")
