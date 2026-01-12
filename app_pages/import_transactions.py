import streamlit as st
import pandas as pd
from utils.navigation import safe_rerun
from db import insert_transaction, apply_category_rules


def show_import_transactions():
    st.header("Import Transactions")

    file = st.file_uploader("Upload CSV", type=["csv"])
    if not file:
        return

    df = pd.read_csv(file)
    st.write("Preview:")
    st.dataframe(df.head())

    st.subheader("Column Mapping")

    columns = df.columns.tolist()

    date_col = st.selectbox("Date Column", columns)
    amount_col = st.selectbox("Amount Column", columns)
    desc_col = st.selectbox("Description Column", columns)
    category_col = st.selectbox("Category Column (optional)", ["None"] + columns)
    account_col = st.selectbox("Account Column (optional)", ["None"] + columns)

    if st.button("Import"):
        for _, row in df.iterrows():
            category = None
            if category_col != "None":
                category = row[category_col]

            auto_category = apply_category_rules(row[desc_col])
            category = auto_category or category or "Uncategorized"

            insert_transaction({
                "date": row[date_col],
                "amount": float(row[amount_col]),
                "description": row[desc_col],
                "category": category,
                "account": row[account_col] if account_col != "None" else "Checking"
            })

        st.success("Imported!")

        # rerun required to return to transactions
        st.session_state.page = "transactions"
        safe_rerun()

