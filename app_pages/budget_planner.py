import streamlit as st
import datetime
from db import get_budgets_for_month, upsert_budget
from utils.navigation import safe_rerun


# ---------------------------------------------------------
# Summary Renderer (Income / Expenses / Net)
# ---------------------------------------------------------
def render_budget_summary(budgets):
    income_total = 0.0
    expense_total = 0.0

    for b in budgets:
        amt = float(b["amount"])
        if b["type"] == "income":
            income_total += amt
        else:
            expense_total += amt

    net_total = income_total - expense_total

    st.markdown("## Summary")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Income", f"${income_total:.2f}")
    with col2:
        st.metric("Expenses", f"${expense_total:.2f}")
    with col3:
        st.metric("Net Total", f"${net_total:.2f}")


# ---------------------------------------------------------
# Render a single section (Income, Bills, Budgets, Savings)
# ---------------------------------------------------------
def _render_section(title, section_type, budgets, year, month):
    st.markdown(f"### {title}")

    section_rows = [b for b in budgets if b["type"] == section_type]

    for b in section_rows:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.text_input(
                "Category",
                value=b["category"],
                key=f"{section_type}_cat_{b['id']}",
                disabled=True,
            )
        with col2:
            new_amt = st.number_input(
                "Amount",
                value=float(b["amount"]),
                key=f"{section_type}_amt_{b['id']}",
                min_value=0.0,
                step=50.0,
            )

        if st.button("Save", key=f"{section_type}_save_{b['id']}"):
            upsert_budget(
                b["category"],
                year,
                month,
                new_amt,
                section_type,
            )
            safe_rerun()

    st.markdown("---")

    st.markdown(f"#### Add new {title.lower()} category")

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
            return

        upsert_budget(new_cat, year, month, new_amt, section_type)
        safe_rerun()


# ---------------------------------------------------------
# Main Page
# ---------------------------------------------------------
def show_budget_planner():
    st.title("Budget Planner")

    today = datetime.date.today()
    year = st.number_input("Year", value=today.year, step=1)
    month = st.number_input("Month", value=today.month, min_value=1, max_value=12)

    budgets = get_budgets_for_month(year, month)

    render_budget_summary(budgets)

    st.markdown("---")

    _render_section("Income", "income", budgets, int(year), int(month))
    _render_section("Bills", "bill", budgets, int(year), int(month))
    _render_section("Budgets", "budget", budgets, int(year), int(month))
    _render_section("Savings", "savings", budgets, int(year), int(month))
