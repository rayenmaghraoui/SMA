"""
\u00c9tat partag\u00e9 entre tous les agents LangGraph.

Ce TypedDict d\u00e9finit la structure de donn\u00e9es qui circule entre les
diff\u00e9rents agents du pipeline d'analyse.
"""

from typing import Any, Dict, List, Optional, TypedDict


class AgentState(TypedDict):
    """
    \u00c9tat partag\u00e9 entre tous les agents du pipeline.

    Chaque agent lit cet \u00e9tat, le compl\u00e8te avec ses r\u00e9sultats,
    et le passe au suivant.

    Attributes:
        raw_data: DataFrames s\u00e9rialis\u00e9s des 5 CSV (ventes, regions, categories, canaux, kpis).
        user_question: Question optionnelle pos\u00e9e via le chat.
        kpis: R\u00e9sultats de l'Analysis Agent \u2014 KPIs calcul\u00e9s par domaine.
        anomalies: Anomalies d\u00e9tect\u00e9es dans les donn\u00e9es.
        interpretation: Analyse textuelle des KPIs par le LLM.
        rag_context: Passages pertinents extraits des guides tunisiens.
        recommendations: Liste de recommandations prioris\u00e9es.
        report: Rapport final structur\u00e9.
        errors: Liste des erreurs non bloquantes survenues.
        current_step: \u00c9tape en cours (pour le streaming SSE).
    """

    # Entr\u00e9e
    raw_data: Dict[str, Any]
    user_question: Optional[str]

    # R\u00e9sultats Analysis Agent
    kpis: Dict[str, Any]
    anomalies: List[Dict[str, Any]]

    # R\u00e9sultats Interpretation Agent
    interpretation: str

    # R\u00e9sultats RAG Agent
    rag_context: List[Dict[str, Any]]

    # R\u00e9sultats Recommendation Agent
    recommendations: List[Dict[str, Any]]

    # R\u00e9sultats Report Agent
    report: Dict[str, Any]

    # M\u00e9moire conversationnelle (3 derniers tours inject\u00e9s dans le prompt)
    conversation_history: List[Dict[str, str]]

    # M\u00e9tadonn\u00e9es
    errors: List[str]
    current_step: str


def create_initial_state(
    raw_data: Optional[Dict[str, Any]] = None,
    user_question: Optional[str] = None,
    conversation_history: Optional[List[Dict[str, str]]] = None,
) -> AgentState:
    """
    Cr\u00e9e un \u00e9tat initial vide pour le pipeline.

    Args:
        raw_data: Donn\u00e9es brutes optionnelles \u00e0 injecter.
        user_question: Question utilisateur optionnelle.

    Returns:
        AgentState initialis\u00e9 avec des valeurs par d\u00e9faut.
    """
    return AgentState(
        raw_data=raw_data or {},
        user_question=user_question,
        conversation_history=conversation_history or [],
        kpis={},
        anomalies=[],
        interpretation="",
        rag_context=[],
        recommendations=[],
        report={},
        errors=[],
        current_step="initialisation",
    )
