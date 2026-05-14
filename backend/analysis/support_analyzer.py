"""
Analyseur catégories produits — KPIs depuis 03_analyse_categorie.csv.

Colonnes attendues (après normalisation) :
    category, ca_total, profit_total, nb_transactions,
    quantite_vendue, prix_moyen
"""

import logging
from typing import Any, Dict

import pandas as pd

logger = logging.getLogger(__name__)


def analyze(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calcule les KPIs catégories à partir du DataFrame des catégories.

    KPIs calculés :
        - total_revenue             : CA total toutes catégories (TND)
        - total_profit              : profit total (TND)
        - total_transactions        : nombre total de transactions
        - total_quantity            : quantité totale vendue
        - top_category_by_revenue   : catégorie avec le plus fort CA
        - top_category_by_quantity  : catégorie avec la plus grande quantité vendue
        - revenue_by_category       : CA par catégorie (dict)
        - profit_by_category        : profit par catégorie (dict)
        - qty_by_category           : quantité par catégorie (dict)

    Args:
        df: DataFrame avec colonnes category, ca_total, profit_total,
            nb_transactions, quantite_vendue, prix_moyen.

    Returns:
        Dictionnaire contenant tous les KPIs catégories.
    """
    logger.info("Analyse catégories en cours — %d lignes", len(df))

    required_cols = {
        "category", "ca_total", "profit_total",
        "nb_transactions", "quantite_vendue", "prix_moyen"
    }
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Colonnes manquantes dans le dataset categories : {missing}")

    df = df.copy()

    total_revenue = float(df["ca_total"].sum())
    total_profit = float(df["profit_total"].sum())
    total_transactions = int(df["nb_transactions"].sum())
    total_quantity = int(df["quantite_vendue"].sum())

    revenue_by_category: Dict[str, float] = {
        str(row["category"]): round(float(row["ca_total"]), 2)
        for _, row in df.iterrows()
    }
    profit_by_category: Dict[str, float] = {
        str(row["category"]): round(float(row["profit_total"]), 2)
        for _, row in df.iterrows()
    }
    qty_by_category: Dict[str, int] = {
        str(row["category"]): int(row["quantite_vendue"])
        for _, row in df.iterrows()
    }

    top_category_by_revenue = (
        max(revenue_by_category, key=revenue_by_category.get)
        if revenue_by_category else "N/A"
    )
    top_category_by_quantity = (
        max(qty_by_category, key=qty_by_category.get)
        if qty_by_category else "N/A"
    )

    kpis = {
        "total_revenue": round(total_revenue, 2),
        "total_profit": round(total_profit, 2),
        "total_transactions": total_transactions,
        "total_quantity": total_quantity,
        "top_category_by_revenue": top_category_by_revenue,
        "top_category_by_quantity": top_category_by_quantity,
        "revenue_by_category": revenue_by_category,
        "profit_by_category": profit_by_category,
        "qty_by_category": qty_by_category,
        # Alias pour compatibilité
        "top_category_by_conv": top_category_by_quantity,
        "conversions_by_category": qty_by_category,
        "revenue_trend": "stable",
    }

    logger.info(
        "KPIs catégories calculés : top=%s, CA=%.0f TND",
        top_category_by_revenue, total_revenue
    )
    return kpis
