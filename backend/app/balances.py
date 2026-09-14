"""Balance logic: net balances + minimized transactions.

Port of frontend/src/services/balance.js — positive net means owed money.
"""


def compute_balances(expenses: list[dict]) -> dict:
    net: dict[str, float] = {}
    for e in expenses:
        net[e["payer_id"]] = net.get(e["payer_id"], 0.0) + float(e["amount"])
        for s in e.get("splits") or []:
            net[s["user_id"]] = net.get(s["user_id"], 0.0) - float(s["share_amount"])

    creditors: list[dict] = []
    debtors: list[dict] = []
    for user_id, amount in net.items():
        v = round(float(amount), 2)
        if v > 0.009:
            creditors.append({"user_id": user_id, "amount": v})
        elif v < -0.009:
            debtors.append({"user_id": user_id, "amount": -v})

    creditors.sort(key=lambda c: c["amount"], reverse=True)
    debtors.sort(key=lambda d: d["amount"], reverse=True)

    transactions: list[dict] = []
    i = j = 0
    while i < len(debtors) and j < len(creditors):
        d, c = debtors[i], creditors[j]
        amt = round(min(d["amount"], c["amount"]), 2)
        transactions.append({"from_user_id": d["user_id"], "to_user_id": c["user_id"], "amount": amt})
        d["amount"] = round(d["amount"] - amt, 2)
        c["amount"] = round(c["amount"] - amt, 2)
        if d["amount"] < 0.01:
            i += 1
        if c["amount"] < 0.01:
            j += 1

    return {"net": {k: round(float(v), 2) for k, v in net.items()}, "transactions": transactions}
