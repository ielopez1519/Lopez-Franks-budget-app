import streamlit as st
from utils.navigation import safe_rerun
from db import (
    get_all_transactions,
    delete_transaction,
    delete_transaction_family,
)


def show_transactions():
    st.header("Transactions")

    # -----------------------------
    # Filters
    # -----------------------------
    st.subheader("Search & Filters")
    col1, col2, col3 = st.columns(3)

    search_text = col1.text_input("Search description")
    category_filter = col2.text_input("Category filter")
    account_filter = col3.text_input("Account name filter")

    txs = get_all_transactions()

    # Group children by parent_id
    children_by_parent = {}
    for t in txs:
        pid = t.get("parent_id")
        if pid:
            children_by_parent.setdefault(pid, []).append(t)

    # Show only top-level rows (normal + parents) in main list
    parents = [t for t in txs if t.get("parent_id") is None]

    filtered = []
    for t in parents:
        account_name = t["accounts"]["name"]
        category = t.get("category") or ""
        desc = t["description"]

        if search_text and search_text.lower() not in desc.lower():
            continue
        if category_filter and category_filter.lower() not in category.lower():
            continue
        if account_filter and account_filter.lower() not in account_name.lower():
            continue

        filtered.append(t)

    st.write(f"Showing {len(filtered)} primary transactions")

    # -----------------------------
    # Transaction list
    # -----------------------------
    st.subheader("Transaction list")

    for t in filtered:
        account_name = t["accounts"]["name"]
        is_split_parent = t.get("is_split_parent", False)

        col1, col2, col3, col4, col5, col6 = st.columns([2, 3, 2, 2, 1, 1])
        col1.write(t["date"])
        col2.write(f"{t['description']} ({account_name})")
        col3.write(f"${t['amount']:,.2f}")

        if is_split_parent:
            col4.markdown(
                "<span style='background-color:#ffcc80;padding:2px 6px;"
                "border-radius:4px;'>Split</span>",
                unsafe_allow_html=True,
            )
        else:
            col4.write(t.get("category") or "")

        edit_btn = col5.button("Edit", key=f"edit_{t['id']}")
        delete_btn = col6.button("Delete", key=f"delete_{t['id']}")

        if edit_btn:
            st.session_state.transaction_id = t["id"]
            st.session_state.page = "edit_transaction"
            safe_rerun()

        if delete_btn:
            if is_split_parent:
                delete_transaction_family(t["id"])
            else:
                delete_transaction(t["id"])
            safe_rerun()

        # Children under split parent
        if is_split_parent:
            children = children_by_parent.get(t["id"], [])
            for c in children:
                ccol1, ccol2, ccol3, ccol4, ccol5, ccol6 = st.columns(
                    [2, 3, 2, 2, 1, 1]
                )
                ccol1.write("")
                ccol2.write(f"↳ {c['description']}")
                ccol3.write(f"${c['amount']:,.2f}")
                ccol4.write(c.get("category") or "")
                ccol5.write("")
                ccol6.write("")

    st.markdown("---")
    colA, colB = st.columns(2)

    if colA.button("Add transaction", key="tx_add"):
        st.session_state.page = "add_transaction"
        safe_rerun()

    if colB.button("Go to budgets", key="tx_budgets"):
        st.session_state.page = "budgets"
        safe_rerun()
