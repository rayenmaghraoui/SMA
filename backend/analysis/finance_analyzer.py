"""
Analyseur financier — calcul des KPIs financiers.

Analyse le dataset 01_finance_performance.csv et produit les indicateurs
clés de performance financière pour une PME tunisienne.
"""

import logging
from typing import Any, Dict

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

logger = logging.getLogger(__name__)


def analyze(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calcule les KPIs financiers à partir du DataFrame finance.

    KPIs calculés :
        - revenue_total     : chiffre d'affaires total (TND)
        - profit_total      : bénéfice net total (TND)
        - profit_margin     : marge bénéficiaire moyenne (%)
        - avg_growth_rate   : taux de croissance moyen (%)
        - best_month        : mois le plus rentable (YYYY-MM)
        - worst_month       : mois le moins rentable (YYYY-MM)
        - trend             : tendance générale ("hausse" | "baisse" | "stable")
        - revenue_volatility: écart-type du chiffre d'affaires (TND)

    Args:
        df: DataFrame avec colonnes date, revenue, cost, profit, growth_rate.

    Returns:
        Dictionnaire contenant tous les KPIs financiers.
    """
    logger.info("Analyse financière en cours — %d lignes", len(df))

    # Vérification des colonnes requises
    required_cols = {"date", "revenue", "cost", "profit", "growth_rate"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Colonnes manquantes dans le dataset finance : {missing}")

    # Copie de travail
    df = df.copy()

    # S'assurer que 'date' est bien en datetime
    if not pd.api.types.is_datetime64_any_dtype(df["date"]):
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # Trier par date
    df = df.sort_values("date").reset_index(drop=True)

    # ================================================================
    # Calcul des KPIs
    # ================================================================

    # Chiffre d'affaires total (TND)
    revenue_total = float(df["revenue"].sum())

    # Bénéfice net total (TND)
    profit_total = float(df["profit"].sum())

    # Marge bénéficiaire moyenne (%)
    # Marge = (profit / revenue) * 100 — moyenne sur toutes les périodes
    df["margin"] = np.where(
        df["revenue"] != 0,
        (df["profit"] / df["revenue"]) * 100,
        0.0
    )
    profit_margin = float(df["margin"].mean())

    # Taux de croissance moyen (%)
    avg_growth_rate = float(df["growth_rate"].mean())

    # Création d'une colonne mois pour l'agrégation
    df["month"] = df["date"].dt.to_period("M").astype(str)

    # Agrégation mensuelle des profits
    monthly_profits = df.groupby("month")["profit"].sum()

    # Mois le plus rentable
    best_month = str(monthly_profits.idxmax()) if len(monthly_profits) > 0 else "N/A"

    # Mois le moins rentable
    worst_month = str(monthly_profits.idxmin()) if len(monthly_profits) > 0 else "N/A"

    # ================================================================
    # Tendance via régression linéaire
    # ================================================================
    trend = _calculate_trend(df["revenue"].values)

    # ================================================================
    # Volatilité du chiffre d'affaires (écart-type)
    # ================================================================
    revenue_volatility = float(df["revenue"].std())

    kpis = {
        "revenue_total": round(revenue_total, 2),
        "profit_total": round(profit_total, 2),
        "profit_margin": round(profit_margin, 2),
        "avg_growth_rate": round(avg_growth_rate, 2),
        "best_month": best_month,
        "worst_month": worst_month,
        "trend": trend,
        "revenue_volatility": round(revenue_volatility, 2),
    }

    logger.info("KPIs financiers calculés : %s", kpis)
    return kpis


def _calculate_trend(values: np.ndarray) -> str:
    """
    Détermine la tendance d'une série temporelle via régression linéaire.

    Args:
        values: Array de valeurs numériques ordonnées chronologiquement.

    Returns:
        "hausse" si pente > 0.01, "baisse" si pente < -0.01, sinon "stable".
    """
    if len(values) < 2:
        return "stable"

    # Création de la variable X (indices temporels)
    X = np.arange(len(values)).reshape(-1, 1)
    y = values.reshape(-1, 1)

    # Régression linéaire
    model = LinearRegression()
    model.fit(X, y)

    # Pente normalisée par la moyenne des valeurs
    slope = model.coef_[0][0]
    mean_value = np.mean(values)

    if mean_value == 0:
        return "stable"

    # Pente relative (en pourcentage par période)
    relative_slope = (slope / mean_value) * 100

    # Seuils : > 1% par période = hausse, < -1% = baisse
    if relative_slope > 1.0:
        return "hausse"
    elif relative_slope < -1.0:
        return "baisse"
    else:
        return "stable"
