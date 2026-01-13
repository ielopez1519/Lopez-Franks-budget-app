import streamlit as st
from typing import Dict, List, Optional
from supabase import create_client, Client

# Initialize Supabase client
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# -----------------------------
# Internal execution wrapper
# -----------------------------
def _exec(query):
    try:
        resp = query.execute()
        return {"success": True, "data": resp.data}
    except Exception as e:
        return {"success": False, "error": str(e)}


# -----------------------------
# Accounts
# -----------------------------
def get_accounts() -> List[Dict]:
    q = supabase.table("accounts").select("*").order("name")
    r = _exec(q)
    return r["data"] if r["success"] else []


# -----------------------------
# Transactions
# -----------------------------
def get_all_transactions() -> List[Dict]:
    q = supabase.table("transactions").select(
        "id, date, amount, description, category, type, "
        "account_id, notes, deleted, is_split_parent, parent_id"
    )
    r = _exec(q)
    return r["data"] if r["success"] else []


def get_transaction_by_id(transaction_id: str) -> Optional[Dict]:
    q = (
        supabase.table("transactions")
        .select(
            "id, date, amount, description, category, type, "
            "account_id, notes, deleted, is_split_parent, parent_id"
        )
        .eq("id", transaction_id)
        .single()
    )
    r = _exec(q)
    return r["data"] if r["success"] else None


def insert_transaction(data: Dict):
    # Normalize category
    if data.get("category"):
        data["category"] = data["category"].strip().lower()

    q = supabase.table("transactions").insert(data).select("*")
    r = _exec(q)

    if not r["success"]:
        raise RuntimeError(f"Insert transaction failed: {r['error']}")

    return r["data"]


def update_transaction(transaction_id: str, data: Dict):
    # Normalize category
    if data.get("category"):
        data["category"] = data["category"].strip().lower()

    q = (
        supabase.table("transactions")
        .update(data)
        .eq("id", transaction_id)
        .select("*")
    )
    r = _exec(q)

    if not r["success"]:
        raise RuntimeError(f"Update transaction failed: {r['error']}")

    return r["data"]


def delete_transaction(transaction_id: str):
    q = (
        supabase.table("transactions")
        .update({"deleted": True})
        .eq("id", transaction_id)
        .select("*")
    )
    r = _exec(q)

    if not r["success"]:
        raise RuntimeError(f"Delete transaction failed: {r['error']}")

    return r["data"]


# -----------------------------
# Monthly Queries
# -----------------------------
def get_transactions_for_month(year: int, month: int) -> List[Dict]:
    start = f"{year}-{month:02d}-01"
    end_month = month + 1 if month < 12 else 1
    end_year = year if month < 12 else year + 1
    end = f"{end_year}-{end_month:02d}-01"

    q = (
        supabase.table("transactions")
        .select(
            "id, date, amount, description, category, type, "
            "account_id, notes, deleted, is_split_parent, parent_id"
        )
        .gte("date", start)
        .lt("date", end)
        .eq("deleted", False)
    )
    r = _exec(q)
    return r["data"] if r["success"] else []


def get_monthly_budget_totals_by_category(year: int, month: int) -> Dict[str, float]:
    q = (
        supabase.table("budgets")
        .select("category, amount")
        .eq("year", year)
        .eq("month", month)
    )
    r = _exec(q)

    if not r["success"]:
        return {}

    totals = {}
    for row in r["data"]:
        cat = (row["category"] or "").lower()
        totals[cat] = totals.get(cat, 0.0) + float(row["amount"])

    return totals
