"""
db.py

Modernized, safe, Phase‑5.2 database layer.
"""

import datetime
from typing import List, Dict, Optional, Any
import streamlit as st
from supabase import create_client

import streamlit as st
st.write("DEBUG URL:", st.secrets.get("SUPABASE_URL"))
st.write("DEBUG KEY EXISTS:", "SUPABASE_KEY" in st.secrets)

# ============================================================
# SUPABASE CLIENT (correct location)
# ============================================================

def get_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]

    # Runtime check (safe)
    if not url or not key:
        st.error("Supabase secrets not loaded.")

    return create_client(url, key)

supabase = get_supabase()

# ============================================================
# INTERNAL SAFE EXEC WRAPPER
# ============================================================

def _exec(query) -> Dict[str, Any]:
    """
    Execute a Supabase query safely.
    Always returns:
        { "success": bool, "data": list|dict|None, "error": str|None }
    Prevents `.data` crashes and gives clear errors.
    """
    try:
        res = query.execute()
    except Exception as e:
        return {"success": False, "data": None, "error": str(e)}

    if res is None:
        return {"success": False, "data": None, "error": "Supabase returned None"}

    data = getattr(res, "data", None)
    error = getattr(res, "error", None)

    # Some versions return dict-like responses
    if data is None and isinstance(res, dict):
        data = res.get("data")
        error = res.get("error")

    return {"success": error is None, "data": data, "error": error}


# ============================================================
# ACCOUNTS
# ============================================================

def get_accounts() -> List[Dict]:
    q = supabase.table("accounts").select("*").order("name")
    r = _exec(q)
    return r["data"] or []


def get_account_balance(account_id: str) -> float:
    """
    Sum all non-deleted, non-parent transactions for an account.
    Prevents double-counting split parents.
    """
    q = (
        supabase.table("transactions")
        .select("amount")
        .eq("account_id", account_id)
        .eq("deleted", False)
        .eq("is_split_parent", False)
    )
    r = _exec(q)
    rows = r["data"] or []
    return float(sum(float(t["amount"]) for t in rows))


# ============================================================
# TRANSACTIONS — CRUD
# ============================================================

def get_all_transactions() -> List[Dict]:
    """
    Return all non-deleted transactions (parents + children),
    joined with account name.
    """
    q = (
        supabase.table("transactions")
        .select("*, accounts(name)")
        .eq("deleted", False)
        .order("date", desc=True)
    )
    r = _exec(q)
    return r["data"] or []


def get_transaction(transaction_id: str) -> Optional[Dict]:
    q = (
        supabase.table("transactions")
        .select("*, accounts(name)")
        .eq("id", transaction_id)
        .single()
    )
    r = _exec(q)
    return r["data"]


def insert_transaction(data: Dict):
    q = supabase.table("transactions").insert(data)
    r = _exec(q)
    if not r["success"]:
        raise RuntimeError(f"Insert transaction failed: {r['error']}")
    return r["data"]


def update_transaction(transaction_id: str, data: Dict):
    q = supabase.table("transactions").update(data).eq("id", transaction_id)
    r = _exec(q)
    if not r["success"]:
        raise RuntimeError(f"Update transaction failed: {r['error']}")
    return r["data"]


def delete_transaction(transaction_id: str):
    q = (
        supabase.table("transactions")
        .update({"deleted": True})
        .eq("id", transaction_id)
    )
    r = _exec(q)
    if not r["success"]:
        raise RuntimeError(f"Delete transaction failed: {r['error']}")
    return r["data"]


# ============================================================
# SPLIT TRANSACTIONS
# ============================================================

def get_child_transactions(parent_id: str) -> List[Dict]:
    q = (
        supabase.table("transactions")
        .select("*")
        .eq("parent_id", parent_id)
        .eq("deleted", False)
        .order("date")
    )
    r = _exec(q)
    return r["data"] or []


def clear_children(parent_id: str):
    q = (
        supabase.table("transactions")
        .update({"deleted": True})
        .eq("parent_id", parent_id)
    )
    r = _exec(q)
    if not r["success"]:
        raise RuntimeError(f"Clear children failed: {r['error']}")
    return r["data"]


def create_split_children(
    parent_id: str,
    date: str,
    account_id: str,
    description: str,
    notes: str,
    splits: List[Dict],
):
    rows = []
    for s in splits:
        rows.append(
            {
                "date": date,
                "amount": s["amount"],
                "description": description,
                "category": s["category"],
                "account_id": account_id,
                "notes": notes,
                "is_split_parent": False,
                "parent_id": parent_id,
            }
        )

    if not rows:
        return None

    q = supabase.table("transactions").insert(rows)
    r = _exec(q)
    if not r["success"]:
        raise RuntimeError(f"Create split children failed: {r['error']}")
    return r["data"]


def delete_transaction_family(parent_id: str):
    # delete children
    q1 = (
        supabase.table("transactions")
        .update({"deleted": True})
        .eq("parent_id", parent_id)
    )
    r1 = _exec(q1)
    if not r1["success"]:
        raise RuntimeError(f"Delete children failed: {r1['error']}")

    # delete parent
    q2 = (
        supabase.table("transactions")
        .update({"deleted": True})
        .eq("id", parent_id)
    )
    r2 = _exec(q2)
    if not r2["success"]:
        raise RuntimeError(f"Delete parent failed: {r2['error']}")

    return r2["data"]


# ============================================================
# MONTHLY TRANSACTIONS (Dashboard)
# ============================================================

def get_transactions_for_month(year: int, month: int) -> List[Dict]:
    """
    Returns all non-deleted, non-parent transactions for the month.
    Children count; parents do not.
    """
    start = datetime.date(year, month, 1)
    end = datetime.date(year + (month == 12), (month % 12) + 1, 1)

    q = (
        supabase.table("transactions")
        .select("*, accounts(name)")
        .eq("deleted", False)
        .eq("is_split_parent", False)
        .gte("date", start.isoformat())
        .lt("date", end.isoformat())
        .order("date")
    )
    r = _exec(q)
    return r["data"] or []


def get_monthly_actuals_by_category(year: int, month: int) -> Dict[str, float]:
    txs = get_transactions_for_month(year, month)
    totals = {}
    for t in txs:
        cat = t.get("category") or "Uncategorized"
        amt = float(t["amount"])
        totals[cat] = totals.get(cat, 0.0) + amt
    return totals


# ============================================================
# BUDGETS
# ============================================================

def get_budgets_for_month(year: int, month: int) -> List[Dict]:
    month_date = datetime.date(year, month, 1)
    q = (
        supabase.table("budgets")
        .select("*")
        .eq("month", month_date.isoformat())
        .order("category")
    )
    r = _exec(q)
    return r["data"] or []


def upsert_budget(category: str, year: int, month: int, amount: float, btype: str):
    """
    Insert or update a budget row for a given category + month.
    budgets.month is a DATE column.
    """
    month_date = datetime.date(year, month, 1)

    row = {
        "category": category,
        "year": year,
        "month": month_date.isoformat(),
        "amount": amount,
        "type": btype,
    }

    q = supabase.table("budgets").upsert(row, on_conflict="category,month")
    r = _exec(q)

    if not r["success"]:
        raise RuntimeError(f"Budget upsert failed: {r['error']}")

    return r["data"]


def get_monthly_budget_totals_by_category(year: int, month: int) -> Dict[str, float]:
    budgets = get_budgets_for_month(year, month)
    totals = {}
    for b in budgets:
        cat = b["category"]
        amt = float(b["amount"])
        totals[cat] = totals.get(cat, 0.0) + amt
    return totals
