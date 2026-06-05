"""
Défi — Détection de fraude financière.

Vous devez implémenter la fonction `detect_fraud`.
La fonction `load_transactions` vous est FOURNIE (ne la modifiez pas).
"""

import csv


def load_transactions(path):
    """Lit un fichier CSV de transactions et renvoie une liste de dicts."""
    transactions = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            transactions.append(_clean_row(row))
    return transactions


def _clean_row(row):
    def get(key):
        v = row.get(key)
        return v.strip() if isinstance(v, str) and v.strip() != "" else None

    amount_raw = get("amount")
    try:
        amount = float(amount_raw) if amount_raw is not None else None
    except ValueError:
        amount = None

    card_raw = get("card_present")
    if card_raw is None:
        card_present = None
    else:
        card_present = card_raw.lower() in ("true", "1", "yes", "oui")

    return {
        "transaction_id": get("transaction_id"),
        "timestamp": get("timestamp"),
        "user_id": get("user_id"),
        "amount": amount,
        "currency": get("currency"),
        "merchant": get("merchant"),
        "country": get("country"),
        "card_present": card_present,
    }


def detect_fraud(transactions):
    """Analyse une liste de transactions et renvoie un verdict pour chacune.

    Retour : list[dict] avec transaction_id, fraud_score (0-1),
    is_suspicious (bool), reason (str) — un résultat par transaction, même ordre.
    """
    results = []
    # keep simple per-user history (amounts) based on earlier transactions in list
    history = {}

    for tx in transactions:
        tid = tx.get("transaction_id")
        user = tx.get("user_id")
        amount = tx.get("amount")

        fraud_score = 0.0
        is_suspicious = False
        reason = "ok"

        # handle missing or malformed amount
        if amount is None:
            reason = "missing amount"
            fraud_score = 0.0
            is_suspicious = False
        else:
            try:
                a = float(amount)
            except Exception:
                a = None

            if a is None:
                reason = "invalid amount"
                fraud_score = 0.0
                is_suspicious = False
            else:
                # Obvious anomalies
                if a <= 0:
                    is_suspicious = True
                    fraud_score = 1.0
                    reason = "non-positive amount"
                else:
                    # compute user historical average if available
                    prev = history.get(user, [])
                    avg = None
                    if prev:
                        avg = sum(prev) / len(prev)

                    if avg is not None and avg > 0:
                        factor = a / avg
                        # mark suspicious only for very large deviations
                        if factor >= 10:
                            is_suspicious = True
                        # score scaled relative to 10x the avg
                        fraud_score = min(1.0, a / (avg * 10))
                        reason = f"amount {a} vs avg {avg:.2f}"
                    else:
                        # no history: flag very large amounts
                        if a >= 1000:
                            is_suspicious = True
                            fraud_score = min(1.0, a / 10000)
                            reason = "very large amount with no history"
                        else:
                            fraud_score = 0.0
                            reason = "ok"

                # add positive amounts to history for future checks
                if a is not None and a > 0:
                    history.setdefault(user, []).append(a)

        results.append({
            "transaction_id": tid,
            "fraud_score": float(fraud_score),
            "is_suspicious": bool(is_suspicious),
            "reason": str(reason),
        })

    return results
