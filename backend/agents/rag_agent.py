"""
Agent RAG — recherche dans les guides tunisiens.

Cet agent construit une requête intelligente à partir des KPIs et anomalies
détectés, puis recherche les passages pertinents dans la base de connaissances
(guides d'entreprises tunisiennes).

Entrée : state["kpis"], state["anomalies"]
Sortie : state["rag_context"]
"""

import logging
from typing import List, Dict, Any

from backend.agents.state import AgentState
from backend.rag.retriever import search

logger = logging.getLogger(__name__)


def _build_search_query(kpis: Dict[str, Any], anomalies: List[Dict]) -> str:
    """
    Construit une requête de recherche intelligente.

    Analyse les KPIs et anomalies pour identifier les thèmes clés à rechercher
    dans les guides tunisiens.

    Args:
        kpis: Dictionnaire des KPIs par domaine (finance, marketing, support).
        anomalies: Liste des anomalies détectées.

    Returns:
        Requête textuelle optimisée pour la recherche sémantique.
    """
    query_parts: List[str] = []

    # Analyse des KPIs financiers
    finance_kpis = kpis.get("finance", {})
    if finance_kpis:
        # Vérifier la tendance
        trend = finance_kpis.get("trend", "")
        if trend == "baisse":
            query_parts.append("baisse chiffre d'affaires")
            query_parts.append("améliorer rentabilité")

        # Vérifier la marge
        profit_margin = finance_kpis.get("profit_margin", 0)
        if profit_margin < 10:
            query_parts.append("marge bénéficiaire faible")
            query_parts.append("réduction des charges")
        elif profit_margin > 20:
            query_parts.append("investissement croissance")

        # Volatilité élevée
        volatility = finance_kpis.get("revenue_volatility", 0)
        if volatility > 0:
            avg_revenue = finance_kpis.get("revenue_total", 0) / 12 if finance_kpis.get("revenue_total") else 0
            if avg_revenue > 0 and volatility / avg_revenue > 0.3:
                query_parts.append("stabilité financière")
                query_parts.append("gestion trésorerie")

    # Analyse des KPIs marketing
    marketing_kpis = kpis.get("marketing", {})
    if marketing_kpis:
        # Taux de conversion faible
        avg_conversion = marketing_kpis.get("avg_conversion_rate", 0)
        if avg_conversion < 5:
            query_parts.append("améliorer conversion marketing")
            query_parts.append("optimisation campagnes publicitaires")

        # Coût par conversion élevé
        cost_per_conv = marketing_kpis.get("cost_per_conversion", 0)
        if cost_per_conv > 50:
            query_parts.append("réduire coût acquisition client")

    # Analyse des KPIs support
    support_kpis = kpis.get("support", {})
    if support_kpis:
        # Satisfaction faible
        avg_satisfaction = support_kpis.get("avg_satisfaction", 0)
        if avg_satisfaction < 3.5:
            query_parts.append("améliorer satisfaction client")
            query_parts.append("qualité service client")

        # Temps de résolution élevé
        avg_resolution = support_kpis.get("avg_resolution_hours", 0)
        if avg_resolution > 24:
            query_parts.append("optimiser temps résolution tickets")

        # Risque de churn élevé
        high_churn = support_kpis.get("high_churn_rate", 0)
        if high_churn > 20:
            query_parts.append("fidélisation clients Tunisie")
            query_parts.append("réduire attrition clients")

    # Ajouter les domaines concernés par les anomalies
    anomaly_domains = set()
    for anomaly in anomalies:
        dataset = anomaly.get("dataset", "")
        if "finance" in dataset.lower():
            anomaly_domains.add("gestion financière PME Tunisie")
        elif "marketing" in dataset.lower():
            anomaly_domains.add("stratégie marketing digital Tunisie")
        elif "support" in dataset.lower():
            anomaly_domains.add("service client entreprise tunisienne")

    query_parts.extend(anomaly_domains)

    # Construire la requête finale
    if not query_parts:
        # Requête par défaut si aucun problème détecté
        query_parts = [
            "gestion entreprise tunisienne",
            "bonnes pratiques PME Tunisie",
        ]

    # Joindre les éléments uniques
    unique_parts = list(dict.fromkeys(query_parts))  # Préserve l'ordre
    query = " ".join(unique_parts[:6])  # Limiter à 6 termes max

    return query


def _build_targeted_queries(kpis: Dict[str, Any], anomalies: List[Dict]) -> List[str]:
    """
    Construit plusieurs requêtes ciblées pour une couverture complète.

    Args:
        kpis: Dictionnaire des KPIs.
        anomalies: Liste des anomalies.

    Returns:
        Liste de requêtes à exécuter.
    """
    queries: List[str] = []

    # Requête principale
    main_query = _build_search_query(kpis, anomalies)
    queries.append(main_query)

    # Requêtes par domaine si des problèmes sont détectés
    finance_kpis = kpis.get("finance", {})
    if finance_kpis.get("trend") == "baisse" or finance_kpis.get("profit_margin", 100) < 10:
        queries.append("gestion financière entreprise Tunisie fiscalité TVA")

    marketing_kpis = kpis.get("marketing", {})
    if marketing_kpis.get("avg_conversion_rate", 100) < 5:
        queries.append("marketing digital PME campagne ROI conversion")

    support_kpis = kpis.get("support", {})
    if support_kpis.get("avg_satisfaction", 5) < 3.5:
        queries.append("relation client qualité service fidélisation")

    return queries[:3]  # Maximum 3 requêtes


def rag_agent(state: AgentState) -> AgentState:
    """
    Agent RAG — recherche contextuelle dans les guides tunisiens.

    Cet agent :
    1. Analyse les KPIs et anomalies pour identifier les problèmes
    2. Construit une requête de recherche intelligente
    3. Recherche les passages pertinents dans ChromaDB
    4. Retourne les résultats dans state["rag_context"]

    Args:
        state: État courant du pipeline.

    Returns:
        État mis à jour avec rag_context rempli.
    """
    logger.info("[RAG Agent] Démarrage de la recherche contextuelle")

    try:
        kpis = state.get("kpis", {})
        anomalies = state.get("anomalies", [])

        # Construire les requêtes ciblées
        queries = _build_targeted_queries(kpis, anomalies)
        logger.debug("[RAG Agent] Requêtes générées : %s", queries)

        # Exécuter les recherches et fusionner les résultats
        all_results: List[Dict[str, Any]] = []
        seen_contents: set = set()

        for query in queries:
            logger.debug("[RAG Agent] Recherche : '%s'", query[:60])
            results = search(query, k=3)

            for result in results:
                # Éviter les doublons (même contenu)
                content_hash = hash(result["page_content"][:100])
                if content_hash not in seen_contents:
                    seen_contents.add(content_hash)
                    all_results.append(result)

        # Trier par score décroissant et garder les top résultats
        all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
        top_results = all_results[:5]  # Garder les 5 meilleurs

        logger.info(
            "[RAG Agent] %d passages pertinents trouvés",
            len(top_results)
        )

        # Log des sources trouvées
        sources = set(r["source"] for r in top_results)
        logger.debug("[RAG Agent] Sources : %s", sources)

        return {
            **state,
            "rag_context": top_results,
            "current_step": "rag_completed",
        }

    except Exception as e:
        logger.exception("[RAG Agent] Erreur : %s", e)
        return {
            **state,
            "rag_context": [],
            "errors": state.get("errors", []) + [f"RAG Agent: {str(e)}"],
            "current_step": "rag_error",
        }
