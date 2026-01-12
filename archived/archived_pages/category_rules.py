import streamlit as st
from utils.navigation import safe_rerun
from db import get_category_rules, add_category_rule, delete_category_rule


def show_category_rules():
    st.header("Category Rules")

    rules = get_category_rules()

    st.subheader("Existing Rules")
    for r in rules:
        col1, col2, col3 = st.columns([4, 3, 1])
        col1.write(f"Match: **{r['match_text']}**")
        col2.write(f"Category: **{r['category']}** (priority {r['priority']})")
        if col3.button("Delete", key=f"del_{r['id']}"):
            delete_category_rule(r["id"])
            safe_rerun()  # rerun required after delete

    st.markdown("---")

    st.subheader("Add New Rule")
    match_text = st.text_input("Match Text")
    category = st.text_input("Category")
    priority = st.number_input("Priority", min_value=1, value=1)

    if st.button("Add Rule"):
        add_category_rule(match_text, category, priority)
        st.success("Rule added!")
        safe_rerun()  # rerun required after add
