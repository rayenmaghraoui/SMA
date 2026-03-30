"""
Agent de rapport — structuration du rapport final.

Cet agent compile tous les résultats du pipeline dans un rapport
JSON structuré et complet.

Entrée : tout l'état (kpis, anomalies, interpretation, recommendations, rag_context)
Sortie : state["report"]
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

from backend.agents.state import AgentState

logger = logging.getLogger(__name__)


def _build_executive_summary(
    kpis: Dict[str, Any],
    anomalies: List[Dict],
    recommendations: List[Dict]
) -> str:
    """
    Génère un résumé exécutif concis pour le rapport.

    Args:
        kpis: KPIs par domaine.
        anomalies: Liste des anomalies.
        recommendations: Liste des recommandations.

    Returns:
        Résumé exécutif en français.
    """
    summary_parts = []

    # Analyse financière
    finance = kpis.get("finance", {})
    if finance:
        revenue = finance.get("revenue_total", 0)
        margin = finance.get("profit_margin", 0)
        trend = finance.get("trend", "stable")

        trend_text = {
            "hausse": "en croissance",
            "baisse": "en déclin",
            "stable": "stable"
        }.get(trend, "non déterminée")

        summary_parts.append(
            f"L'entreprise a réalisé un chiffre d'affaires de {revenue:,.0f} TND "
            f"avec une marge de {margin:.1f}%. La tendance est {trend_text}."
        )

    # Performance marketing
    marketing = kpis.get("marketing", {})
    if marketing:
        conv_rate = marketing.get("avg_conversion_rate", 0)
        best_channel = marketing.get("best_channel", "N/A")

        summary_parts.append(
            f"Le taux de conversion marketing moyen est de {conv_rate:.2f}%, "
            f"avec le canal '{best_channel}' comme meilleur performeur."
        )

    # Service client
    support = kpis.get("support", {})
    if support:
        satisfaction = support.get("avg_satisfaction", 0)
        churn = support.get("high_churn_rate", 0)

        satisfaction_level = "bon" if satisfaction >= 4 else "moyen" if satisfaction >= 3 else "faible"

        summary_parts.append(
            f"La satisfaction client est {satisfaction_level} ({satisfaction:.1f}/5) "
            f"avec un risque de churn de {churn:.1f}%."
        )

    # Anomalies
    if anomalies:
        summary_parts.append(
            f"{len(anomalies)} anomalie(s) ont été détectées et nécessitent attention."
        )

    # Recommandations prioritaires
    high_priority = [r for r in recommendations if r.get("priorite", 5) <= 2]
    if high_priority:
        titles = [r.get("titre", "") for r in high_priority]
        summary_parts.append(
            f"Actions prioritaires : {', '.join(titles)}."
        )

    return " ".join(summary_parts)


def _extract_rag_sources(rag_context: List[Dict]) -> List[Dict[str, str]]:
    """
    Extrait les sources du contexte RAG pour le rapport.

    Args:
        rag_context: Contexte RAG complet.

    Returns:
        Liste simplifiée des sources avec nom et section.
    """
    sources = []
    seen = set()

    for ctx in rag_context:
        source = ctx.get("source", "")
        section = ctx.get("section", "")
        key = f"{source}:{section}"

        if key not in seen and source:
            seen.add(key)
            sources.append({
                "document": source,
                "section": section,
                "pertinence": ctx.get("score", 0),
            })

    return sources


def _format_kpis_for_report(kpis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Formate les KPIs pour le rapport avec des labels français.

    Args:
        kpis: KPIs bruts.

    Returns:
        KPIs formatés avec métadonnées.
    """
    formatted = {}

    # Finance
    finance = kpis.get("finance", {})
    if finance:
        formatted["finance"] = {
            "titre": "Performance Financière",
            "indicateurs": [
                {
                    "label": "Chiffre d'affaires total",
                    "valeur": finance.get("revenue_total", 0),
                    "unite": "TND",
                    "format": "currency",
                },
                {
                    "label": "Bénéfice total",
                    "valeur": finance.get("profit_total", 0),
                    "unite": "TND",
                    "format": "currency",
                },
                {
                    "label": "Marge bénéficiaire",
                    "valeur": finance.get("profit_margin", 0),
                    "unite": "%",
                    "format": "percent",
                },
                {
                    "label": "Croissance moyenne",
                    "valeur": finance.get("avg_growth_rate", 0),
                    "unite": "%",
                    "format": "percent",
                },
                {
                    "label": "Tendance",
                    "valeur": finance.get("trend", "N/A"),
                    "unite": "",
                    "format": "text",
                },
            ],
            "meilleur_mois": finance.get("best_month", "N/A"),
            "pire_mois": finance.get("worst_month", "N/A"),
        }

    # Marketing
    marketing = kpis.get("marketing", {})
    if marketing:
        formatted["marketing"] = {
            "titre": "Performance Marketing",
            "indicateurs": [
                {
                    "label": "Budget dépensé",
                    "valeur": marketing.get("total_budget_spent", 0),
                    "unite": "TND",
                    "format": "currency",
                },
                {
                    "label": "Conversions totales",
                    "valeur": marketing.get("total_conversions", 0),
                    "unite": "",
                    "format": "number",
                },
                {
                    "label": "Taux de conversion",
                    "valeur": marketing.get("avg_conversion_rate", 0),
                    "unite": "%",
                    "format": "percent",
                },
                {
                    "label": "Coût par conversion",
                    "valeur": marketing.get("cost_per_conversion", 0),
                    "unite": "TND",
                    "format": "currency",
                },
            ],
            "meilleur_canal": marketing.get("best_channel", "N/A"),
            "meilleure_campagne": marketing.get("top_campaign", "N/A"),
            "roi_par_canal": marketing.get("roi_by_channel", {}),
        }

    # Support
    support = kpis.get("support", {})
    if support:
        formatted["support"] = {
            "titre": "Service Client",
            "indicateurs": [
                {
                    "label": "Satisfaction moyenne",
                    "valeur": support.get("avg_satisfaction", 0),
                    "unite": "/5",
                    "format": "rating",
                },
                {
                    "label": "Temps de résolution",
                    "valeur": support.get("avg_resolution_hours", 0),
                    "unite": "heures",
                    "format": "duration",
                },
                {
                    "label": "Taux de churn élevé",
                    "valeur": support.get("high_churn_rate", 0),
                    "unite": "%",
                    "format": "percent",
                },
                {
                    "label": "Conformité SLA",
                    "valeur": support.get("sla_compliance", 0),
                    "unite": "%",
                    "format": "percent",
                },
            ],
            "probleme_frequent": support.get("top_issue_type", "N/A"),
        }

    return formatted


def report_agent(state: AgentState) -> AgentState:
    """
    Agent de génération du rapport final.

    Cet agent :
    1. Compile tous les résultats du pipeline
    2. Structure le rapport en JSON
    3. Génère un résumé exécutif
    4. Remplit state["report"]

    Args:
        state: État courant du pipeline.

    Returns:
        État mis à jour avec le rapport complet.
    """
    logger.info("[Report Agent] Génération du rapport final")

    try:
        kpis = state.get("kpis", {})
        anomalies = state.get("anomalies", [])
        interpretation = state.get("interpretation", "")
        recommendations = state.get("recommendations", [])
        rag_context = state.get("rag_context", [])
        errors = state.get("errors", [])

        # Générer le résumé exécutif
        resume_executif = _build_executive_summary(
            kpis, anomalies, recommendations
        )

        # Formater les KPIs
        kpis_formatted = _format_kpis_for_report(kpis)

        # Extraire les sources RAG
        sources_rag = _extract_rag_sources(rag_context)

        # Structurer le rapport final
        report = {
            "resume_executif": resume_executif,
            "kpis": kpis_formatted,
            "anomalies": {
                "total": len(anomalies),
                "details": anomalies,
            },
            "interpretation": interpretation,
            "recommendations": recommendations,
            "sources_rag": sources_rag,
            "metadata": {
                "date_generation": datetime.now().isoformat(),
                "version": "1.0",
                "pipeline_errors": errors,
                "nombre_sources": len(sources_rag),
            },
        }

        logger.info("[Report Agent] Rapport généré avec succès")
        logger.debug(
            "[Report Agent] Contenu: %d KPIs, %d anomalies, %d recommandations",
            len(kpis_formatted),
            len(anomalies),
            len(recommendations)
        )

        return {
            **state,
            "report": report,
            "current_step": "report_completed",
        }

    except Exception as e:
        logger.exception("[Report Agent] Erreur : %s", e)

        # Générer un rapport minimal en cas d'erreur
        error_report = {
            "resume_executif": "Erreur lors de la génération du rapport.",
            "kpis": state.get("kpis", {}),
            "anomalies": {"total": 0, "details": []},
            "interpretation": state.get("interpretation", ""),
            "recommendations": state.get("recommendations", []),
            "sources_rag": [],
            "metadata": {
                "date_generation": datetime.now().isoformat(),
                "version": "1.0",
                "pipeline_errors": state.get("errors", []) + [str(e)],
                "error": True,
            },
        }

        return {
            **state,
            "report": error_report,
            "errors": state.get("errors", []) + [f"Report Agent: {str(e)}"],
            "current_step": "report_error",
        }
