"""
Agent de recommandation — génération de conseils stratégiques.

Cet agent utilise l'interprétation LLM et le contexte RAG pour
générer 5 recommandations priorisées et actionnables.

Entrée : state["interpretation"], state["rag_context"], state["kpis"]
Sortie : state["recommendations"]
"""

import logging
import json
import re
from typing import Any, Dict, List

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from backend.agents.state import AgentState
from backend.config import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_MODEL,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
)

logger = logging.getLogger(__name__)

# Prompt système pour les recommandations
SYSTEM_PROMPT = """Tu es un consultant stratégique spécialisé dans les PME tunisiennes.

CONTEXTE :
- Tu fournis des recommandations concrètes et actionnables.
- Tes conseils tiennent compte du contexte économique tunisien.
- Tu connais les organismes locaux (BFPME, SOTUGAR, APII).
- Les montants sont en Dinars Tunisiens (TND).

FORMAT OBLIGATOIRE :
Tu dois retourner EXACTEMENT un tableau JSON avec 5 recommandations.
Chaque recommandation a cette structure :
{
  "priorite": 1 à 5 (1 = plus urgent),
  "titre": "titre court",
  "action": "description détaillée de l'action à mener",
  "impact": "impact attendu (chiffré si possible)",
  "source": "guide ou source de la recommandation"
}

RÈGLES :
- Exactement 5 recommandations
- Priorisées de 1 (urgent) à 5 (moins urgent)
- Actions concrètes, pas de généralités
- Impacts mesurables quand possible
- Adapté au contexte tunisien

RETOURNE UNIQUEMENT LE TABLEAU JSON, sans texte avant ou après.
"""


def _get_llm() -> ChatOpenAI:
    """Retourne une instance du LLM configuré."""
    return ChatOpenAI(
        base_url=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_API_KEY,
        model=AZURE_OPENAI_MODEL,
        temperature=LLM_TEMPERATURE,
        max_tokens=LLM_MAX_TOKENS,
    )


def _extract_json_from_response(response: str) -> List[Dict]:
    """
    Extrait le tableau JSON de la réponse LLM.

    Le LLM peut parfois ajouter du texte avant/après le JSON.
    Cette fonction tente d'extraire uniquement le JSON valide.

    Args:
        response: Réponse brute du LLM.

    Returns:
        Liste de recommandations parsées.
    """
    # Essayer de parser directement
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass

    # Chercher un tableau JSON dans la réponse
    json_match = re.search(r'\[[\s\S]*\]', response)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    # Fallback : créer des recommandations par défaut
    logger.warning("Impossible de parser le JSON, utilisation du fallback")
    return []


def _build_recommendations_prompt(
    interpretation: str,
    rag_context: List[Dict],
    kpis: Dict[str, Any]
) -> str:
    """Construit le prompt pour générer les recommandations."""

    # Extraire les sources RAG
    rag_sources = []
    for ctx in rag_context[:5]:
        source = ctx.get("source", "Guide tunisien")
        section = ctx.get("section", "")
        content = ctx.get("page_content", "")[:200]
        rag_sources.append(f"- [{source}] {section}: {content}...")

    rag_text = "\n".join(rag_sources) if rag_sources else "Aucune source RAG disponible."

    # Identifier les problèmes clés depuis les KPIs
    problems = []

    finance = kpis.get("finance", {})
    if finance.get("profit_margin", 100) < 10:
        problems.append("Marge bénéficiaire faible")
    if finance.get("trend") == "baisse":
        problems.append("Tendance des revenus à la baisse")

    marketing = kpis.get("marketing", {})
    if marketing.get("avg_conversion_rate", 100) < 5:
        problems.append("Taux de conversion marketing faible")
    if marketing.get("cost_per_conversion", 0) > 50:
        problems.append("Coût d'acquisition client élevé")

    support = kpis.get("support", {})
    if support.get("avg_satisfaction", 5) < 3.5:
        problems.append("Satisfaction client insuffisante")
    if support.get("high_churn_rate", 0) > 20:
        problems.append("Risque élevé de perte de clients")

    problems_text = "\n".join(f"• {p}" for p in problems) if problems else "Aucun problème majeur identifié."

    return f"""ANALYSE DE L'ENTREPRISE :
{interpretation[:1500]}

PROBLÈMES IDENTIFIÉS :
{problems_text}

SOURCES DE RÉFÉRENCE (guides tunisiens) :
{rag_text}

CONSIGNE :
Génère exactement 5 recommandations stratégiques au format JSON.
Base-toi sur l'analyse ci-dessus et les bonnes pratiques des guides tunisiens.
Priorise les actions selon leur urgence et leur impact potentiel.

RETOURNE UNIQUEMENT LE TABLEAU JSON."""


def _get_fallback_recommendations(kpis: Dict[str, Any]) -> List[Dict]:
    """
    Génère des recommandations par défaut si le LLM échoue.

    Args:
        kpis: KPIs de l'entreprise.

    Returns:
        Liste de 5 recommandations génériques mais pertinentes.
    """
    recommendations = []

    finance = kpis.get("finance", {})
    marketing = kpis.get("marketing", {})
    support = kpis.get("support", {})

    # Recommandation 1 : Finance
    if finance.get("profit_margin", 100) < 15:
        recommendations.append({
            "priorite": 1,
            "titre": "Optimiser la marge bénéficiaire",
            "action": "Renégocier les contrats fournisseurs et identifier les postes de charge à réduire. Analyser la structure de coûts fixes vs variables.",
            "impact": "Amélioration de la marge de 2-5 points",
            "source": "guide_gestion_financiere_tunisie.md"
        })
    else:
        recommendations.append({
            "priorite": 3,
            "titre": "Consolider les acquis financiers",
            "action": "Maintenir la discipline budgétaire et constituer une réserve de trésorerie équivalente à 3 mois de charges.",
            "impact": "Sécurisation financière à moyen terme",
            "source": "guide_gestion_financiere_tunisie.md"
        })

    # Recommandation 2 : Marketing
    best_channel = marketing.get("best_channel", "digital")
    recommendations.append({
        "priorite": 2,
        "titre": f"Renforcer le canal {best_channel}",
        "action": f"Augmenter le budget alloué au canal {best_channel} de 20% et optimiser les campagnes existantes avec des tests A/B.",
        "impact": "Augmentation des conversions de 15-25%",
        "source": "guide_gestion_entreprises_tunisiennes.md"
    })

    # Recommandation 3 : Service client
    if support.get("avg_satisfaction", 5) < 4:
        recommendations.append({
            "priorite": 2,
            "titre": "Améliorer la satisfaction client",
            "action": "Former l'équipe support aux techniques de résolution rapide. Mettre en place un système de suivi post-résolution.",
            "impact": "Amélioration du score de satisfaction de +0.5 point",
            "source": "guide_gestion_entreprises_tunisiennes.md"
        })
    else:
        recommendations.append({
            "priorite": 4,
            "titre": "Capitaliser sur la satisfaction client",
            "action": "Lancer un programme de parrainage et collecter des témoignages clients pour le marketing.",
            "impact": "Acquisition de nouveaux clients à coût réduit",
            "source": "guide_gestion_entreprises_tunisiennes.md"
        })

    # Recommandation 4 : Digitalisation
    recommendations.append({
        "priorite": 3,
        "titre": "Accélérer la digitalisation",
        "action": "Implémenter un CRM pour centraliser les données clients. Automatiser les relances et le suivi commercial.",
        "impact": "Gain de productivité de 20% sur les tâches administratives",
        "source": "guide_gestion_entreprises_tunisiennes.md"
    })

    # Recommandation 5 : Financement
    recommendations.append({
        "priorite": 5,
        "titre": "Explorer les financements BFPME",
        "action": "Contacter la BFPME ou SOTUGAR pour les lignes de crédit PME. Préparer un dossier de financement pour les investissements prévus.",
        "impact": "Accès à des financements à taux préférentiels",
        "source": "guide_gestion_financiere_tunisie.md"
    })

    return recommendations


def recommendation_agent(state: AgentState) -> AgentState:
    """
    Agent de recommandation stratégique.

    Cet agent :
    1. Analyse l'interprétation et le contexte RAG
    2. Génère 5 recommandations priorisées via le LLM
    3. Remplit state["recommendations"]

    Args:
        state: État courant du pipeline.

    Returns:
        État mis à jour avec les recommandations.
    """
    logger.info("[Recommendation Agent] Génération des recommandations")

    try:
        interpretation = state.get("interpretation", "")
        rag_context = state.get("rag_context", [])
        kpis = state.get("kpis", {})

        # Construire le prompt
        user_prompt = _build_recommendations_prompt(
            interpretation, rag_context, kpis
        )

        logger.debug("[Recommendation Agent] Appel LLM...")

        # Appeler le LLM
        llm = _get_llm()
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ]

        response = llm.invoke(messages)
        response_text = response.content

        # Parser la réponse JSON
        recommendations = _extract_json_from_response(response_text)

        # Valider et compléter si nécessaire
        if not recommendations or len(recommendations) < 5:
            logger.warning(
                "[Recommendation Agent] Réponse LLM incomplète, utilisation du fallback"
            )
            recommendations = _get_fallback_recommendations(kpis)

        # S'assurer qu'on a exactement 5 recommandations
        recommendations = recommendations[:5]

        # Trier par priorité
        recommendations.sort(key=lambda x: x.get("priorite", 5))

        logger.info(
            "[Recommendation Agent] %d recommandations générées",
            len(recommendations)
        )

        return {
            **state,
            "recommendations": recommendations,
            "current_step": "recommendations_completed",
        }

    except Exception as e:
        logger.exception("[Recommendation Agent] Erreur : %s", e)

        # Utiliser les recommandations par défaut en cas d'erreur
        fallback = _get_fallback_recommendations(state.get("kpis", {}))

        return {
            **state,
            "recommendations": fallback,
            "errors": state.get("errors", []) + [f"Recommendation Agent: {str(e)}"],
            "current_step": "recommendations_fallback",
        }
