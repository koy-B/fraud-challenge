"""
Interface Streamlit — Hackathon INTELO2026
Détection de fraude : règles métier + IA + planisphère mondial.
"""

from pathlib import Path

import streamlit as st

from ai_detection import SKLEARN_AVAILABLE, enhance_with_ai
from fraud_detection import detect_fraud, load_transactions
from globe_view import render_globe

SAMPLE_CSV = Path(__file__).parent / "data" / "sample_transactions.csv"

RISK_LABELS = [
    (0.0, 0.35, "Faible", "#22c55e"),
    (0.35, 0.65, "Modéré", "#f59e0b"),
    (0.65, 1.01, "Élevé", "#ef4444"),
]


def _inject_styles() -> None:
    st.markdown("""
    <style>
      @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,600;0,9..40,700;1,9..40,400&family=JetBrains+Mono:wght@400;600&display=swap');

      .stApp {
        background: linear-gradient(165deg, #060a12 0%, #0c1424 40%, #0a1628 100%);
        color: #e2e8f0;
        font-family: 'DM Sans', system-ui, sans-serif;
      }

      [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a101c 0%, #0f172a 100%);
        border-right: 1px solid rgba(6, 182, 212, 0.15);
      }

      [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #f1f5f9 !important;
        font-weight: 700;
      }

      .hero-block {
        background: linear-gradient(135deg, rgba(6,182,212,0.12) 0%, rgba(99,102,241,0.08) 50%, transparent 100%);
        border: 1px solid rgba(6, 182, 212, 0.2);
        border-radius: 20px;
        padding: 28px 32px;
        margin-bottom: 24px;
        position: relative;
        overflow: hidden;
      }
      .hero-block::before {
        content: '';
        position: absolute;
        top: -50%; right: -20%;
        width: 300px; height: 300px;
        background: radial-gradient(circle, rgba(6,182,212,0.15) 0%, transparent 70%);
        pointer-events: none;
      }
      .hero-title {
        font-size: 2rem;
        font-weight: 700;
        color: #f8fafc;
        margin: 0 0 8px 0;
        letter-spacing: -0.02em;
      }
      .hero-sub {
        color: #94a3b8;
        font-size: 1rem;
        margin: 0;
        max-width: 640px;
        line-height: 1.6;
      }
      .badge-ai {
        display: inline-block;
        background: linear-gradient(90deg, #06b6d4, #6366f1);
        color: white;
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        padding: 4px 10px;
        border-radius: 20px;
        margin-bottom: 12px;
      }

      .kpi-card {
        background: rgba(15, 23, 42, 0.7);
        border: 1px solid rgba(148, 163, 184, 0.12);
        border-radius: 14px;
        padding: 18px 20px;
        backdrop-filter: blur(8px);
      }
      .kpi-label {
        font-size: 0.75rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 6px;
      }
      .kpi-value {
        font-size: 1.75rem;
        font-weight: 700;
        color: #f1f5f9;
        font-family: 'JetBrains Mono', monospace;
      }
      .kpi-value.danger { color: #f87171; }
      .kpi-value.safe { color: #4ade80; }
      .kpi-value.accent { color: #22d3ee; }

      .alert-card {
        background: rgba(15, 23, 42, 0.85);
        border-radius: 12px;
        padding: 16px 18px;
        margin-bottom: 12px;
        border-left: 4px solid;
        transition: transform 0.15s ease;
      }
      .alert-card:hover { transform: translateX(4px); }

      .section-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #e2e8f0;
        margin: 24px 0 12px 0;
        display: flex;
        align-items: center;
        gap: 8px;
      }

      div[data-testid="stMetric"] {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(148, 163, 184, 0.1);
        border-radius: 12px;
        padding: 12px 16px;
      }

      .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: transparent;
      }
      .stTabs [data-baseweb="tab"] {
        background: rgba(15, 23, 42, 0.5);
        border-radius: 10px;
        color: #94a3b8;
        border: 1px solid transparent;
      }
      .stTabs [aria-selected="true"] {
        background: rgba(6, 182, 212, 0.15) !important;
        color: #22d3ee !important;
        border-color: rgba(6, 182, 212, 0.3) !important;
      }

      .stButton > button[kind="primary"] {
        background: linear-gradient(90deg, #0891b2, #4f46e5);
        border: none;
        font-weight: 700;
        letter-spacing: 0.03em;
        border-radius: 12px;
        padding: 12px 24px;
        box-shadow: 0 4px 20px rgba(6, 182, 212, 0.3);
      }
      .stButton > button[kind="primary"]:hover {
        box-shadow: 0 6px 28px rgba(6, 182, 212, 0.45);
      }

      .filter-panel {
        background: rgba(8, 16, 32, 0.85);
        border: 1px solid rgba(56, 189, 248, 0.15);
        border-radius: 14px;
        padding: 16px 18px 6px 18px;
        margin-bottom: 16px;
      }
      .tx-count {
        display: inline-block;
        background: rgba(6, 182, 212, 0.15);
        color: #67e8f9;
        font-size: 0.78rem;
        font-weight: 600;
        padding: 4px 12px;
        border-radius: 20px;
        border: 1px solid rgba(6, 182, 212, 0.25);
        margin-bottom: 14px;
      }
      .tx-list {
        border: 1px solid rgba(148, 163, 184, 0.1);
        border-radius: 10px;
        overflow: hidden;
        font-size: 0.78rem;
      }
      .tx-head, .tx-row {
        display: grid;
        grid-template-columns: 8px 90px 1.2fr 56px 40px 88px 52px 1.4fr;
        gap: 8px;
        align-items: center;
        padding: 7px 12px;
      }
      .tx-head {
        background: rgba(8, 16, 32, 0.9);
        color: #64748b;
        font-size: 0.65rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        border-bottom: 1px solid rgba(148, 163, 184, 0.12);
      }
      .tx-row {
        border-bottom: 1px solid rgba(148, 163, 184, 0.06);
        transition: background 0.12s;
      }
      .tx-row:last-child { border-bottom: none; }
      .tx-row:hover { background: rgba(6, 182, 212, 0.06); }
      .tx-row.suspect { background: rgba(248, 113, 113, 0.04); }
      .tx-dot {
        width: 7px; height: 7px; border-radius: 50%;
      }
      .tx-dot.alert { background: #f87171; box-shadow: 0 0 6px #f87171; }
      .tx-dot.ok { background: #4ade80; }
      .tx-col-id {
        font-family: 'JetBrains Mono', monospace;
        font-weight: 600;
        color: #e2e8f0;
        font-size: 0.72rem;
      }
      .tx-col-merchant { color: #cbd5e1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
      .tx-col-user, .tx-col-country { color: #94a3b8; }
      .tx-col-amount {
        font-family: 'JetBrains Mono', monospace;
        font-weight: 600;
        color: #f1f5f9;
        text-align: right;
        font-size: 0.72rem;
      }
      .tx-col-score {
        font-weight: 700;
        text-align: center;
        font-size: 0.72rem;
      }
      .tx-col-reason {
        color: #64748b;
        font-size: 0.68rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
      @media (max-width: 900px) {
        .tx-head, .tx-row {
          grid-template-columns: 8px 80px 1fr 50px 72px 1fr;
        }
        .tx-head span:nth-child(5),
        .tx-head span:nth-child(8),
        .tx-row span:nth-child(5),
        .tx-row span:nth-child(8) { display: none; }
      }

      .inspector-wrap {
        background: linear-gradient(160deg, rgba(10, 20, 40, 0.95) 0%, rgba(6, 12, 28, 0.98) 100%);
        border: 1px solid rgba(56, 189, 248, 0.2);
        border-radius: 18px;
        padding: 24px 28px;
        margin-top: 8px;
      }
      .inspector-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        flex-wrap: wrap;
        gap: 12px;
        margin-bottom: 20px;
        padding-bottom: 16px;
        border-bottom: 1px solid rgba(148, 163, 184, 0.12);
      }
      .inspector-id {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.5rem;
        font-weight: 700;
        color: #f8fafc;
      }
      .inspector-status {
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        padding: 8px 16px;
        border-radius: 10px;
      }
      .inspector-status.alert {
        background: rgba(248, 113, 113, 0.15);
        color: #fca5a5;
        border: 1px solid rgba(248, 113, 113, 0.3);
      }
      .inspector-status.ok {
        background: rgba(74, 222, 128, 0.12);
        color: #86efac;
        border: 1px solid rgba(74, 222, 128, 0.25);
      }
      .info-chip {
        background: rgba(15, 23, 42, 0.8);
        border: 1px solid rgba(148, 163, 184, 0.1);
        border-radius: 10px;
        padding: 12px 14px;
        margin-bottom: 8px;
      }
      .info-chip-label {
        font-size: 0.68rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 4px;
      }
      .info-chip-value {
        font-size: 0.95rem;
        font-weight: 600;
        color: #e2e8f0;
      }
      .score-bar-wrap { margin-bottom: 14px; }
      .score-bar-label {
        display: flex;
        justify-content: space-between;
        font-size: 0.78rem;
        color: #94a3b8;
        margin-bottom: 5px;
      }
      .score-bar-track {
        height: 8px;
        background: rgba(30, 41, 59, 0.8);
        border-radius: 4px;
        overflow: hidden;
      }
      .score-bar-fill {
        height: 100%;
        border-radius: 4px;
        transition: width 0.4s ease;
      }
      .verdict-box {
        background: rgba(8, 16, 32, 0.6);
        border-radius: 12px;
        padding: 16px 18px;
        margin-top: 16px;
        border-left: 4px solid;
      }

      #MainMenu, footer, header { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)


def _risk_level(score: float) -> tuple[str, str]:
    for low, high, label, color in RISK_LABELS:
        if low <= score < high:
            return label, color
    return "Élevé", "#ef4444"


def _esc(text) -> str:
    if text is None:
        return "—"
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _score_bar(label: str, value: float, color: str) -> str:
    pct = min(100, max(0, int(value * 100)))
    return f"""
    <div class="score-bar-wrap">
      <div class="score-bar-label"><span>{label}</span><span>{pct}%</span></div>
      <div class="score-bar-track">
        <div class="score-bar-fill" style="width:{pct}%;background:{color};"></div>
      </div>
    </div>"""


def _tx_row_html(row) -> str:
    score = float(row.get("fraud_score", 0))
    _, color = _risk_level(score)
    suspicious = bool(row.get("is_suspicious", False))
    dot = "alert" if suspicious else "ok"
    row_cls = "suspect" if suspicious else ""
    reason = _esc(row.get("reason", ""))
    if len(reason) > 48:
        reason = reason[:45] + "…"

    return f"""
    <div class="tx-row {row_cls}">
      <span class="tx-dot {dot}"></span>
      <span class="tx-col-id">{_esc(row.get('transaction_id'))}</span>
      <span class="tx-col-merchant">{_esc(row.get('merchant', '—'))}</span>
      <span class="tx-col-user">{_esc(row.get('user_id'))}</span>
      <span class="tx-col-country">{_esc(row.get('country', '—'))}</span>
      <span class="tx-col-amount">{_esc(row.get('amount'))} {_esc(row.get('currency', ''))}</span>
      <span class="tx-col-score" style="color:{color}">{score:.0%}</span>
      <span class="tx-col-reason" title="{_esc(row.get('reason', ''))}">{reason}</span>
    </div>"""


def _render_tx_compact_list(view) -> None:
    rows = "".join(_tx_row_html(row) for _, row in view.iterrows())
    st.markdown(f"""
    <div class="tx-list">
      <div class="tx-head">
        <span></span><span>ID</span><span>Commerçant</span><span>Client</span>
        <span>Pays</span><span>Montant</span><span>Score</span><span>Raison</span>
      </div>
      {rows}
    </div>
    """, unsafe_allow_html=True)


def _render_inspector(row) -> None:
    score = float(row.get("fraud_score", 0))
    rule = float(row.get("rule_score", score))
    ai = float(row.get("ai_score", 0))
    label, color = _risk_level(score)
    suspicious = bool(row.get("is_suspicious", False))
    status_cls = "alert" if suspicious else "ok"
    status_txt = "Transaction suspecte" if suspicious else "Transaction conforme"
    verdict_color = "#f87171" if suspicious else "#4ade80"

    chips = [
        ("Client", row.get("user_id")),
        ("Montant", f"{row.get('amount')} {row.get('currency', '')}"),
        ("Commerçant", row.get("merchant")),
        ("Pays", row.get("country")),
        ("Date", str(row.get("timestamp", ""))[:19]),
        ("Carte présente", "Oui" if row.get("card_present") else "Non" if row.get("card_present") is False else "—"),
    ]

    chips_html = "".join(
        f'<div class="info-chip"><div class="info-chip-label">{_esc(lbl)}</div>'
        f'<div class="info-chip-value">{_esc(val)}</div></div>'
        for lbl, val in chips
    )

    scores_html = (
        _score_bar("Score règles métier", rule, "#38bdf8")
        + _score_bar("Score IA", ai, "#a78bfa")
        + _score_bar("Score final fusionné", score, color)
    )

    st.markdown(f"""
    <div class="inspector-wrap">
      <div class="inspector-header">
        <div>
          <div class="inspector-id">{_esc(row.get('transaction_id'))}</div>
          <div style="color:#64748b;font-size:0.85rem;margin-top:4px;">
            Niveau de risque : <strong style="color:{color}">{label}</strong>
          </div>
        </div>
        <div class="inspector-status {status_cls}">{status_txt}</div>
      </div>
      <div style="display:grid;grid-template-columns:1.2fr 1fr;gap:24px;">
        <div>
          <div style="color:#94a3b8;font-size:0.78rem;font-weight:600;text-transform:uppercase;
                      letter-spacing:0.06em;margin-bottom:10px;">Détails de la transaction</div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">{chips_html}</div>
        </div>
        <div>
          <div style="color:#94a3b8;font-size:0.78rem;font-weight:600;text-transform:uppercase;
                      letter-spacing:0.06em;margin-bottom:10px;">Analyse des scores</div>
          {scores_html}
        </div>
      </div>
      <div class="verdict-box" style="border-color:{verdict_color}">
        <div style="font-size:0.72rem;color:#64748b;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;">
          Verdict &amp; justification
        </div>
        <div style="color:#e2e8f0;font-size:0.95rem;line-height:1.5;">
          {_esc(row.get('reason', 'Aucune anomalie détectée.'))}
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)


def _init_session() -> None:
    if "analyzed" not in st.session_state:
        st.session_state.analyzed = False
    if "transactions_cache" not in st.session_state:
        st.session_state.transactions_cache = None
    if "results_cache" not in st.session_state:
        st.session_state.results_cache = None
    if "data_fingerprint" not in st.session_state:
        st.session_state.data_fingerprint = None
    if "globe_version" not in st.session_state:
        st.session_state.globe_version = 0


def _fingerprint(transactions: list[dict], ai_enabled: bool, ai_weight: float) -> str:
    ids = ",".join(str(t.get("transaction_id", "")) for t in transactions)
    return f"{ids}|{ai_enabled}|{ai_weight}"


def _run_analysis(transactions: list[dict], ai_enabled: bool, ai_weight: float) -> None:
    rule_results = detect_fraud(transactions)
    if ai_enabled and SKLEARN_AVAILABLE:
        results = enhance_with_ai(transactions, rule_results, ai_weight=ai_weight)
    else:
        results = [
            {**r, "rule_score": r["fraud_score"], "ai_score": 0.0, "ai_boosted": False}
            for r in rule_results
        ]
    st.session_state.transactions_cache = transactions
    st.session_state.results_cache = results
    st.session_state.analyzed = True
    st.session_state.data_fingerprint = _fingerprint(transactions, ai_enabled, ai_weight)
    st.session_state.globe_version = st.session_state.get("globe_version", 0) + 1


def _render_kpis(df) -> None:
    total = len(df)
    alerts = int(df["is_suspicious"].sum()) if "is_suspicious" in df.columns else 0
    safe = total - alerts
    avg = float(df["fraud_score"].mean()) if "fraud_score" in df.columns else 0.0
    ai_boosted = int(df["ai_boosted"].sum()) if "ai_boosted" in df.columns else 0
    avg_ai = float(df["ai_score"].mean()) if "ai_score" in df.columns else 0.0

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f"""<div class="kpi-card"><div class="kpi-label">Transactions</div>
            <div class="kpi-value accent">{total}</div></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="kpi-card"><div class="kpi-label">Alertes fraude</div>
            <div class="kpi-value danger">{alerts}</div></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="kpi-card"><div class="kpi-label">Conformes</div>
            <div class="kpi-value safe">{safe}</div></div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class="kpi-card"><div class="kpi-label">Score fusionné</div>
            <div class="kpi-value">{avg:.0%}</div></div>""", unsafe_allow_html=True)
    with c5:
        st.markdown(f"""<div class="kpi-card"><div class="kpi-label">Confirmations IA</div>
            <div class="kpi-value accent">{ai_boosted}</div>
            <div class="kpi-label" style="margin-top:4px">Moy. IA {avg_ai:.0%}</div></div>""",
            unsafe_allow_html=True)


def render_interface(transactions: list[dict], results: list[dict]) -> None:
    import pandas as pd

    df_tx = pd.DataFrame(transactions)
    df_res = pd.DataFrame(results)
    df = df_tx.merge(df_res, on="transaction_id", how="right") if "transaction_id" in df_tx.columns else df_res.copy()
    df["niveau_risque"] = df["fraud_score"].apply(lambda s: _risk_level(float(s))[0])

    st.markdown("""
    <div class="hero-block">
      <span class="badge-ai">IA + Règles métier</span>
      <p class="hero-title">Centre de surveillance anti-fraude</p>
      <p class="hero-sub">Analyse hybride : moteur de règles + modèle d'anomalies (Isolation Forest).
      Le planisphère signale les pays à risque en temps réel.</p>
    </div>
    """, unsafe_allow_html=True)

    _render_kpis(df)

    globe_col, signals_col = st.columns([1.4, 1])
    with globe_col:
        st.markdown('<p class="section-title">🌍 Planisphère — signaux par pays</p>', unsafe_allow_html=True)
        render_globe(df, height=480, version=st.session_state.get("globe_version", 0))

    with signals_col:
        st.markdown('<p class="section-title">📡 Alertes géographiques</p>', unsafe_allow_html=True)
        if "country" in df.columns:
            country_stats = (
                df.groupby("country", dropna=True)
                .agg(total=("transaction_id", "count"), alertes=("is_suspicious", "sum"),
                     score_max=("fraud_score", "max"))
                .reset_index()
                .sort_values("alertes", ascending=False)
            )
            for _, row in country_stats.iterrows():
                code = row["country"] or "?"
                alerts = int(row["alertes"])
                color = "#ef4444" if alerts > 0 else "#22c55e"
                st.markdown(f"""
                <div class="alert-card" style="border-color:{color}">
                  <strong style="color:#f1f5f9">{code}</strong>
                  <span style="color:#64748b"> — {int(row['total'])} tx</span><br>
                  <span style="color:{color};font-weight:600">{alerts} alerte(s)</span>
                  <span style="color:#64748b"> · score max {row['score_max']:.0%}</span>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("Aucune donnée géographique.")

    st.markdown("---")

    tab_table, tab_alertes, tab_ia, tab_aide = st.tabs([
        "📊 Transactions", "🚨 Alertes", "🤖 Analyse IA", "📖 Guide",
    ])

    with tab_table:
        st.markdown('<div class="filter-panel">', unsafe_allow_html=True)
        f1, f2, f3, f4 = st.columns(4)
        countries = ["(Tous)"] + sorted(df["country"].dropna().unique().tolist()) if "country" in df.columns else ["(Tous)"]
        users = ["(Tous)"] + sorted(df["user_id"].dropna().unique().tolist()) if "user_id" in df.columns else ["(Tous)"]
        country = f1.selectbox("🌍 Pays", countries, key="filter_country")
        user_f = f2.selectbox("👤 Client", users, key="filter_user")
        only_sus = f3.checkbox("🚨 Suspectes uniquement", key="filter_suspicious")
        min_s = f4.slider("📊 Score minimum", 0.0, 1.0, 0.0, 0.05, key="filter_min_score")
        st.markdown("</div>", unsafe_allow_html=True)

        view = df.copy()
        if country != "(Tous)":
            view = view[view["country"] == country]
        if user_f != "(Tous)":
            view = view[view["user_id"] == user_f]
        if only_sus:
            view = view[view["is_suspicious"]]
        view = view[view["fraud_score"] >= min_s].sort_values("fraud_score", ascending=False)

        sus_count = int(view["is_suspicious"].sum()) if "is_suspicious" in view.columns else 0
        st.markdown(
            f'<span class="tx-count">{len(view)} transaction(s) · {sus_count} alerte(s)</span>',
            unsafe_allow_html=True,
        )

        if view.empty:
            st.info("Aucune transaction ne correspond aux filtres.")
        else:
            view_mode = st.radio(
                "Affichage",
                ["Compact", "Tableau"],
                horizontal=True,
                key="tx_view_mode",
                label_visibility="collapsed",
            )

            if view_mode == "Compact":
                _render_tx_compact_list(view)
            else:
                cols = [c for c in [
                    "transaction_id", "timestamp", "user_id", "amount", "currency",
                    "merchant", "country", "fraud_score", "rule_score", "ai_score",
                    "niveau_risque", "is_suspicious", "reason",
                ] if c in view.columns]
                st.dataframe(
                    view[cols],
                    width="stretch",
                    hide_index=True,
                    column_config={
                        "fraud_score": st.column_config.ProgressColumn(
                            "Score", min_value=0, max_value=1, format="%.0f%%",
                        ),
                        "rule_score": st.column_config.NumberColumn("Règles", format="%.2f"),
                        "ai_score": st.column_config.NumberColumn("IA", format="%.2f"),
                        "is_suspicious": st.column_config.CheckboxColumn("Suspect"),
                    },
                )

    with tab_alertes:
        alerts = df[df["is_suspicious"]].sort_values("fraud_score", ascending=False)
        if alerts.empty:
            st.success("Aucune alerte sur ce lot.")
        else:
            for _, row in alerts.iterrows():
                score = float(row["fraud_score"])
                label, color = _risk_level(score)
                ai_tag = " · 🤖 IA" if row.get("ai_boosted") else ""
                st.markdown(f"""
                <div class="alert-card" style="border-color:{color}">
                  <strong style="color:#f8fafc">{row.get('transaction_id')}</strong>
                  <span style="color:#64748b"> · {row.get('user_id')} · {row.get('amount')} {row.get('currency', '')}</span><br>
                  <span style="color:{color};font-weight:700">Risque {label} — {score:.0%}{ai_tag}</span><br>
                  <span style="color:#94a3b8;font-size:0.9em">{row.get('reason', '')}</span>
                </div>""", unsafe_allow_html=True)

    with tab_ia:
        st.markdown("""
        #### Moteur IA — Isolation Forest

        Le modèle analyse **6 dimensions** par transaction :
        montant, log-montant, heure, présence carte, pays, fréquence client.

        Il détecte les comportements atypiques que les règles seules pourraient manquer,
        puis fusionne les scores : **60 % règles + 40 % IA**.
        """)
        if not SKLEARN_AVAILABLE:
            st.warning("Installez scikit-learn : `pip install scikit-learn`")
        else:
            st.success("scikit-learn actif — modèle Isolation Forest opérationnel")

        if "ai_score" in df.columns:
            chart1, chart2 = st.columns(2)
            with chart1:
                st.markdown("**Score IA vs Score règles**")
                scatter = df[["rule_score", "ai_score", "is_suspicious"]].copy()
                st.scatter_chart(scatter, x="rule_score", y="ai_score", color="is_suspicious")
            with chart2:
                st.markdown("**Distribution score IA**")
                st.bar_chart(df["ai_score"].round(2).value_counts().sort_index())

    with tab_aide:
        st.markdown("""
        | Couche | Rôle |
        |--------|------|
        | **Règles métier** | Montants, géographie, fréquence, doublons |
        | **IA (Isolation Forest)** | Anomalies multivariées, confirmation des alertes |
        | **Planisphère** | Visualisation des signaux par pays en temps réel |

        **Commande :** `streamlit run app.py`
        """)

    st.markdown("---")
    st.markdown('<p class="section-title">🔍 Inspecter une transaction</p>', unsafe_allow_html=True)

    if not df.empty:
        tx_index = df.set_index("transaction_id")
        tx_options = df.sort_values("fraud_score", ascending=False)["transaction_id"].tolist()

        def _tx_label(tid: str) -> str:
            r = tx_index.loc[tid]
            icon = "🚨" if r["is_suspicious"] else "✅"
            return f"{icon} {tid} — {float(r['fraud_score']):.0%}"

        sel = st.selectbox(
            "Sélectionner une transaction à analyser en détail",
            tx_options,
            key="inspect_transaction",
            format_func=_tx_label,
        )
        row = df[df["transaction_id"] == sel].iloc[0]
        _render_inspector(row)


def main() -> None:
    st.set_page_config(
        page_title="FraudShield — INTELO2026",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _init_session()
    _inject_styles()

    with st.sidebar:
        st.markdown("### 🛡️ FraudShield")
        st.caption("Hackathon INTELO2026 · @koy-B")
        st.divider()

        use_sample = st.toggle("Données d'exemple", value=True, key="toggle_sample")
        ai_enabled = st.toggle("Boost IA activé", value=True, key="toggle_ai")
        ai_weight = st.slider(
            "Poids IA dans le score", 0.1, 0.6, 0.4, 0.05,
            disabled=not ai_enabled, key="slider_ai_weight",
        )

        transactions: list[dict] = []
        if use_sample:
            transactions = load_transactions(str(SAMPLE_CSV))
            st.success(f"{len(transactions)} transactions")
        else:
            uploaded = st.file_uploader("CSV", type=["csv"], key="upload_csv")
            if uploaded:
                tmp = Path(".streamlit_upload.csv")
                tmp.write_bytes(uploaded.getvalue())
                transactions = load_transactions(str(tmp))
                tmp.unlink(missing_ok=True)
                st.success(f"{len(transactions)} importées")

        if st.session_state.analyzed:
            st.divider()
        if st.session_state.analyzed and st.button("Réinitialiser l'analyse", use_container_width=True):
            st.session_state.analyzed = False
            st.session_state.transactions_cache = None
            st.session_state.results_cache = None
            st.session_state.data_fingerprint = None
            st.session_state.globe_version = 0
            st.rerun()

    st.markdown("# FraudShield")
    st.caption("Détection de fraude financière augmentée par l'IA")

    if not transactions:
        st.info("Chargez des transactions dans la barre latérale.")
        return

    fp = _fingerprint(transactions, ai_enabled, ai_weight)
    if st.session_state.data_fingerprint and st.session_state.data_fingerprint != fp:
        st.session_state.analyzed = False

    col_btn, col_hint = st.columns([2, 3])
    with col_btn:
        run_clicked = st.button(
            "⚡ Lancer l'analyse hybride (Règles + IA)",
            type="primary",
            use_container_width=True,
            key="btn_analyze",
        )
    with col_hint:
        if st.session_state.analyzed and st.session_state.data_fingerprint != fp:
            st.warning("Données ou paramètres IA modifiés — relancez l'analyse.")

    if run_clicked:
        try:
            with st.spinner("Analyse en cours — règles métier + modèle IA..."):
                _run_analysis(transactions, ai_enabled, ai_weight)
        except NotImplementedError:
            st.error("Implémentez `detect_fraud` dans fraud_detection.py.")
            return
        except Exception as exc:
            st.error(f"Erreur : {exc}")
            return

    if st.session_state.analyzed and st.session_state.transactions_cache and st.session_state.results_cache:
        render_interface(st.session_state.transactions_cache, st.session_state.results_cache)


if __name__ == "__main__":
    main()
