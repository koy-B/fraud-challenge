"""
Couche IA complémentaire — utilisée par l'interface uniquement.
Ne modifie pas le contrat de detect_fraud (tests CI inchangés).
"""

from __future__ import annotations

from datetime import datetime

import numpy as np

try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import MinMaxScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


def _parse_hour(ts) -> float:
    if not isinstance(ts, str) or not ts.strip():
        return 12.0
    value = ts.strip()
    try:
        if value.endswith("Z"):
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        else:
            dt = datetime.fromisoformat(value)
        return float(dt.hour)
    except ValueError:
        return 12.0


def _build_feature_matrix(transactions: list[dict]) -> np.ndarray:
    user_counts: dict[str, int] = {}
    rows = []

    for tx in transactions:
        user = tx.get("user_id") or "unknown"
        user_counts[user] = user_counts.get(user, 0) + 1

        amount = tx.get("amount")
        amount_val = float(amount) if isinstance(amount, (int, float)) else 0.0
        log_amount = float(np.log1p(max(amount_val, 0.0)))

        card = tx.get("card_present")
        card_val = 1.0 if card is True else 0.0 if card is False else 0.5

        country = tx.get("country") or "XX"
        country_val = (hash(country) % 97) / 97.0

        hour = _parse_hour(tx.get("timestamp")) / 23.0
        user_freq = min(user_counts[user], 10) / 10.0

        rows.append([
            amount_val,
            log_amount,
            hour,
            card_val,
            country_val,
            user_freq,
        ])

    return np.array(rows, dtype=float)


def _normalize_scores(raw: np.ndarray) -> np.ndarray:
    if len(raw) == 0:
        return raw
    if len(raw) == 1:
        return np.array([0.5])
    scaler = MinMaxScaler()
    return scaler.fit_transform(raw.reshape(-1, 1)).ravel()


def compute_ai_scores(transactions: list[dict]) -> list[float]:
    """Retourne un score IA (0-1) par transaction."""
    if not transactions:
        return []

    features = _build_feature_matrix(transactions)
    if not SKLEARN_AVAILABLE or len(transactions) < 3:
        return [0.0] * len(transactions)

    contamination = min(0.35, max(0.08, 2 / len(transactions)))
    model = IsolationForest(
        n_estimators=120,
        contamination=contamination,
        random_state=42,
    )
    model.fit(features)
    decision = -model.decision_function(features)
    normalized = _normalize_scores(decision)
    return [float(min(1.0, max(0.0, s))) for s in normalized]


def enhance_with_ai(
    transactions: list[dict],
    rule_results: list[dict],
    ai_weight: float = 0.4,
) -> list[dict]:
    """Fusionne les scores règles + IA pour l'interface."""
    ai_scores = compute_ai_scores(transactions)
    enhanced = []

    for tx, rule, ai_score in zip(transactions, rule_results, ai_scores):
        rule_score = float(rule.get("fraud_score", 0.0))
        combined = min(1.0, (1 - ai_weight) * rule_score + ai_weight * ai_score)

        is_suspicious = bool(rule.get("is_suspicious", False))
        reason = str(rule.get("reason", ""))

        if ai_score >= 0.7 and not is_suspicious and combined >= 0.45:
            is_suspicious = True
            reason = f"IA : anomalie comportementale détectée — {reason}"
        elif ai_score >= 0.65 and is_suspicious:
            reason = f"{reason} · Confirmé par IA ({ai_score:.0%})"
        elif ai_score >= 0.8:
            combined = min(1.0, combined + 0.05)

        if is_suspicious and combined < 0.55:
            combined = max(combined, 0.55)

        enhanced.append({
            "transaction_id": rule.get("transaction_id"),
            "fraud_score": round(combined, 4),
            "is_suspicious": is_suspicious,
            "reason": reason,
            "rule_score": round(rule_score, 4),
            "ai_score": round(ai_score, 4),
            "ai_boosted": ai_score >= 0.65,
        })

    return enhanced
