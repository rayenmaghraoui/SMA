"""
Analyseur canaux marketing — KPIs depuis 04_analyse_canaux.csv.

Colonnes attendues (après normalisation) :
    sales_channel, ca_total, nb_transactions, panier_moyen
"""

import logging
from typing import Any, Dict

import pandas as pd

logger = logging.getLogger(__name__)


def analyze(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calcule les KPIs canaux à partir du DataFrame des canaux de vente.

    KPIs calculés :
        - total_ca              : CA total tous canaux (TND)
        - total_transactions    : nombre total de transactions
        - best_channel          : canal avec le plus fort CA
        - top_panier_channel    : canal avec le panier moyen le plus élevé
        - ca_by_channel         : CA par canal (dict)
        - transactions_by_channel : transactions par canal (dict)
        - panier_by_channel     : panier moyen par canal (dict)

    Args:
        df: DataFrame avec colonnes sales_channel, ca_total,
            nb_transactions, panier_moyen.

    Returns:
        Dictionnaire contenant tous les KPIs canaux.
    """
    logger.info("Analyse canaux marketing en cours — %d lignes", len(df))

    required_cols = {"sales_channel", "ca_total", "nb_transactions", "panier_moyen"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Colonnes manquantes dans le dataset canaux : {missing}")

    df = df.copy()

    total_ca = float(df["ca_total"].sum())
    total_transactions = int(df["nb_transactions"].sum())

    ca_by_channel: Dict[str, float] = {
        str(row["sales_channel"]): round(float(row["ca_total"]), 2)
        for _, row in df.iterrows()
    }
    transactions_by_channel: Dict[str, int] = {
        str(row["sales_channel"]): int(row["nb_transactions"])
        for _, row in df.iterrows()
    }
    panier_by_channel: Dict[str, float] = {
        str(row["sales_channel"]): round(float(row["panier_moyen"]), 2)
        for _, row in df.iterrows()
    }

    best_channel = max(ca_by_channel, key=ca_by_channel.get) if ca_by_channel else "N/A"
    top_panier_channel = max(panier_by_channel, key=panier_by_channel.get) if panier_by_channel else "N/A"

    kpis = {
        "total_ca": round(total_ca, 2),
        "total_transactions": total_transactions,
        "best_channel": best_channel,
        "top_panier_channel": top_panier_channel,
        "ca_by_channel": ca_by_channel,
        "transactions_by_channel": transactions_by_channel,
        "panier_by_channel": panier_by_channel,
        # Alias pour compatibilité avec report_agent
        "total_budget_spent": round(total_ca, 2),
        "total_conversions": total_transactions,
        "avg_conversion_rate": 0.0,
        "cost_per_conversion": 0.0,
        "roi_by_channel": ca_by_channel,
        "revenue_by_channel": ca_by_channel,
        "top_campaign": best_channel,
    }

    logger.info(
        "KPIs canaux calculés : CA total=%.0f TND, meilleur canal=%s",
        total_ca, best_channel
    )
    return kpis
