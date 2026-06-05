"""
Analyseur financier — KPIs calculés dynamiquement depuis 01_donnees_vente.csv.

Si le dataset ventes est disponible, les KPIs sont recalculés en temps réel.
Sinon, fallback sur 05_kpis_globaux.csv (format clé-valeur) pour compatibilité.
"""

import logging
from typing import Any, Dict

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def analyze(df: pd.DataFrame, df_ventes: pd.DataFrame = None) -> Dict[str, Any]:
    """
    Calcule les KPIs financiers dynamiquement depuis les transactions (ventes).

    Si df_ventes est fourni, les KPIs sont calculés en temps réel depuis
    01_donnees_vente.csv. Sinon, fallback sur 05_kpis_globaux.csv.

    Args:
        df       : DataFrame kpis_globaux (fallback, format indicateur/valeur).
        df_ventes: DataFrame ventes (calcul dynamique, prioritaire).

    Returns:
        Dictionnaire contenant tous les KPIs financiers.
    """
    if df_ventes is not None and not df_ventes.empty:
        return _analyze_from_ventes(df_ventes)
    return _analyze_from_kpis_csv(df)


def _analyze_from_ventes(df: pd.DataFrame) -> Dict[str, Any]:
    """Calcule les KPIs dynamiquement depuis 01_donnees_vente.csv."""
    logger.info("Calcul dynamique des KPIs depuis ventes — %d transactions", len(df))

    required_cols = {"revenue_tnd", "estimated_profit", "quantity", "customer_id"}
    missing = required_cols - set(df.columns)
    if missing:
        logger.warning("Colonnes manquantes pour calcul dynamique : %s", missing)
        return _analyze_from_kpis_csv(pd.DataFrame())

    revenue_total   = float(df["revenue_tnd"].sum())
    profit_total    = float(df["estimated_profit"].sum())
    profit_margin   = round((profit_total / revenue_total * 100), 2) if revenue_total > 0 else 0.0
    nb_transactions = int(len(df))
    panier_moyen    = round(revenue_total / nb_transactions, 2) if nb_transactions > 0 else 0.0
    quantite_totale = int(df["quantity"].sum())
    nb_clients      = int(df["customer_id"].nunique())
    ca_moyen_client = round(revenue_total / nb_clients, 2) if nb_clients > 0 else 0.0

    # Tendance temporelle (si sale_date disponible)
    avg_growth_rate   = 0.0
    trend             = "stable"
    best_period       = "N/A"
    worst_period      = "N/A"
    revenue_volatility = 0.0

    if "sale_date" in df.columns:
        try:
            df["sale_date"] = pd.to_datetime(df["sale_date"])
            monthly = (
                df.groupby(df["sale_date"].dt.to_period("M"))["revenue_tnd"]
                .sum()
                .sort_index()
            )
            if len(monthly) >= 2:
                growth_rates = monthly.pct_change().dropna() * 100
                avg_growth_rate    = round(float(growth_rates.mean()), 2)
                revenue_volatility = round(float(growth_rates.std()), 2)
                best_period        = str(monthly.idxmax())
                worst_period       = str(monthly.idxmin())
                if avg_growth_rate > 2:
                    trend = "croissance"
                elif avg_growth_rate < -2:
                    trend = "déclin"
                else:
                    trend = "stable"
        except Exception as e:
            logger.warning("Erreur calcul tendance : %s", e)

    kpis = {
        "revenue_total":     round(revenue_total, 2),
        "profit_total":      round(profit_total, 2),
        "profit_margin":     profit_margin,
        "nb_transactions":   nb_transactions,
        "panier_moyen":      panier_moyen,
        "quantite_totale":   quantite_totale,
        "nb_clients":        nb_clients,
        "ca_moyen_client":   ca_moyen_client,
        "avg_growth_rate":   avg_growth_rate,
        "trend":             trend,
        "best_period":       best_period,
        "worst_period":      worst_period,
        "revenue_volatility": revenue_volatility,
        "source":            "dynamique (ventes)",
    }

    logger.info(
        "KPIs dynamiques : CA=%.0f TND, Marge=%.1f%%, Tendance=%s",
        revenue_total, profit_margin, trend
    )
    return kpis


def _analyze_from_kpis_csv(df: pd.DataFrame) -> Dict[str, Any]:
    """Fallback : calcule les KPIs depuis 05_kpis_globaux.csv."""
    logger.info("Fallback KPIs depuis kpis_globaux — %d lignes", len(df))

    if df.empty or "indicateur" not in df.columns:
        return {
            "revenue_total": 0.0, "profit_total": 0.0, "profit_margin": 0.0,
            "nb_transactions": 0, "panier_moyen": 0.0, "quantite_totale": 0,
            "nb_clients": 0, "ca_moyen_client": 0.0,
            "avg_growth_rate": 0.0, "trend": "stable",
            "best_period": "N/A", "worst_period": "N/A",
            "revenue_volatility": 0.0, "source": "fallback (vide)",
        }

    def get_val(name: str) -> float:
        row = df[df["indicateur"].str.strip() == name]
        return float(row["valeur"].values[0]) if len(row) > 0 else 0.0

    return {
        "revenue_total":     round(get_val("CA Total (TND)"), 2),
        "profit_total":      round(get_val("Profit Total (TND)"), 2),
        "profit_margin":     round(get_val("Marge Beneficiaire (%)"), 2),
        "nb_transactions":   int(get_val("Nb Transactions")),
        "panier_moyen":      round(get_val("Panier Moyen (TND)"), 2),
        "quantite_totale":   int(get_val("Quantite Totale Vendue")),
        "nb_clients":        int(get_val("Nb Clients Uniques")),
        "ca_moyen_client":   round(get_val("CA Moyen par Client (TND)"), 2),
        "avg_growth_rate":   0.0,
        "trend":             "stable",
        "best_period":       "N/A",
        "worst_period":      "N/A",
        "revenue_volatility": 0.0,
        "source":            "statique (kpis_globaux.csv)",
    }