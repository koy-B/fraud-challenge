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


def render_interface(transactions: list[dict], results: list[dict]) -> None:
    """
    ══════════════════════════════════════════════════════════════════
    À COMPLÉTER — votre interface intuitive pour le jury / le public.
    ══════════════════════════════════════════════════════════════════

    Idées (libres) :
      - titres et textes en langage simple (« transaction suspecte », « client à risque ») ;
      - cartes / indicateurs visuels (nombre d'alertes, niveau de risque) ;
      - tableau ou liste filtrable (uniquement les suspectes, par client, par pays…) ;
      - codes couleur, icônes, graphiques ;
      - zone « comment l'IA / vos règles décident » pour expliquer une alerte.

    Le jury évalue : clarté, utilité, intuitivité — pas le code en lui-même.
    """
    import pandas as pd

    # Merge original transactions with results for a rich table
    df_tx = pd.DataFrame(transactions)
    df_res = pd.DataFrame(results)
    if "transaction_id" in df_tx.columns and "transaction_id" in df_res.columns:
        df = df_tx.merge(df_res, on="transaction_id", how="right")
    else:
        df = df_res.copy()

    # Basic KPIs
    total = len(df)
    suspicious_count = int(df["is_suspicious"].sum()) if "is_suspicious" in df.columns else 0
    avg_score = float(df["fraud_score"].mean()) if "fraud_score" in df.columns else 0.0

    k1, k2, k3 = st.columns([1, 1, 2])
    k1.metric("Transactions", f"{total}")
    k2.metric("Alertes", f"{suspicious_count}")
    k3.metric("Score moyen", f"{avg_score:.2f}")

    st.markdown("---")

    # Filters
    with st.expander("Filtres"):
        cols = st.columns(3)
        country_opts = ["(Tous)"] + sorted(df["country"].dropna().unique().tolist()) if "country" in df.columns else ["(Tous)"]
        country = cols[0].selectbox("Pays", country_opts)
        only_suspicious = cols[1].checkbox("Afficher uniquement les suspectes", value=False)
        min_score = cols[2].slider("Score minimal", 0.0, 1.0, 0.0, 0.01)

    # Apply filters
    df_view = df.copy()
    if country and country != "(Tous)" and "country" in df_view.columns:
        df_view = df_view[df_view["country"] == country]
    if only_suspicious and "is_suspicious" in df_view.columns:
        df_view = df_view[df_view["is_suspicious"] == True]
    if "fraud_score" in df_view.columns:
        df_view = df_view[df_view["fraud_score"] >= float(min_score)]

    # Charts
    st.subheader("Vue d'ensemble")
    chart_cols = st.columns(2)
    if "country" in df_view.columns:
        by_country = df_view["country"].fillna("(inconnu)").value_counts()
        chart_cols[0].bar_chart(by_country)
    if "merchant" in df_view.columns:
        by_merchant = df_view["merchant"].fillna("(inconnu)").value_counts().head(10)
        chart_cols[1].bar_chart(by_merchant)

    st.markdown("---")

    # Table of transactions
    st.subheader("Transactions")
    display_cols = [c for c in ["transaction_id", "timestamp", "user_id", "amount", "currency", "merchant", "country", "fraud_score", "is_suspicious", "reason"] if c in df_view.columns]
    st.dataframe(df_view[display_cols].sort_values(by=["fraud_score"], ascending=False), use_container_width=True)

    # Detail panel
    st.markdown("---")
    st.subheader("Détails d'une transaction")
    tx_ids = df_view["transaction_id"].tolist()
    if tx_ids:
        sel = st.selectbox("Sélectionner une transaction", options=tx_ids)
        row = df_view[df_view["transaction_id"] == sel].iloc[0]
        st.write(row[display_cols].to_dict())
        score = float(row.get("fraud_score", 0.0))
        st.progress(min(max(score, 0.0), 1.0))
        st.caption(f"Raison: {row.get('reason', '')}")
    else:
        st.info("Aucune transaction à afficher avec les filtres sélectionnés.")

    # Explainability / notes
    with st.expander("Comment sont prises les décisions ?"):
        st.write(
            "Le modèle présenté ici utilise des règles simples pour l'exemple : montants non-positifs sont signalés, "
            "et les montants très supérieurs à l'historique de l'utilisateur sont considérés comme suspects. "
            "Pour un usage réel, remplacez par un modèle ML ou règles métier robustes et documentées."
        )


def main() -> None:
    st.set_page_config(
        page_title="Détection de fraude — Hackathon INTELO2026",
        page_icon="🛡️",
        layout="wide",
    )

    st.title("Détection de fraude financière")
    st.caption("Hackathon INTELO2026 — interface participant · évaluée par le jury")

    with st.sidebar:
        st.header("Charger des données")
        use_sample = st.toggle("Utiliser le fichier d'exemple", value=True)
        transactions: list[dict] = []

        if use_sample:
            transactions = load_transactions(str(SAMPLE_CSV))
            st.success(f"{len(transactions)} transactions (exemple)")
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
            "**Jury :** évaluez l'ergonomie et la clarté de l'écran principal, "
            "pas seulement le score des tests."
        )

    if not transactions:
        st.info("Chargez des transactions (barre latérale) puis lancez l'analyse.")
        return

    if st.button("Analyser", type="primary"):
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
