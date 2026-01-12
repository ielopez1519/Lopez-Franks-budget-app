import streamlit as st
from utils.navigation import safe_rerun
from db import (
    get_transaction,
    update_transaction,
    delete_transaction,
    get_accounts,
    get_child_transactions,
    clear_children,
    create_split_children,
    delete_transaction_family,
)


def show_edit_transaction():
    st.header("Edit transaction")

    transaction_id = st.session_state.get("transaction_id")
    if not transaction_id:
        st.error("No transaction selected.")
        return

    tx = get_transaction(transaction_id)
    accounts = get_accounts()

    is_split_parent = tx.get("is_split_parent", False)

    date = st.date_input("Date", tx["date"])
    amount = st.number_input("Amount", value=float(tx["amount"]))
    description = st.text_input("Description", tx["description"])
    notes = st.text_area("Notes", tx.get("notes", ""))

    account_names = [a["name"] for a in accounts]
    current_account = tx["accounts"]["name"]
    account_name = st.selectbox(
        "Account",
        account_names,
        index=account_names.index(current_account),
    )
    account_id = next(a["id"] for a in accounts if a["name"] == account_name)

    if not is_split_parent:
        category = st.text_input("Category", tx.get("category") or "")
    else:
        st.write("Category: Split (children have their own categories)")
        category = "Split"

    st.markdown("---")

    # Split UI
    st.subheader("Split transaction")

    existing_children = get_child_transactions(transaction_id) if is_split_parent else []

    split_mode = st.checkbox(
        "Treat this as a split transaction",
        value=is_split_parent,
        help="If enabled, this transaction becomes a parent with multiple child splits.",
    )

    split_rows = []

    if split_mode:
        st.info("Enter one or more split lines. The total should match the amount.")

        if existing_children:
            st.write("Existing splits:")
            for idx, child in enumerate(existing_children):
                ccol1, ccol2 = st.columns([3, 1])
                cat = ccol1.text_input(
                    "Category",
                    value=child.get("category") or "",
                    key=f"split_cat_existing_{idx}",
                )
                amt = ccol2.number_input(
                    "Amount",
                    value=float(child["amount"]),
                    step=1.0,
                    key=f"split_amt_existing_{idx}",
                )
                split_rows.append({"category": cat, "amount": amt})

        st.write("Add new split lines:")
        for idx in range(3):
            ccol1, ccol2 = st.columns([3, 1])
            cat = ccol1.text_input(
                "Category",
                value="",
                key=f"split_cat_new_{idx}",
            )
            amt = ccol2.number_input(
                "Amount",
                value=0.0,
                step=1.0,
                key=f"split_amt_new_{idx}",
            )
            if cat and amt != 0.0:
                split_rows.append({"category": cat, "amount": amt})

        total_splits = sum(r["amount"] for r in split_rows)
        st.write(
            f"Total of splits: ${total_splits:,.2f} "
            f"(transaction amount: ${amount:,.2f})"
        )

    st.markdown("---")

    col_save, col_delete = st.columns(2)

    if col_save.button("Save changes", key="edit_tx_save"):
        if split_mode:
            total_splits = sum(r["amount"] for r in split_rows)
            if abs(total_splits - amount) > 0.01:
                st.error(
                    "Total of splits does not match the transaction amount. "
                    "Adjust either the amount or the splits."
                )
                return

            update_transaction(
                transaction_id,
                {
                    "date": date.isoformat(),
                    "amount": amount,
                    "description": description,
                    "notes": notes,
                    "account_id": account_id,
                    "category": "Split",
                    "is_split_parent": True,
                    "parent_id": None,
                },
            )

            clear_children(transaction_id)
            create_split_children(
                parent_id=transaction_id,
                date=date.isoformat(),
                account_id=account_id,
                description=description,
                notes=notes,
                splits=split_rows,
            )

        else:
            update_transaction(
                transaction_id,
                {
                    "date": date.isoformat(),
                    "amount": amount,
                    "category": category,
                    "description": description,
                    "notes": notes,
                    "account_id": account_id,
                    "is_split_parent": False,
                    "parent_id": None,
                },
            )
            if is_split_parent:
                clear_children(transaction_id)

        st.success("Updated.")
        st.session_state.page = "transactions"
        safe_rerun()

    if col_delete.button("Delete transaction", key="edit_tx_delete"):
        if is_split_parent:
            delete_transaction_family(transaction_id)
        else:
            delete_transaction(transaction_id)
        st.success("Deleted.")
        st.session_state.page = "transactions"
        safe_rerun()
