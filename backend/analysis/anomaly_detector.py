"""
Détecteur d'anomalies — méthode IQR (Interquartile Range).

Détecte les valeurs aberrantes dans les colonnes numériques des trois
datasets du projet (finance, marketing, support).
"""

import logging
from typing import Any, Dict, List

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def detect(datasets: Dict[str, pd.DataFrame]) -> List[Dict[str, Any]]:
    """
    Détecte les anomalies dans les trois datasets via la méthode IQR.

    La méthode IQR (Interquartile Range) identifie comme anomalie toute
    valeur X où :
        - X < Q1 - 1.5 * IQR  → anomalie basse ("low")
        - X > Q3 + 1.5 * IQR  → anomalie haute ("high")

    Avec :
        - Q1 = premier quartile (25e percentile)
        - Q3 = troisième quartile (75e percentile)
        - IQR = Q3 - Q1

    Args:
        datasets: Dictionnaire {"finance": df, "marketing": df, "support": df}.

    Returns:
        Liste de dictionnaires décrivant chaque anomalie détectée :
        {
            "dataset": str,    # nom du dataset
            "colonne": str,    # nom de la colonne
            "index": int,      # index de la ligne
            "valeur": float,   # valeur aberrante
            "type": str        # "high" ou "low"
        }
    """
    logger.info("Détection des anomalies en cours — %d datasets", len(datasets))

    anomalies: List[Dict[str, Any]] = []

    for dataset_name, df in datasets.items():
        logger.debug("Analyse du dataset '%s' — %d lignes", dataset_name, len(df))

        # Sélectionner uniquement les colonnes numériques
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

        for col in numeric_cols:
            col_anomalies = _detect_iqr_anomalies(df, col, dataset_name)
            anomalies.extend(col_anomalies)

    logger.info("Détection terminée — %d anomalies trouvées", len(anomalies))
    return anomalies


def _detect_iqr_anomalies(
    df: pd.DataFrame,
    column: str,
    dataset_name: str
) -> List[Dict[str, Any]]:
    """
    Applique la méthode IQR sur une colonne spécifique.

    Args:
        df: DataFrame contenant la colonne.
        column: Nom de la colonne à analyser.
        dataset_name: Nom du dataset (pour le rapport).

    Returns:
        Liste d'anomalies pour cette colonne.
    """
    values = df[column].dropna()

    if len(values) < 4:
        # Pas assez de données pour calculer les quartiles
        return []

    # Calcul des quartiles et de l'IQR
    q1 = float(values.quantile(0.25))
    q3 = float(values.quantile(0.75))
    iqr = q3 - q1

    # Seuils
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    anomalies: List[Dict[str, Any]] = []

    for idx, value in df[column].items():
        if pd.isna(value):
            continue

        anomaly_type = None

        if value < lower_bound:
            anomaly_type = "low"
        elif value > upper_bound:
            anomaly_type = "high"

        if anomaly_type:
            anomalies.append({
                "dataset": dataset_name,
                "colonne": column,
                "index": int(idx),
                "valeur": round(float(value), 2),
                "type": anomaly_type,
            })

    if anomalies:
        logger.debug(
            "[%s.%s] %d anomalies détectées (seuils: %.2f — %.2f)",
            dataset_name, column, len(anomalies), lower_bound, upper_bound
        )

    return anomalies
