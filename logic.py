from db import (
    get_transactions,
    get_splits_for_transaction
)

def get_transactions_with_splits():
    txs = get_transactions()
    result = []

    for tx in txs:
        splits = get_splits_for_transaction(tx["id"])
        tx["splits"] = splits
        result.append(tx)

    return result

def compute_category_totals(transactions):
    totals = {}

    for tx in transactions:
        if tx["splits"]:
            for s in tx["splits"]:
                cat = s["category"]
                totals[cat] = totals.get(cat, 0) + s["amount"]
        else:
            cat = tx["category"]
            totals[cat] = totals.get(cat, 0) + tx["amount"]

    return totals
