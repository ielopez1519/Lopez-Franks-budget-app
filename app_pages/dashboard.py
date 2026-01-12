import streamlit as st
import datetime
import pandas as pd
from db import (
    get_transactions_for_month,
    get_monthly_budget_totals_by_category,
)


def show_dashboard():
    st.header("Dashboard")

    today = datetime.date.today()
    year = st.number_input("Year", value=today.year, step=1)
    month = st.number_input("Month", value=today.month, min_value=1, max_value=12)

    year = int(year)
    month = int(month)

    txs = get_transactions_for_month(year, month)
    budgets = get_monthly_budget_totals_by_category(year, month)

    if not txs and not budgets:
        st.info("No data for this month yet.")
        return

    # Actuals by category
    actuals = {}
    income_total = 0.0
    expense_total = 0.0

    for t in txs:
        cat = t.get("category")
        if not cat:
            continue
        amt = float(t["amount"])
        actuals[cat] = actuals.get(cat, 0.0) + amt
        if amt > 0:
            income_total += amt
        else:
            expense_total += amt

    net = income_total + expense_total

    st.subheader("Overview")
    col1, col2, col3 = st.columns(3)
    col1.metric("Income", f"${income_total:,.2f}")
    col2.metric("Spending", f"${abs(expense_total):,.2f}")
    col3.metric("Net", f"${net:,.2f}")

    # Budget vs actual by category
    st.markdown("---")
    st.subheader("Budget vs actual by category")

    categories = sorted(
        c for c in set(list(actuals.keys()) + list(budgets.keys())) if c
    )

    rows = []
    for cat in categories:
        b = budgets.get(cat, 0.0)
        a = actuals.get(cat, 0.0)
        diff = a - b
        rows.append(
            {
                "Category": cat,
                "Budgeted": b,
                "Actual": a,
                "Difference": diff,
            }
        )

    if rows:
        df = pd.DataFrame(rows)
        df_display = df.copy()
        df_display["Budgeted"] = df_display["Budgeted"].map(lambda x: f"${x:,.2f}")
        df_display["Actual"] = df_display["Actual"].map(lambda x: f"${x:,.2f}")
        df_display["Difference"] = df_display["Difference"].map(
            lambda x: f"${x:,.2f}"
        )
        st.dataframe(df_display, use_container_width=True)

        st.markdown("**Spending by category (actuals only)**")
        actual_only = {
            cat: val for cat, val in actuals.items() if val < 0 and cat in categories
        }
        if actual_only:
            chart_df = pd.DataFrame(
                {
                    "Category": list(actual_only.keys()),
                    "Spending": [abs(v) for v in actual_only.values()],
                }
            )
            chart_df = chart_df.set_index("Category")
            st.bar_chart(chart_df)
