"""
Analyseur support client — calcul des KPIs du service client.

Analyse le dataset 03_customer_support.csv et produit les indicateurs
clés de performance du support client pour une PME tunisienne.
"""

import logging
from typing import Any, Dict

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

logger = logging.getLogger(__name__)


def analyze(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calcule les KPIs support client à partir du DataFrame des tickets.

    KPIs calculés :
        - avg_satisfaction      : score de satisfaction moyen (1-5)
        - avg_resolution_hours  : temps moyen de résolution (heures)
        - high_churn_rate       : % de tickets avec churn_risk = "high"
        - top_issue_type        : type de problème le plus fréquent
        - sla_compliance        : % tickets résolus en moins de 24h
        - satisfaction_trend    : tendance de la satisfaction ("hausse" | "baisse" | "stable")

    Args:
        df: DataFrame avec colonnes date, ticket_id, issue_type,
            resolution_hours, satisfaction_score, churn_risk.

    Returns:
        Dictionnaire contenant tous les KPIs support client.
    """
    logger.info("Analyse support client en cours — %d lignes", len(df))

    # Vérification des colonnes requises
    required_cols = {
        "date", "ticket_id", "issue_type",
        "resolution_hours", "satisfaction_score", "churn_risk"
    }
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Colonnes manquantes dans le dataset support : {missing}")

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

    # Score de satisfaction moyen (1-5)
    avg_satisfaction = float(df["satisfaction_score"].mean())

    # Temps moyen de résolution (heures)
    avg_resolution_hours = float(df["resolution_hours"].mean())

    # ================================================================
    # Taux de churn risk élevé (%)
    # ================================================================
    total_tickets = len(df)
    high_churn_count = int((df["churn_risk"].str.lower() == "high").sum())

    if total_tickets > 0:
        high_churn_rate = (high_churn_count / total_tickets) * 100
    else:
        high_churn_rate = 0.0

    # ================================================================
    # Type de problème le plus fréquent
    # ================================================================
    issue_counts = df["issue_type"].value_counts()
    if len(issue_counts) > 0:
        top_issue_type = str(issue_counts.index[0])
    else:
        top_issue_type = "N/A"

    # ================================================================
    # SLA Compliance : % tickets résolus en moins de 24h
    # ================================================================
    sla_threshold_hours = 24.0
    resolved_within_sla = int((df["resolution_hours"] <= sla_threshold_hours).sum())

    if total_tickets > 0:
        sla_compliance = (resolved_within_sla / total_tickets) * 100
    else:
        sla_compliance = 0.0

    # ================================================================
    # Tendance de la satisfaction
    # ================================================================
    satisfaction_trend = _calculate_satisfaction_trend(df)

    kpis = {
        "avg_satisfaction": round(avg_satisfaction, 2),
        "avg_resolution_hours": round(avg_resolution_hours, 2),
        "high_churn_rate": round(high_churn_rate, 2),
        "top_issue_type": top_issue_type,
        "sla_compliance": round(sla_compliance, 2),
        "satisfaction_trend": satisfaction_trend,
    }

    logger.info("KPIs support client calculés : %s", kpis)
    return kpis


def _calculate_satisfaction_trend(df: pd.DataFrame) -> str:
    """
    Calcule la tendance de la satisfaction client via régression linéaire.

    Agrège les scores de satisfaction par mois, puis applique une
    régression linéaire pour déterminer la tendance.

    Args:
        df: DataFrame avec colonnes 'date' et 'satisfaction_score'.

    Returns:
        "hausse" si la satisfaction augmente, "baisse" si elle diminue,
        "stable" sinon.
    """
    if len(df) < 2:
        return "stable"

    # Agrégation mensuelle
    df = df.copy()
    df["month"] = df["date"].dt.to_period("M")
    monthly_satisfaction = df.groupby("month")["satisfaction_score"].mean()

    if len(monthly_satisfaction) < 2:
        return "stable"

    # Régression linéaire
    X = np.arange(len(monthly_satisfaction)).reshape(-1, 1)
    y = monthly_satisfaction.values.reshape(-1, 1)

    model = LinearRegression()
    model.fit(X, y)

    slope = model.coef_[0][0]
    mean_value = np.mean(y)

    if mean_value == 0:
        return "stable"

    # Pente relative (en pourcentage par mois)
    relative_slope = (slope / mean_value) * 100

    # Seuils : > 0.5% par mois = hausse, < -0.5% = baisse
    if relative_slope > 0.5:
        return "hausse"
    elif relative_slope < -0.5:
        return "baisse"
    else:
        return "stable"
