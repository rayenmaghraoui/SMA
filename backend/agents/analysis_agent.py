"""
Agent d'analyse des données.

Premier agent du pipeline LangGraph. Charge les 5 datasets, calcule les KPIs
via les analyseurs (finance/kpis, marketing/canaux, categories) et les analyses
inline ventes/régions, puis détecte les anomalies.
"""

import logging
from typing import Any, Dict

from backend.agents.state import AgentState
from backend.analysis import loader
from backend.analysis import kpis_analyzer
from backend.analysis import canaux_analyzer
from backend.analysis import categories_analyzer
from backend.analysis import anomaly_detector

logger = logging.getLogger(__name__)


def analysis_agent(state: AgentState) -> AgentState:
    """
    Agent d'analyse des données.

    Étape 1 du pipeline :
        1. Charge les 5 datasets CSV (ventes, regions, categories, canaux, kpis)
        2. Calcule les KPIs de chaque domaine
        3. Détecte les anomalies via la méthode IQR
        4. Met à jour l'état avec les résultats

    Args:
        state: État actuel du pipeline LangGraph.

    Returns:
        État mis à jour avec les KPIs et anomalies.
    """
    logger.info("=== Démarrage de l'Analysis Agent ===")

    errors = list(state.get("errors", []))
    kpis: Dict[str, Any] = {}
    anomalies = []

    try:
        # ============================================================
        # Étape 1 : Chargement des datasets
        # ============================================================
        logger.info("Chargement des datasets...")

        raw_data = state.get("raw_data", {})

        if raw_data and "ventes" in raw_data:
            # Utiliser les données pré-chargées (cas upload personnalisé)
            logger.info("Utilisation des données pré-chargées dans l'état")
            datasets = _deserialize_datasets(raw_data)
        else:
            # Charger les données par défaut depuis les fichiers CSV
            datasets = loader.load_datasets()

        logger.info(
            "Datasets chargés — ventes: %d, regions: %d, categories: %d, "
            "canaux: %d, kpis: %d lignes",
            len(datasets["ventes"]),
            len(datasets["regions"]),
            len(datasets["categories"]),
            len(datasets["canaux"]),
            len(datasets["kpis"]),
        )

        # ============================================================
        # Étape 2 : Calcul des KPIs par domaine
        # ============================================================

        logger.info("Calcul des KPIs financiers (dynamique depuis ventes)...")
        kpis["finance"] = kpis_analyzer.analyze(
            datasets["kpis"],
            df_ventes=datasets.get("ventes")
        )

        logger.info("Calcul des KPIs canaux marketing...")
        kpis["marketing"] = canaux_analyzer.analyze(datasets["canaux"])

        logger.info("Calcul des KPIs catégories produits...")
        kpis["categories"] = categories_analyzer.analyze(datasets["categories"])

        logger.info("Calcul des KPIs ventes...")
        kpis["ventes"] = _analyze_ventes(datasets["ventes"])

        logger.info("Calcul des KPIs régionaux...")
        kpis["regions"] = _analyze_regions(datasets["regions"])

        # ============================================================
        # Étape 3 : Détection des anomalies
        # ============================================================
        logger.info("Détection des anomalies...")
        anomalies = anomaly_detector.detect(datasets)
        logger.info("%d anomalies détectées", len(anomalies))

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

    logger.info("=== Analysis Agent terminé ===")

    return {
        **state,
        "kpis": kpis,
        "anomalies": anomalies,
        "errors": errors,
        "current_step": "analysis_complete",
    }


def _analyze_ventes(df: Any) -> Dict[str, Any]:
    """
    Calcule les KPIs agrégés à partir du dataset ventes.

    Args:
        df: DataFrame ventes (invoice_id, product_name, category, quantity,
            unit_price_tnd, revenue_tnd, customer_id, customer_region,
            sale_date, sales_channel, payment_method, estimated_profit).

    Returns:
        Dictionnaire de KPIs ventes.
    """
    total_revenue = float(df["revenue_tnd"].sum())
    total_quantity = int(df["quantity"].sum())

    # Meilleur produit par revenu
    prod_rev = df.groupby("product_name")["revenue_tnd"].sum()
    best_product = str(prod_rev.idxmax()) if len(prod_rev) > 0 else "N/A"

    # Meilleure région par revenu
    region_rev = df.groupby("customer_region")["revenue_tnd"].sum()
    best_region = str(region_rev.idxmax()) if len(region_rev) > 0 else "N/A"

    # Meilleur canal par revenu
    channel_rev = df.groupby("sales_channel")["revenue_tnd"].sum()
    best_channel = str(channel_rev.idxmax()) if len(channel_rev) > 0 else "N/A"

    # Revenu moyen par commande
    avg_revenue_per_order = total_revenue / len(df) if len(df) > 0 else 0.0

    return {
        "total_revenue": round(total_revenue, 2),
        "total_quantity": total_quantity,
        "best_product": best_product,
        "best_region": best_region,
        "best_channel": best_channel,
        "avg_revenue_per_order": round(avg_revenue_per_order, 2),
    }


def _analyze_regions(df: Any) -> Dict[str, Any]:
    """
    Calcule les KPIs agrégés à partir du dataset régional.

    Args:
        df: DataFrame regions (customer_region, ca_total, profit_total,
            nb_transactions, panier_moyen).

    Returns:
        Dictionnaire de KPIs régionaux.
    """
    total_revenue = float(df["ca_total"].sum())
    total_orders = int(df["nb_transactions"].sum())
    avg_ticket_global = float(df["panier_moyen"].mean())

    # Meilleure région par CA
    top_region = str(df.loc[df["ca_total"].idxmax(), "customer_region"]) if len(df) > 0 else "N/A"

    # CA par région
    revenue_by_region: Dict[str, float] = {
        str(row["customer_region"]): round(float(row["ca_total"]), 2)
        for _, row in df.iterrows()
    }

    return {
        "total_revenue": round(total_revenue, 2),
        "total_orders": total_orders,
        "avg_ticket_global": round(avg_ticket_global, 2),
        "top_region": top_region,
        "revenue_by_region": revenue_by_region,
    }


def _deserialize_datasets(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convertit les données brutes (dict/list) en DataFrames Pandas.

    Args:
        raw_data: Dictionnaire contenant les données sérialisées.

    Returns:
        Dictionnaire avec les DataFrames pour chaque dataset.
    """
    import pandas as pd

    datasets = {}

    for key in ["ventes", "regions", "categories", "canaux", "kpis"]:
        if key in raw_data:
            data = raw_data[key]
            if isinstance(data, pd.DataFrame):
                datasets[key] = data
            elif isinstance(data, dict):
                datasets[key] = pd.DataFrame(data)
            elif isinstance(data, list):
                datasets[key] = pd.DataFrame(data)
            else:
                raise ValueError(f"Format non supporté pour {key}: {type(data)}")

    return datasets
