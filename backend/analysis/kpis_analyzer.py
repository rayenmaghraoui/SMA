"""
Analyseur financier — KPIs depuis 05_kpis_globaux.csv (format Indicateur/Valeur).
"""

import logging
from typing import Any, Dict

import pandas as pd

logger = logging.getLogger(__name__)


def analyze(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calcule les KPIs financiers à partir du DataFrame kpis_globaux.

    Le fichier 05_kpis_globaux.csv a un format clé-valeur :
        Indicateur | Valeur
    Les colonnes après normalisation sont : indicateur, valeur.

    Args:
        df: DataFrame avec colonnes indicateur, valeur.

    Returns:
        Dictionnaire contenant tous les KPIs financiers.
    """
    logger.info("Analyse financière (kpis_globaux) en cours — %d lignes", len(df))

    required_cols = {"indicateur", "valeur"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Colonnes manquantes dans le dataset kpis : {missing}")

    def get_val(name: str) -> float:
        """Extrait la valeur d'un indicateur par son nom."""
        row = df[df["indicateur"].str.strip() == name]
        return float(row["valeur"].values[0]) if len(row) > 0 else 0.0

    revenue_total = get_val("CA Total (TND)")
    profit_total = get_val("Profit Total (TND)")
    profit_margin = get_val("Marge Beneficiaire (%)")
    nb_transactions = int(get_val("Nb Transactions"))
    panier_moyen = get_val("Panier Moyen (TND)")
    quantite_totale = int(get_val("Quantite Totale Vendue"))
    nb_clients = int(get_val("Nb Clients Uniques"))
    ca_moyen_client = get_val("CA Moyen par Client (TND)")

    kpis = {
        "revenue_total": round(revenue_total, 2),
        "profit_total": round(profit_total, 2),
        "profit_margin": round(profit_margin, 2),
        "nb_transactions": nb_transactions,
        "panier_moyen": round(panier_moyen, 2),
        "quantite_totale": quantite_totale,
        "nb_clients": nb_clients,
        "ca_moyen_client": round(ca_moyen_client, 2),
        # Champs conservés pour compatibilité avec report_agent
        "avg_growth_rate": 0.0,
        "trend": "stable",
        "best_period": "N/A",
        "worst_period": "N/A",
        "revenue_volatility": 0.0,
    }

    logger.info("KPIs financiers calculés : CA=%.0f TND, Marge=%.1f%%", revenue_total, profit_margin)
    return kpis
