import streamlit as st
from db import get_all_transactions, get_child_transactions


def show_debug_splits():
    st.header("Debug: split transactions")

    txs = get_all_transactions()
    parents = [t for t in txs if t.get("is_split_parent", False)]

    st.write(f"Found {len(parents)} split parent transactions.")

    for p in parents:
        st.markdown("---")
        st.subheader(f"Parent: {p['description']} (${p['amount']:,.2f})")
        st.write(
            {
                "id": p["id"],
                "date": p["date"],
                "category": p.get("category"),
                "account_id": p["account_id"],
                "is_split_parent": p.get("is_split_parent"),
                "parent_id": p.get("parent_id"),
            }
        )

        children = get_child_transactions(p["id"])
        st.write(f"Children ({len(children)}):")
        for c in children:
            st.write(
                {
                    "id": c["id"],
                    "amount": c["amount"],
                    "category": c.get("category"),
                    "date": c["date"],
                    "parent_id": c.get("parent_id"),
                    "is_split_parent": c.get("is_split_parent"),
                }
            )
