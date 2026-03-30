"""
Agent d'analyse des donn\u00e9es.

Premier agent du pipeline LangGraph. Charge les datasets, calcule les KPIs
via les trois analyzers (finance, marketing, support) et d\u00e9tecte les anomalies.
"""

import logging
from typing import Any, Dict

from backend.agents.state import AgentState
from backend.analysis import loader
from backend.analysis import finance_analyzer
from backend.analysis import marketing_analyzer
from backend.analysis import support_analyzer
from backend.analysis import anomaly_detector

logger = logging.getLogger(__name__)


def analysis_agent(state: AgentState) -> AgentState:
    """
    Agent d'analyse des donn\u00e9es.

    \u00c9tape 1 du pipeline :
        1. Charge les trois datasets CSV (finance, marketing, support)
        2. Calcule les KPIs de chaque domaine
        3. D\u00e9tecte les anomalies via la m\u00e9thode IQR
        4. Met \u00e0 jour l'\u00e9tat avec les r\u00e9sultats

    Args:
        state: \u00c9tat actuel du pipeline LangGraph.

    Returns:
        \u00c9tat mis \u00e0 jour avec les KPIs et anomalies.
    """
    logger.info("=== D\u00e9marrage de l'Analysis Agent ===")

    errors = list(state.get("errors", []))
    kpis: Dict[str, Any] = {}
    anomalies = []

    try:
        # ============================================================
        # \u00c9tape 1 : Chargement des datasets
        # ============================================================
        logger.info("Chargement des datasets...")

        # V\u00e9rifier si des donn\u00e9es brutes sont d\u00e9j\u00e0 dans l'\u00e9tat
        raw_data = state.get("raw_data", {})

        if raw_data and "finance" in raw_data:
            # Utiliser les donn\u00e9es d\u00e9j\u00e0 charg\u00e9es (cas upload personnalis\u00e9)
            logger.info("Utilisation des donn\u00e9es pr\u00e9-charg\u00e9es dans l'\u00e9tat")
            datasets = _deserialize_datasets(raw_data)
        else:
            # Charger les donn\u00e9es par d\u00e9faut
            datasets = loader.load_datasets()

        logger.info(
            "Datasets charg\u00e9s \u2014 finance: %d, marketing: %d, support: %d lignes",
            len(datasets["finance"]),
            len(datasets["marketing"]),
            len(datasets["support"]),
        )

        # ============================================================
        # \u00c9tape 2 : Calcul des KPIs par domaine
        # ============================================================
        logger.info("Calcul des KPIs financiers...")
        kpis["finance"] = finance_analyzer.analyze(datasets["finance"])

        logger.info("Calcul des KPIs marketing...")
        kpis["marketing"] = marketing_analyzer.analyze(datasets["marketing"])

        logger.info("Calcul des KPIs support client...")
        kpis["support"] = support_analyzer.analyze(datasets["support"])

        # ============================================================
        # \u00c9tape 3 : D\u00e9tection des anomalies
        # ============================================================
        logger.info("D\u00e9tection des anomalies...")
        anomalies = anomaly_detector.detect(datasets)
        logger.info("%d anomalies d\u00e9tect\u00e9es", len(anomalies))

    except FileNotFoundError as e:
        error_msg = f"Fichier introuvable : {e}"
        logger.error(error_msg)
        errors.append(error_msg)

    except ValueError as e:
        error_msg = f"Erreur de validation : {e}"
        logger.error(error_msg)
        errors.append(error_msg)

    except Exception as e:
        error_msg = f"Erreur inattendue dans analysis_agent : {e}"
        logger.exception(error_msg)
        errors.append(error_msg)

    # Retourner l'\u00e9tat mis \u00e0 jour
    logger.info("=== Analysis Agent termin\u00e9 ===")

    return {
        **state,
        "kpis": kpis,
        "anomalies": anomalies,
        "errors": errors,
        "current_step": "analysis_complete",
    }


def _deserialize_datasets(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convertit les donn\u00e9es brutes (dict/list) en DataFrames Pandas.

    Args:
        raw_data: Dictionnaire contenant les donn\u00e9es s\u00e9rialis\u00e9es.

    Returns:
        Dictionnaire avec les DataFrames pour chaque dataset.
    """
    import pandas as pd

    datasets = {}

    for key in ["finance", "marketing", "support"]:
        if key in raw_data:
            data = raw_data[key]
            if isinstance(data, pd.DataFrame):
                datasets[key] = data
            elif isinstance(data, dict):
                datasets[key] = pd.DataFrame(data)
            elif isinstance(data, list):
                datasets[key] = pd.DataFrame(data)
            else:
                raise ValueError(f"Format non support\u00e9 pour {key}: {type(data)}")

    return datasets
