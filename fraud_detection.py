"""
Défi — Détection de fraude financière.

Vous devez implémenter la fonction `detect_fraud`.
La fonction `load_transactions` vous est FOURNIE (ne la modifiez pas).
"""

import csv
from collections import defaultdict
from datetime import datetime, timezone


REQUIRED_FIELDS = ("transaction_id", "user_id", "amount", "country")
AMOUNT_RATIO_THRESHOLD = 10.0
GEO_WINDOW_HOURS = 3.0
FREQ_WINDOW_MINUTES = 60
FREQ_COUNT_THRESHOLD = 5

REASON_OK = "Transaction conforme au profil du client"
REASON_NEGATIVE_AMOUNT = "Montant nul ou négatif"
REASON_HIGH_AMOUNT = "Montant très supérieur à l'habitude du client"
REASON_GEO = "Deux pays différents en trop peu de temps"
REASON_FREQUENCY = "Fréquence de transactions anormalement élevée"
REASON_DUPLICATE = "Transaction en double détectée"


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


def _parse_timestamp(ts):
    if not isinstance(ts, str) or not ts.strip():
        return None
    value = ts.strip()
    try:
        if value.endswith("Z"):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed
    except ValueError:
        return None


def _missing_fields(tx):
    return [field for field in REQUIRED_FIELDS if tx.get(field) is None]


def _find_geo_conflicts(transactions):
    """Repère les transactions impliquées dans un déplacement géographique impossible."""
    flagged = {}
    by_user = defaultdict(list)

    for tx in transactions:
        user = tx.get("user_id")
        if user:
            by_user[user].append(tx)

    for txs in by_user.values():
        indexed = []
        for tx in txs:
            ts = _parse_timestamp(tx.get("timestamp"))
            country = tx.get("country")
            tid = tx.get("transaction_id")
            if ts and country and tid:
                indexed.append((ts, country, tid))

        indexed.sort(key=lambda item: item[0])
        for i in range(len(indexed)):
            for j in range(i + 1, len(indexed)):
                ts1, country1, tid1 = indexed[i]
                ts2, country2, tid2 = indexed[j]
                if country1 == country2:
                    continue
                hours = abs((ts2 - ts1).total_seconds()) / 3600
                if hours <= GEO_WINDOW_HOURS:
                    for tid in (tid1, tid2):
                        flagged[tid] = (REASON_GEO, 0.88)
                elif hours > GEO_WINDOW_HOURS:
                    break

    return flagged


def _high_amount_vs_history(amount, history_amounts):
    if not history_amounts or amount is None or amount <= 0:
        return False, 0.0

    avg = sum(history_amounts) / len(history_amounts)
    if avg <= 0:
        return False, 0.0

    ratio = amount / avg
    if ratio < AMOUNT_RATIO_THRESHOLD:
        return False, 0.0

    score = min(0.95, 0.7 + min(ratio / 100, 0.2))
    return True, max(score, 0.9)


def _frequency_issue(tx, user_history):
    ts = _parse_timestamp(tx.get("timestamp"))
    if ts is None:
        return False, 0.0

    recent = 1
    for prev in user_history:
        prev_ts = _parse_timestamp(prev.get("timestamp"))
        if prev_ts is None:
            continue
        minutes = abs((ts - prev_ts).total_seconds()) / 60
        if minutes <= FREQ_WINDOW_MINUTES:
            recent += 1

    if recent >= FREQ_COUNT_THRESHOLD:
        return True, 0.82
    return False, 0.0


def detect_fraud(transactions):
    """Analyse une liste de transactions et renvoie un verdict pour chacune.

    Retour : list[dict] avec transaction_id, fraud_score (0-1),
    is_suspicious (bool), reason (str) — un résultat par transaction, même ordre.
    """
    geo_flags = _find_geo_conflicts(transactions)
    seen_ids = set()
    user_amount_history = defaultdict(list)
    user_tx_history = defaultdict(list)

    results = []
    for tx in transactions:
        tid = tx.get("transaction_id")
        amount = tx.get("amount")
        user = tx.get("user_id")

        fraud_score = 0.0
        is_suspicious = False
        reason = REASON_OK

        missing = _missing_fields(tx)
        if missing:
            is_suspicious = True
            fraud_score = 0.85
            reason = f"Champs obligatoires manquants: {', '.join(missing)}"
        elif tid is not None and tid in seen_ids:
            is_suspicious = True
            fraud_score = 0.8
            reason = REASON_DUPLICATE
        elif amount is not None and amount <= 0:
            is_suspicious = True
            fraud_score = 0.9
            reason = REASON_NEGATIVE_AMOUNT
        elif tid in geo_flags:
            is_suspicious = True
            reason, fraud_score = geo_flags[tid]
        else:
            hist_amounts = user_amount_history.get(user, [])
            high_amount, amount_score = _high_amount_vs_history(amount, hist_amounts)
            if high_amount:
                is_suspicious = True
                fraud_score = amount_score
                reason = REASON_HIGH_AMOUNT
            else:
                freq_issue, freq_score = _frequency_issue(tx, user_tx_history.get(user, []))
                if freq_issue:
                    is_suspicious = True
                    fraud_score = freq_score
                    reason = REASON_FREQUENCY

        if tid is not None:
            seen_ids.add(tid)
        if user is not None:
            user_tx_history[user].append(tx)
            if amount is not None and amount > 0:
                user_amount_history[user].append(amount)

        results.append({
            "transaction_id": tid,
            "fraud_score": float(fraud_score),
            "is_suspicious": bool(is_suspicious),
            "reason": str(reason),
        })

    return results
