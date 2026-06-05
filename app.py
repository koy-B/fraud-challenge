"""
Interface Streamlit — À CRÉER PAR VOUS pour le jury.

Cette application fournit une interface simple pour charger des transactions (fichier exemple ou import),
lancer une analyse via `detect_fraud()` et explorer les résultats : indicateurs clés, filtres, graphiques
et détails par transaction. L'objectif est d'offrir une vue claire et compréhensible pour un public
non technique (le jury) afin de faciliter la comparaison et le repêchage des candidats.

Le jury lancera :  streamlit run app.py

Règles :
    - Ne modifiez pas l'appel à detect_fraud / load_transactions (contrat technique).
    - Personnalisez render_interface() : clarté, intuitivité, compréhension pour un public non technique.
    - L'interface n'est PAS notée par la CI ; elle sert au jury pour repêcher et comparer les candidats.
"""

from pathlib import Path

import streamlit as st

from fraud_detection import detect_fraud, load_transactions

SAMPLE_CSV = Path(__file__).parent / "data" / "sample_transactions.csv"

RISK_LABELS = [
    (0.0, 0.3, "Faible", "#22c55e"),
    (0.3, 0.7, "Modéré", "#f59e0b"),
    (0.7, 1.01, "Élevé", "#ef4444"),
]


def _risk_level(score: float) -> tuple[str, str]:
    for low, high, label, color in RISK_LABELS:
        if low <= score < high:
            return label, color
    return "Élevé", "#ef4444"


def render_interface(transactions: list[dict], results: list[dict]) -> None:
    """Interface intuitive pour le jury : alertes, filtres et explications."""
    import pandas as pd

    df_tx = pd.DataFrame(transactions)
    df_res = pd.DataFrame(results)
    if "transaction_id" in df_tx.columns and "transaction_id" in df_res.columns:
        df = df_tx.merge(df_res, on="transaction_id", how="right")
    else:
        df = df_res.copy()

    df["niveau_risque"] = df["fraud_score"].apply(lambda s: _risk_level(float(s))[0])

    total = len(df)
    suspicious_count = int(df["is_suspicious"].sum()) if "is_suspicious" in df.columns else 0
    safe_count = total - suspicious_count
    avg_score = float(df["fraud_score"].mean()) if "fraud_score" in df.columns else 0.0
    max_score = float(df["fraud_score"].max()) if "fraud_score" in df.columns else 0.0

    st.markdown("### Résultats de l'analyse")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Transactions analysées", total)
    k2.metric("Alertes fraude", suspicious_count, delta=f"-{safe_count} conformes" if safe_count else None)
    k3.metric("Score moyen", f"{avg_score:.0%}")
    k4.metric("Risque max", f"{max_score:.0%}")

    if suspicious_count > 0:
        st.warning(
            f"**{suspicious_count} transaction(s) suspecte(s)** nécessitent une vérification. "
            "Consultez le détail ci-dessous pour comprendre chaque alerte."
        )
    else:
        st.success("Aucune transaction suspecte détectée sur ce lot.")

    st.markdown("---")

    tab_table, tab_alertes, tab_aide = st.tabs(["Vue complète", "Alertes uniquement", "Comment ça marche ?"])

    with tab_table:
        with st.expander("Filtres", expanded=False):
            cols = st.columns(4)
            country_opts = ["(Tous)"] + sorted(df["country"].dropna().unique().tolist()) if "country" in df.columns else ["(Tous)"]
            country = cols[0].selectbox("Pays", country_opts)
            user_opts = ["(Tous)"] + sorted(df["user_id"].dropna().unique().tolist()) if "user_id" in df.columns else ["(Tous)"]
            user_filter = cols[1].selectbox("Client", user_opts)
            only_suspicious = cols[2].checkbox("Suspectes seulement", value=False)
            min_score = cols[3].slider("Score minimal", 0.0, 1.0, 0.0, 0.05)

        df_view = df.copy()
        if country != "(Tous)" and "country" in df_view.columns:
            df_view = df_view[df_view["country"] == country]
        if user_filter != "(Tous)" and "user_id" in df_view.columns:
            df_view = df_view[df_view["user_id"] == user_filter]
        if only_suspicious and "is_suspicious" in df_view.columns:
            df_view = df_view[df_view["is_suspicious"]]
        if "fraud_score" in df_view.columns:
            df_view = df_view[df_view["fraud_score"] >= min_score]

        chart_cols = st.columns(2)
        if "fraud_score" in df_view.columns:
            risk_counts = df_view["niveau_risque"].value_counts()
            chart_cols[0].bar_chart(risk_counts, color="#6366f1")
            chart_cols[0].caption("Répartition par niveau de risque")
        if "country" in df_view.columns:
            by_country = df_view.groupby("country")["is_suspicious"].sum().fillna(0)
            chart_cols[1].bar_chart(by_country, color="#ef4444")
            chart_cols[1].caption("Alertes par pays")

        display_cols = [
            c for c in [
                "transaction_id", "timestamp", "user_id", "amount", "currency",
                "merchant", "country", "fraud_score", "niveau_risque",
                "is_suspicious", "reason",
            ]
            if c in df_view.columns
        ]
        st.dataframe(
            df_view[display_cols].sort_values("fraud_score", ascending=False),
            use_container_width=True,
            hide_index=True,
        )

    with tab_alertes:
        alerts = df[df["is_suspicious"]].sort_values("fraud_score", ascending=False) if "is_suspicious" in df.columns else df.head(0)
        if alerts.empty:
            st.info("Aucune alerte sur ce lot de transactions.")
        else:
            for _, row in alerts.iterrows():
                score = float(row.get("fraud_score", 0))
                label, color = _risk_level(score)
                st.markdown(
                    f"""
                    <div style="border-left: 4px solid {color}; padding: 12px 16px; margin-bottom: 12px;
                                background: #f8fafc; border-radius: 0 8px 8px 0;">
                        <strong>{row.get('transaction_id', '?')}</strong>
                        &nbsp;·&nbsp; Client <strong>{row.get('user_id', '?')}</strong>
                        &nbsp;·&nbsp; {row.get('amount', '?')} {row.get('currency', '')}
                        &nbsp;·&nbsp; {row.get('merchant', '')} ({row.get('country', 'N/A')})<br>
                        <span style="color:{color}; font-weight:600;">Risque {label} — {score:.0%}</span><br>
                        <em>{row.get('reason', '')}</em>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    with tab_aide:
        st.markdown("""
        #### Comment le détecteur décide ?

        Le moteur analyse chaque transaction **en la comparant à l'historique du même client** :

        | Règle | Exemple | Verdict |
        |-------|---------|---------|
        | Montant nul ou négatif | Remboursement à -30 € | Suspect |
        | Champ obligatoire manquant | Pays absent | Suspect |
        | Montant >> habitudes (×10) | 4 800 € alors que la moyenne est ~50 € | Suspect |
        | Deux pays en < 3 h | Paris puis Tokyo en 40 min | Suspect |
        | Rafale de transactions | 5+ paiements en 1 heure | Suspect |
        | Voyage légitime | Hôtel en France puis aux USA 3 jours après | Conforme |

        **Objectif :** signaler les fraudes évidentes sans pénaliser les clients honnêtes.
        """)

    st.markdown("---")
    st.subheader("Inspecter une transaction")
    tx_ids = df["transaction_id"].tolist()
    if tx_ids:
        sel = st.selectbox("Choisir une transaction", options=tx_ids)
        row = df[df["transaction_id"] == sel].iloc[0]
        score = float(row.get("fraud_score", 0))
        label, color = _risk_level(score)

        c1, c2 = st.columns([2, 1])
        with c1:
            st.json({
                "transaction_id": row.get("transaction_id"),
                "client": row.get("user_id"),
                "montant": f"{row.get('amount')} {row.get('currency', '')}",
                "commerçant": row.get("merchant"),
                "pays": row.get("country"),
                "date": row.get("timestamp"),
                "carte_présente": row.get("card_present"),
            })
        with c2:
            st.markdown(f"**Niveau :** <span style='color:{color}'>{label}</span>", unsafe_allow_html=True)
            st.progress(min(max(score, 0.0), 1.0))
            st.caption(f"Score : {score:.0%}")
            if row.get("is_suspicious"):
                st.error(f"Alerte : {row.get('reason', '')}")
            else:
                st.success(row.get("reason", "Transaction conforme"))


def main() -> None:
    st.set_page_config(
        page_title="Détection de fraude — Hackathon INTELO2026",
        page_icon="🛡️",
        layout="wide",
    )

    st.title("🛡️ Détection de fraude financière")
    st.caption("Hackathon INTELO2026 — Interface de démonstration · @koy-B")

    with st.sidebar:
        st.header("Données")
        use_sample = st.toggle("Fichier d'exemple", value=True)
        transactions: list[dict] = []

        if use_sample:
            transactions = load_transactions(str(SAMPLE_CSV))
            st.success(f"{len(transactions)} transactions chargées")
        else:
            uploaded = st.file_uploader("Importer un CSV", type=["csv"])
            if uploaded:
                tmp = Path(".streamlit_upload.csv")
                tmp.write_bytes(uploaded.getvalue())
                transactions = load_transactions(str(tmp))
                tmp.unlink(missing_ok=True)
                st.success(f"{len(transactions)} transactions importées")

        st.divider()
        st.markdown(
            "**Pour le jury :** cette interface explique *pourquoi* une transaction est signalée, "
            "sans avoir à lire le code Python."
        )

    if not transactions:
        st.info("Chargez des transactions via la barre latérale, puis lancez l'analyse.")
        return

    if st.button("Lancer l'analyse anti-fraude", type="primary", use_container_width=True):
        try:
            results = detect_fraud(transactions)
        except NotImplementedError:
            st.error("Implémentez d'abord `detect_fraud` dans `fraud_detection.py`.")
            return
        except Exception as exc:
            st.error(f"Erreur : {exc}")
            return

        render_interface(transactions, results)


if __name__ == "__main__":
    main()
