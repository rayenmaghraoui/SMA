"""
Analyseur marketing — calcul des KPIs des campagnes marketing.

Analyse le dataset 02_marketing_campaigns.csv et produit les indicateurs
clés de performance marketing pour une PME tunisienne.
"""

import logging
from typing import Any, Dict

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def analyze(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calcule les KPIs marketing à partir du DataFrame des campagnes.

    KPIs calculés :
        - total_budget_spent   : budget total dépensé (TND)
        - total_conversions    : nombre total de conversions
        - avg_conversion_rate  : taux de conversion moyen (%)
        - best_channel         : canal avec le meilleur ROI
        - roi_by_channel       : ROI par canal (dict)
        - cost_per_conversion  : coût moyen par conversion (TND)
        - top_campaign         : campagne la plus performante

    Args:
        df: DataFrame avec colonnes date, campaign_id, channel, budget,
            clicks, conversions, conversion_rate.

    Returns:
        Dictionnaire contenant tous les KPIs marketing.
    """
    logger.info("Analyse marketing en cours — %d lignes", len(df))

    # Vérification des colonnes requises
    required_cols = {
        "date", "campaign_id", "channel", "budget",
        "clicks", "conversions", "conversion_rate"
    }
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Colonnes manquantes dans le dataset marketing : {missing}")

    # Copie de travail
    df = df.copy()

    # ================================================================
    # Calcul des KPIs
    # ================================================================

    # Budget total dépensé (TND)
    total_budget_spent = float(df["budget"].sum())

    # Nombre total de conversions
    total_conversions = int(df["conversions"].sum())

    # Taux de conversion moyen (%)
    # Pondéré par le nombre de clics pour éviter de surévaluer les petites campagnes
    total_clicks = int(df["clicks"].sum())
    if total_clicks > 0:
        avg_conversion_rate = (total_conversions / total_clicks) * 100
    else:
        avg_conversion_rate = 0.0

    # ================================================================
    # ROI par canal
    # ROI = (conversions / budget) * 100
    # ================================================================
    channel_stats = df.groupby("channel").agg({
        "budget": "sum",
        "conversions": "sum",
        "clicks": "sum"
    }).reset_index()

    roi_by_channel: Dict[str, float] = {}
    for _, row in channel_stats.iterrows():
        channel_name = str(row["channel"])
        channel_budget = float(row["budget"])
        channel_conversions = int(row["conversions"])

        if channel_budget > 0:
            roi = (channel_conversions / channel_budget) * 100
        else:
            roi = 0.0

        roi_by_channel[channel_name] = round(roi, 2)

    # Meilleur canal (ROI le plus élevé)
    if roi_by_channel:
        best_channel = max(roi_by_channel, key=roi_by_channel.get)
    else:
        best_channel = "N/A"

    # ================================================================
    # Coût par conversion (TND)
    # ================================================================
    if total_conversions > 0:
        cost_per_conversion = total_budget_spent / total_conversions
    else:
        cost_per_conversion = 0.0

    # ================================================================
    # Campagne la plus performante
    # Critère : nombre de conversions le plus élevé
    # ================================================================
    campaign_conversions = df.groupby("campaign_id")["conversions"].sum()
    if len(campaign_conversions) > 0:
        top_campaign = str(campaign_conversions.idxmax())
    else:
        top_campaign = "N/A"

    kpis = {
        "total_budget_spent": round(total_budget_spent, 2),
        "total_conversions": total_conversions,
        "avg_conversion_rate": round(avg_conversion_rate, 2),
        "best_channel": best_channel,
        "roi_by_channel": roi_by_channel,
        "cost_per_conversion": round(cost_per_conversion, 2),
        "top_campaign": top_campaign,
    }

    logger.info("KPIs marketing calculés : %s", kpis)
    return kpis
