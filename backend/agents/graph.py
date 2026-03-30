"""
Graphe LangGraph — orchestration du pipeline multi-agents complet.

Ce module définit le graphe d'exécution des 5 agents et fournit
les fonctions pour lancer le pipeline.

Pipeline final :
    analysis_agent → interpretation_agent → rag_agent
    → recommendation_agent → report_agent → END
"""

import logging
from typing import Any, Dict, Optional

from langgraph.graph import StateGraph, END

from backend.agents.state import AgentState, create_initial_state
from backend.agents.analysis_agent import analysis_agent
from backend.agents.interpretation_agent import interpretation_agent
from backend.agents.rag_agent import rag_agent
from backend.agents.recommendation_agent import recommendation_agent
from backend.agents.report_agent import report_agent

logger = logging.getLogger(__name__)

# Liste des étapes pour le suivi de progression
PIPELINE_STEPS = [
    "analysis_agent",
    "interpretation_agent",
    "rag_agent",
    "recommendation_agent",
    "report_agent",
]


def _build_graph() -> StateGraph:
    """
    Construit le graphe LangGraph avec les 5 agents.

    Workflow :
        1. analysis_agent      : Calcul des KPIs et détection d'anomalies
        2. interpretation_agent: Interprétation LLM des KPIs
        3. rag_agent           : Recherche contextuelle dans les guides
        4. recommendation_agent: Génération de recommandations
        5. report_agent        : Structuration du rapport final

    Returns:
        Graphe LangGraph compilé.
    """
    # Création du graphe avec le type d'état
    workflow = StateGraph(AgentState)

    # Ajout des 5 nœuds (agents)
    workflow.add_node("analysis_agent", analysis_agent)
    workflow.add_node("interpretation_agent", interpretation_agent)
    workflow.add_node("rag_agent", rag_agent)
    workflow.add_node("recommendation_agent", recommendation_agent)
    workflow.add_node("report_agent", report_agent)

    # Définition du point d'entrée
    workflow.set_entry_point("analysis_agent")

    # Enchaînement des agents (pipeline linéaire)
    workflow.add_edge("analysis_agent", "interpretation_agent")
    workflow.add_edge("interpretation_agent", "rag_agent")
    workflow.add_edge("rag_agent", "recommendation_agent")
    workflow.add_edge("recommendation_agent", "report_agent")
    workflow.add_edge("report_agent", END)

    # Compilation du graphe
    return workflow.compile()


# Instance globale du graphe compilé
_graph = _build_graph()


def run_graph(
    raw_data: Optional[Dict[str, Any]] = None,
    user_question: Optional[str] = None
) -> AgentState:
    """
    Exécute le pipeline complet et retourne l'état final.

    Args:
        raw_data: Données brutes optionnelles (DataFrames sérialisés).
                  Si None, les données par défaut sont chargées.
        user_question: Question utilisateur optionnelle pour le mode chat.

    Returns:
        État final contenant le rapport complet.
    """
    logger.info("=== Démarrage du pipeline LangGraph (5 agents) ===")
    logger.info("Pipeline : %s", " → ".join(PIPELINE_STEPS))

    # Création de l'état initial
    initial_state = create_initial_state(
        raw_data=raw_data,
        user_question=user_question
    )

    # Exécution du graphe
    try:
        final_state = _graph.invoke(initial_state)
        logger.info("=== Pipeline terminé avec succès ===")

        # Log des résultats
        errors = final_state.get("errors", [])

        if errors:
            logger.warning("Pipeline terminé avec %d erreur(s)", len(errors))

        logger.info(
            "Rapport généré: %d recommandations, %d anomalies",
            len(final_state.get("recommendations", [])),
            len(final_state.get("anomalies", []))
        )

        return final_state

    except Exception as e:
        logger.exception("Erreur lors de l'exécution du pipeline : %s", e)
        return {
            **initial_state,
            "errors": [str(e)],
            "current_step": "error",
        }


async def run_graph_async(
    raw_data: Optional[Dict[str, Any]] = None,
    user_question: Optional[str] = None
) -> AgentState:
    """
    Version asynchrone de run_graph.

    Utilise ainvoke() pour l'exécution non-bloquante dans FastAPI.

    Args:
        raw_data: Données brutes optionnelles.
        user_question: Question utilisateur optionnelle.

    Returns:
        État final du pipeline.
    """
    logger.info("=== Démarrage du pipeline LangGraph async ===")

    initial_state = create_initial_state(
        raw_data=raw_data,
        user_question=user_question
    )

    try:
        final_state = await _graph.ainvoke(initial_state)
        logger.info("=== Pipeline async terminé ===")
        return final_state

    except Exception as e:
        logger.exception("Erreur pipeline async : %s", e)
        return {
            **initial_state,
            "errors": [str(e)],
            "current_step": "error",
        }


async def run_graph_streaming(
    raw_data: Optional[Dict[str, Any]] = None,
    user_question: Optional[str] = None
):
    """
    Générateur asynchrone pour le streaming du pipeline.

    Yield des événements à chaque étape pour le streaming SSE.

    Args:
        raw_data: Données brutes optionnelles.
        user_question: Question utilisateur optionnelle.

    Yields:
        Dictionnaires {"step": str, "status": str, "data": Any}
    """
    logger.info("=== Démarrage du pipeline streaming ===")

    initial_state = create_initial_state(
        raw_data=raw_data,
        user_question=user_question
    )

    try:
        # Stream les événements du graphe
        async for event in _graph.astream(initial_state):
            # event est un dict avec le nom du nœud et son output
            for node_name, node_output in event.items():
                current_step = node_output.get("current_step", node_name)

                yield {
                    "step": node_name,
                    "status": "completed",
                    "current_step": current_step,
                }

                # Si c'est le report_agent, yield le rapport final
                if node_name == "report_agent":
                    yield {
                        "step": "final",
                        "status": "done",
                        "report": node_output.get("report", {}),
                        "interpretation": node_output.get("interpretation", ""),
                    }

    except Exception as e:
        logger.exception("Erreur streaming : %s", e)
        yield {
            "step": "error",
            "status": "error",
            "error": str(e),
        }


def get_graph_info() -> Dict[str, Any]:
    """
    Retourne des informations sur la structure du graphe.

    Returns:
        Dictionnaire avec les nœuds et transitions du graphe.
    """
    return {
        "phase": 4,
        "version": "1.0.0",
        "nodes": PIPELINE_STEPS,
        "total_agents": len(PIPELINE_STEPS),
        "edges": [
            ("START", "analysis_agent"),
            ("analysis_agent", "interpretation_agent"),
            ("interpretation_agent", "rag_agent"),
            ("rag_agent", "recommendation_agent"),
            ("recommendation_agent", "report_agent"),
            ("report_agent", "END"),
        ],
        "description": (
            "Pipeline complet : analyse des données, interprétation LLM, "
            "recherche RAG, recommandations et génération du rapport."
        ),
    }


def get_pipeline_steps() -> list:
    """Retourne la liste des étapes du pipeline."""
    return PIPELINE_STEPS.copy()
