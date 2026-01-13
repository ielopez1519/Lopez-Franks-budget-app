import streamlit as st
import datetime
import pandas as pd

from db import (
    get_budgets_for_month,
    upsert_budget,
    supabase_url,
)


def show_budget_planner():
    st.title("Budget Planner")

    st.write("SUPABASE URL:", supabase_url)

    # Default to current month
    today = datetime.date.today()
    year = st.number_input("Year", value=today.year, step=1)
    month = st.number_input("Month", value=today.month, min_value=1, max_value=12)

    # Load budgets
    budgets = get_budgets_for_month(int(year), int(month))

    # Convert to DataFrame for easier manipulation
    if budgets:
        df = pd.DataFrame(budgets)
    else:
        df = pd.DataFrame(columns=["category", "amount", "type", "year", "month"])

    # Normalize category to lowercase
    if "category" in df.columns:
        df["category"] = df["category"].astype(str).str.lower()

    # ---------------------------------------------------------
    # Summary (Income / Expenses / Net)
    # ---------------------------------------------------------
    if not df.empty:
        income_total = df[df["type"] == "income"]["amount"].sum()
        expense_total = df[df["type"] != "income"]["amount"].sum()
        net_total = income_total - expense_total

        st.subheader("Planned Summary")

        col1, col2, col3 = st.columns(3)
        col1.metric("Income Planned", f"${income_total:,.2f}")
        col2.metric("Expenses Planned", f"${expense_total:,.2f}")
        col3.metric("Net Planned", f"${net_total:,.2f}")
    else:
        st.info("No planned budgets for this month yet.")

    st.markdown("---")

    # Helper to render each section
    def render_section(title, section_type):
        st.subheader(title)

        # Filter for this section
        section_df = df[df["type"] == section_type].copy()

        if section_df.empty:
            st.info(f"No {title.lower()} set for this month.")
            return # <-- IMPORTANT: stop here if no rows

        # IMPORTANT: keep id internally, but hide it from the UI
        internal_df = section_df[["id", "category", "amount"]].copy()

        # Show only category + amount to the user
        edited_df = st.data_editor(
            internal_df.drop(columns=["id"]), # hide id from UI
            num_rows="dynamic",
            key=f"editor_{section_type}",
        )

        # Reattach id after editing
        edited_df = edited_df.join(internal_df["id"], how="left")

        col1, col2 = st.columns([1, 1])

        # Save changes
        if col1.button(f"Save {title}", key=f"save_{section_type}"):
            for _, row in edited_df.iterrows():
                upsert_budget(
                    id=row["id"], # <-- this is the critical fix 
                    category=row["category"], 
                    year=int(year), 
                    month=int(month), 
                    amount=float(row["amount"]), 
                    btype=section_type,
                )
            st.success(f"{title} saved.")

        # Add new row
        with col2:
            with st.expander(f"Add new {title} category"):
                new_cat = st.text_input(f"New {title} category", key=f"new_{section_type}_cat")
                new_amt = st.number_input(
                    f"{title} amount",
                    min_value=0.0,
                    step=50.0,
                    key=f"new_{section_type}_amt",
                )

                if st.button(f"Add {title}", key=f"add_{section_type}"):
                    if new_cat.strip() == "":
                        st.error("Category name cannot be empty.")
                    else:
                        upsert_budget(
                            category=new_cat.strip().lower(),
                            year=int(year),
                            month=int(month),
                            amount=float(new_amt),
                            btype=section_type,
                        )
                        st.success(f"{title} added.")
                        st.experimental_rerun()

        st.markdown("---")

    # Render each section
    render_section("Income", "income")
    render_section("Bills", "bill")
    render_section("Budgets", "budget")
    render_section("Savings", "savings")
