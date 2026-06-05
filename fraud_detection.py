"""
Défi — Détection de fraude financière.

Vous devez implémenter la fonction `detect_fraud`.
La fonction `load_transactions` vous est FOURNIE (ne la modifiez pas).
"""

import csv


REQUIRED_FIELDS = ("transaction_id", "user_id", "amount", "country")
REASON_OK = "Transaction conforme au profil du client"
REASON_NEGATIVE_AMOUNT = "Montant nul ou négatif"


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


def _missing_fields(tx):
    return [field for field in REQUIRED_FIELDS if tx.get(field) is None]


def detect_fraud(transactions):
    """Analyse une liste de transactions et renvoie un verdict pour chacune.

    Retour : list[dict] avec transaction_id, fraud_score (0-1),
    is_suspicious (bool), reason (str) — un résultat par transaction, même ordre.
    """
    results = []
    for tx in transactions:
        tid = tx.get("transaction_id")
        amount = tx.get("amount")

        fraud_score = 0.0
        is_suspicious = False
        reason = REASON_OK

        missing = _missing_fields(tx)
        if missing:
            is_suspicious = True
            fraud_score = 0.85
            reason = f"Champs obligatoires manquants: {', '.join(missing)}"
        elif amount is not None and amount <= 0:
            is_suspicious = True
            fraud_score = 0.9
            reason = REASON_NEGATIVE_AMOUNT

        results.append({
            "transaction_id": tid,
            "fraud_score": float(fraud_score),
            "is_suspicious": bool(is_suspicious),
            "reason": str(reason),
        })

    return results
