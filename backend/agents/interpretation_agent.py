"""
Agent d'interprétation — analyse LLM des KPIs.

Cet agent utilise DeepSeek-V3.2 via Azure AI Foundry pour interpréter les KPIs calculés
et les anomalies détectées dans le contexte d'une PME tunisienne.

Entrée : state["kpis"], state["anomalies"], state["rag_context"]
Sortie : state["interpretation"]
"""

import logging
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

# Prompt système pour l'interprétation
SYSTEM_PROMPT = """Tu es un consultant business spécialisé dans les PME tunisiennes.

CONTEXTE :
- Tu analyses les KPIs d'une entreprise tunisienne.
- Tous les montants sont en Dinars Tunisiens (TND).
- Tu connais le contexte économique tunisien : TVA 19%, IS 15% pour PME,
  Code du travail tunisien, saisonnalité (Ramadan, été).

RÈGLES STRICTES :
- Maximum 5 points au total.
- Chaque point = 1 courte phrase.
- Pas de paragraphes, pas de répétitions.
- Langage simple et direct.
- Inclure des chiffres ou KPIs si pertinent.
- Éviter les formulations vagues ou génériques.
- Ne pas utiliser le gras, l'italique ou tout autre formatage spécial.
- Ne pas utiliser de symboles comme **, *, #, __, etc.

FORMAT OBLIGATOIRE (respecter exactement) :
Insight 1: courte explication
Insight 2: courte explication
Insight 3: courte explication
Action 1: courte recommandation
Action 2: courte recommandation

IMPORTANT :
- Chaque ligne commence par un mot-clé court suivi de deux-points.
- Ne rien écrire avant le premier "Insight 1:".
- Ne rien écrire après le dernier point.
- Répondre uniquement en français.
"""


def _format_kpis_for_prompt(kpis: Dict[str, Any]) -> str:
    """Formate les KPIs pour le prompt LLM."""
    lines = []

    # KPIs Finance
    finance = kpis.get("finance", {})
    if finance:
        lines.append("📊 FINANCE :")
        lines.append(f"  - Chiffre d'affaires total : {finance.get('revenue_total', 'N/A'):,.0f} TND")
        lines.append(f"  - Bénéfice total : {finance.get('profit_total', 'N/A'):,.0f} TND")
        lines.append(f"  - Marge bénéficiaire : {finance.get('profit_margin', 'N/A'):.1f}%")
        lines.append(f"  - Croissance moyenne : {finance.get('avg_growth_rate', 'N/A'):.1f}%")
        lines.append(f"  - Tendance : {finance.get('trend', 'N/A')}")
        lines.append(f"  - Meilleur mois : {finance.get('best_month', 'N/A')}")
        lines.append(f"  - Pire mois : {finance.get('worst_month', 'N/A')}")

    # KPIs Marketing
    marketing = kpis.get("marketing", {})
    if marketing:
        lines.append("\n📈 MARKETING :")
        lines.append(f"  - Budget total dépensé : {marketing.get('total_budget_spent', 'N/A'):,.0f} TND")
        lines.append(f"  - Conversions totales : {marketing.get('total_conversions', 'N/A')}")
        lines.append(f"  - Taux de conversion moyen : {marketing.get('avg_conversion_rate', 'N/A'):.2f}%")
        lines.append(f"  - Meilleur canal : {marketing.get('best_channel', 'N/A')}")
        lines.append(f"  - Coût par conversion : {marketing.get('cost_per_conversion', 'N/A'):.2f} TND")
        lines.append(f"  - Meilleure campagne : {marketing.get('top_campaign', 'N/A')}")

    # KPIs Support
    support = kpis.get("support", {})
    if support:
        lines.append("\n🎧 SUPPORT CLIENT :")
        lines.append(f"  - Satisfaction moyenne : {support.get('avg_satisfaction', 'N/A'):.2f}/5")
        lines.append(f"  - Temps de résolution moyen : {support.get('avg_resolution_hours', 'N/A'):.1f}h")
        lines.append(f"  - Taux de churn élevé : {support.get('high_churn_rate', 'N/A'):.1f}%")
        lines.append(f"  - Problème le plus fréquent : {support.get('top_issue_type', 'N/A')}")
        lines.append(f"  - Conformité SLA (<24h) : {support.get('sla_compliance', 'N/A'):.1f}%")

    return "\n".join(lines)


def _format_anomalies_for_prompt(anomalies: List[Dict]) -> str:
    """Formate les anomalies pour le prompt LLM."""
    if not anomalies:
        return "Aucune anomalie significative détectée."

    lines = ["⚠️ ANOMALIES DÉTECTÉES :"]

    # Grouper par dataset
    by_dataset: Dict[str, List[Dict]] = {}
    for a in anomalies:
        dataset = a.get("dataset", "inconnu")
        if dataset not in by_dataset:
            by_dataset[dataset] = []
        by_dataset[dataset].append(a)

    for dataset, items in by_dataset.items():
        lines.append(f"\n  [{dataset.upper()}]")
        for item in items[:5]:  # Limiter à 5 par dataset
            anomaly_type = "↑ haute" if item.get("type") == "high" else "↓ basse"
            lines.append(
                f"    - {item.get('colonne')}: {item.get('valeur')} ({anomaly_type})"
            )

    return "\n".join(lines)


def _format_rag_context_for_prompt(rag_context: List[Dict]) -> str:
    """Formate le contexte RAG pour le prompt LLM."""
    if not rag_context:
        return ""

    lines = ["📚 CONTEXTE DES GUIDES TUNISIENS :"]

    for i, ctx in enumerate(rag_context[:3], 1):
        source = ctx.get("source", "Guide")
        section = ctx.get("section", "")
        content = ctx.get("page_content", "")[:300]

        lines.append(f"\n  [{i}] Source: {source}")
        if section:
            lines.append(f"      Section: {section}")
        lines.append(f"      Extrait: {content}...")

    return "\n".join(lines)


def _get_llm() -> ChatOpenAI:
    """Retourne une instance du LLM configuré."""
    return ChatOpenAI(
        base_url=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_API_KEY,
        model=AZURE_OPENAI_MODEL,
        temperature=LLM_TEMPERATURE,
        max_tokens=1024,
    )


def _remove_duplicate_content(text: str) -> str:
    """
    Supprime le contenu dupliqué dans la réponse LLM.

    DeepSeek peut parfois répéter le même contenu. Cette fonction
    détecte et supprime les sections dupliquées.

    Args:
        text: Texte potentiellement avec doublons.

    Returns:
        Texte nettoyé sans doublons.
    """
    if not text or len(text) < 180:
        return text

    normalized = " ".join(text.split()).strip()

    # Méthode 1: Chercher si le début du texte se répète plus loin
    # Prendre les premiers 50 caractères comme signature
    signature = normalized[:80].strip()

    if signature:
        # Chercher cette signature après la position 100
        second_occurrence = normalized.find(signature, 120)

        if second_occurrence > 0:
            # Le texte se répète - garder uniquement la première partie
            return normalized[:second_occurrence].strip()

    # Méthode 2: Chercher des phrases clés qui se répètent
    key_phrases = [
        "Pour améliorer la satisfaction client",
        "Analyse de la situation financière",
        "Évaluation de la performance marketing",
        "Points forts",
        "Points faibles",
    ]

    for phrase in key_phrases:
        first_pos = normalized.find(phrase)
        if first_pos >= 0:
            second_pos = normalized.find(phrase, first_pos + len(phrase) + 30)
            if second_pos > 0:
                # Cette phrase apparaît deux fois - couper au deuxième
                return normalized[:second_pos].strip()

    # Méthode 3: Détection générique d'une répétition de bloc long (suffixe)
    # On cherche un segment de taille significative présent 2 fois.
    for window in (260, 220, 180):
        if len(normalized) < window * 2:
            continue
        segment = normalized[:window]
        second = normalized.find(segment, window + 40)
        if second > 0:
            return normalized[:second].strip()

    return normalized


def _build_interpretation_prompt(
    kpis_text: str,
    anomalies_text: str,
    rag_text: str,
    user_question: str = "",
) -> str:
    """
    Construit un prompt d'interprétation adapté au contexte.

    Si l'utilisateur pose une question ciblée (ex: satisfaction client),
    le prompt force une réponse focalisée sur ce besoin.
    """
    question = (user_question or "").strip()

    base_context = f"""Voici les données d'une PME tunisienne à analyser :

{kpis_text}

{anomalies_text}

{rag_text}
"""

    if question:
        return base_context + f"""
QUESTION UTILISATEUR :
{question}

CONSIGNES PRIORITAIRES :
1. Réponds d'abord et directement à la question utilisateur.
2. Focalise la réponse uniquement sur le domaine concerné.
   Si la question porte sur la satisfaction client, concentre-toi sur le support client.
3. N'ajoute pas d'analyse détaillée finance/marketing sauf si indispensable à la question.
4. Donne 3 à 5 actions concrètes, priorisées et mesurables.
5. Appuie chaque recommandation par les KPIs/anomalies disponibles.
6. Conclus avec des objectifs chiffrés à court terme (30 à 90 jours).
7. Ne répète pas les sections ou les paragraphes.

Format attendu : réponse structurée, concise et actionnable en français."""

    return base_context + """
CONSIGNES :
1. Analyse la situation financière globale de l'entreprise.
2. Évalue la performance marketing et identifie les canaux les plus rentables.
3. Examine la qualité du service client et le risque de perte de clients.
4. Identifie les 3 points forts et les 3 points faibles principaux.
5. Explique les anomalies détectées et leurs impacts potentiels.

Fournis une analyse structurée et actionnable."""


def interpretation_agent(state: AgentState) -> AgentState:
    """
    Agent d'interprétation des KPIs via LLM.

    Cet agent :
    1. Construit un prompt avec les KPIs, anomalies et contexte RAG
    2. Appelle DeepSeek-V3.2 via Azure AI Foundry pour générer une interprétation
    3. Remplit state["interpretation"]

    Args:
        state: État courant du pipeline.

    Returns:
        État mis à jour avec l'interprétation.
    """
    logger.info("[Interpretation Agent] Démarrage de l'interprétation LLM")

    try:
        kpis = state.get("kpis", {})
        anomalies = state.get("anomalies", [])
        rag_context = state.get("rag_context", [])

        user_question = state.get("user_question", "")

        # Construire le prompt utilisateur
        kpis_text = _format_kpis_for_prompt(kpis)
        anomalies_text = _format_anomalies_for_prompt(anomalies)
        rag_text = _format_rag_context_for_prompt(rag_context)
        user_prompt = _build_interpretation_prompt(
            kpis_text=kpis_text,
            anomalies_text=anomalies_text,
            rag_text=rag_text,
            user_question=user_question,
        )

        logger.debug("[Interpretation Agent] Appel LLM en cours...")

        # Appeler le LLM
        llm = _get_llm()
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ]

        response = llm.invoke(messages)
        interpretation = response.content

        # Nettoyer les doublons potentiels
        interpretation = _remove_duplicate_content(interpretation)

        logger.info(
            "[Interpretation Agent] Interprétation générée (%d caractères)",
            len(interpretation)
        )

        return {
            **state,
            "interpretation": interpretation,
            "current_step": "interpretation_completed",
        }

    except Exception as e:
        logger.exception("[Interpretation Agent] Erreur : %s", e)
        error_msg = (
            "Impossible de générer l'interprétation. "
            "Vérifiez la configuration Azure OpenAI (clé API, endpoint, modèle)."
        )
        return {
            **state,
            "interpretation": error_msg,
            "errors": state.get("errors", []) + [f"Interpretation Agent: {str(e)}"],
            "current_step": "interpretation_error",
        }


async def interpretation_agent_async(state: AgentState) -> AgentState:
    """
    Version asynchrone de l'agent d'interprétation.

    Permet le streaming token par token pour la route /chat.

    Args:
        state: État courant du pipeline.

    Returns:
        État mis à jour avec l'interprétation.
    """
    logger.info("[Interpretation Agent] Démarrage async")

    try:
        kpis = state.get("kpis", {})
        anomalies = state.get("anomalies", [])
        rag_context = state.get("rag_context", [])
        user_question = state.get("user_question", "")

        kpis_text = _format_kpis_for_prompt(kpis)
        anomalies_text = _format_anomalies_for_prompt(anomalies)
        rag_text = _format_rag_context_for_prompt(rag_context)
        user_prompt = _build_interpretation_prompt(
            kpis_text=kpis_text,
            anomalies_text=anomalies_text,
            rag_text=rag_text,
            user_question=user_question,
        )

        llm = _get_llm()
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ]

        response = await llm.ainvoke(messages)
        interpretation = _remove_duplicate_content(response.content)

        logger.info("[Interpretation Agent] Interprétation async générée")

        return {
            **state,
            "interpretation": interpretation,
            "current_step": "interpretation_completed",
        }

    except Exception as e:
        logger.exception("[Interpretation Agent] Erreur async : %s", e)
        return {
            **state,
            "interpretation": f"Erreur: {str(e)}",
            "errors": state.get("errors", []) + [str(e)],
            "current_step": "interpretation_error",
        }
