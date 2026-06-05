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

      #MainMenu, footer, header { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)


def _risk_level(score: float) -> tuple[str, str]:
    for low, high, label, color in RISK_LABELS:
        if low <= score < high:
            return label, color
    return "Élevé", "#ef4444"


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
        f1, f2, f3, f4 = st.columns(4)
        countries = ["(Tous)"] + sorted(df["country"].dropna().unique().tolist()) if "country" in df.columns else ["(Tous)"]
        users = ["(Tous)"] + sorted(df["user_id"].dropna().unique().tolist()) if "user_id" in df.columns else ["(Tous)"]
        country = f1.selectbox("Pays", countries, key="filter_country")
        user_f = f2.selectbox("Client", users, key="filter_user")
        only_sus = f3.checkbox("Suspectes seulement", key="filter_suspicious")
        min_s = f4.slider("Score min.", 0.0, 1.0, 0.0, 0.05, key="filter_min_score")

        view = df.copy()
        if country != "(Tous)":
            view = view[view["country"] == country]
        if user_f != "(Tous)":
            view = view[view["user_id"] == user_f]
        if only_sus:
            view = view[view["is_suspicious"]]
        view = view[view["fraud_score"] >= min_s]

        cols = [c for c in [
            "transaction_id", "timestamp", "user_id", "amount", "currency",
            "merchant", "country", "fraud_score", "rule_score", "ai_score",
            "niveau_risque", "is_suspicious", "reason",
        ] if c in view.columns]
        st.dataframe(view[cols].sort_values("fraud_score", ascending=False),
                     use_container_width=True, hide_index=True)

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
    st.subheader("🔍 Inspecter une transaction")
    if not df.empty:
        sel = st.selectbox("Transaction", df["transaction_id"].tolist(), key="inspect_transaction")
        row = df[df["transaction_id"] == sel].iloc[0]
        score = float(row["fraud_score"])
        label, color = _risk_level(score)
        left, right = st.columns([2, 1])
        with left:
            st.json({
                "id": row.get("transaction_id"),
                "client": row.get("user_id"),
                "montant": f"{row.get('amount')} {row.get('currency', '')}",
                "pays": row.get("country"),
                "commerçant": row.get("merchant"),
                "score_règles": row.get("rule_score"),
                "score_ia": row.get("ai_score"),
                "score_final": score,
            })
        with right:
            st.markdown(f"**{label}**", help="Niveau de risque")
            st.progress(min(score, 1.0))
            if row.get("is_suspicious"):
                st.error(row.get("reason", ""))
            else:
                st.success(row.get("reason", "Conforme"))


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
