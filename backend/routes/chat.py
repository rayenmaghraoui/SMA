"""
Route /chat — interface conversationnelle avec streaming SSE.

Cette route permet aux utilisateurs de poser des questions en langage
naturel et reçoit les réponses en streaming (Server-Sent Events).

Routage d'intention :
    - Questions stratégiques → pipeline LangGraph (5 agents)
    - Questions d'exploration data → SQL agent (génération + exécution SQL)
"""

import json
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from backend.models.request_models import ChatRequest, SqlQueryRequest
from backend.agents.graph import run_graph_streaming, get_pipeline_steps
from backend.routes.report import save_report
from backend.sql_agent.intent_router import classify_intent, is_destructive_operation
from backend.sql_agent.generator import generate_sql
from backend.sql_agent.executor import execute_sql

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["Chat"])


def _format_sse(event_type: str, content: str) -> str:
    """
    Formate un événement SSE.

    Format SSE standard :
        data: {"type": "...", "content": "..."}

    Args:
        event_type: Type d'événement ("step", "token", "done", "error").
        content: Contenu de l'événement.

    Returns:
        Chaîne formatée pour SSE.
    """
    data = json.dumps({"type": event_type, "content": content}, ensure_ascii=False)
    return f"data: {data}\n\n"


async def _stream_chat_response(message: str, history: list) -> AsyncGenerator[str, None]:
    """
    Générateur asynchrone pour le streaming de la réponse.

    Routage d'intention :
        - "sql"       → SQL agent, résultat envoyé en SSE type "sql_result"
        - "strategic" → pipeline LangGraph complet (5 agents)

    Args:
        message: Question de l'utilisateur.
        history: Historique des 3 derniers échanges.

    Yields:
        Événements SSE formatés.
    """
    # Vérification préalable : opérations destructives toujours refusées
    if is_destructive_operation(message):
        yield _format_sse(
            "error",
            "Cette opération n'est pas autorisée. "
            "Le système accepte uniquement les requêtes de lecture (SELECT). "
            "Les opérations de modification, suppression ou création de tables/colonnes "
            "ne sont pas permises."
        )
        yield _format_sse("done", "")
        return

    # Routage d'intention
    intent = classify_intent(message)
    logger.info("Intent pour '%s': %s", message[:60], intent)

    if intent == "sql":
        async for event in _stream_sql_response(message):
            yield event
    else:
        async for event in _stream_strategic_response(message, history):
            yield event


async def _stream_sql_response(message: str) -> AsyncGenerator[str, None]:
    """
    Pipeline SQL : génère et exécute une requête SQL, stream le résultat.

    Yields:
        Événements SSE : step → sql_result → done (ou error).
    """
    try:
        yield _format_sse("step", "Analyse de votre question en cours...")
        yield _format_sse("step", "Génération de la requête SQL...")

        sql, viz_type = await generate_sql(message)
        yield _format_sse("step", "Exécution de la requête sur les données...")

        rows, errors = await execute_sql(sql)

        if errors:
            yield _format_sse("error", errors[0])
            return

        # Construire la réponse SQL complète
        from backend.routes.sql import _build_chart_data
        chart_data = _build_chart_data(rows, viz_type)
        chart_dict = chart_data.model_dump() if chart_data else None

        sql_result = {
            "sql": sql,
            "rows_preview": rows[:100],
            "total_rows": len(rows),
            "chart_data": chart_dict,
            "message": f"{len(rows)} ligne(s) retournée(s).",
        }
        yield _format_sse("sql_result", json.dumps(sql_result, ensure_ascii=False, default=str))
        yield _format_sse("done", "")

    except Exception as e:
        logger.exception("Erreur SQL streaming: %s", e)
        yield _format_sse("error", str(e))


async def _stream_strategic_response(message: str, history: list) -> AsyncGenerator[str, None]:
    """
    Pipeline LangGraph complet (5 agents) pour les questions stratégiques.

    Args:
        message: Question utilisateur.
        history: Historique des 3 derniers échanges (mémoire conversationnelle).

    Yields:
        Événements SSE : step → token → report → done (ou error).
    """
    step_labels = {
        "analysis_agent": "Analyse des données en cours...",
        "interpretation_agent": "Interprétation des KPIs...",
        "rag_agent": "Recherche dans les guides tunisiens...",
        "recommendation_agent": "Génération des recommandations...",
        "report_agent": "Structuration du rapport final...",
    }

    try:
        # Envoyer le début
        yield _format_sse("step", "Démarrage de l'analyse stratégique...")

        # Exécuter le pipeline en streaming avec l'historique
        async for event in run_graph_streaming(
            user_question=message,
            conversation_history=history,
        ):
            step = event.get("step", "")
            status = event.get("status", "")

            if step in step_labels:
                # Notifier l'étape en cours
                yield _format_sse("step", step_labels[step])

            elif step == "final":
                # Envoyer l'interprétation token par token (simulé)
                interpretation = event.get("interpretation", "")

                if interpretation:
                    # Envoyer par chunks de caractères pour préserver la structure Markdown
                    chunk_size = 60
                    for i in range(0, len(interpretation), chunk_size):
                        yield _format_sse("token", interpretation[i:i + chunk_size])

                # Envoyer le rapport complet
                report = event.get("report", {})
                if isinstance(report, dict) and report:
                    try:
                        save_report(report)
                    except Exception as e:
                        logger.warning("Impossible de sauvegarder le rapport depuis /chat: %s", e)
                yield _format_sse("report", json.dumps(report, ensure_ascii=False))

            elif step == "error":
                yield _format_sse("error", event.get("error", "Erreur inconnue"))
                return

        # Signal de fin
        yield _format_sse("done", "")

    except Exception as e:
        logger.exception("Erreur streaming chat: %s", e)
        yield _format_sse("error", str(e))


@router.post("/chat")
async def chat(request: ChatRequest) -> StreamingResponse:
    """
    Interface conversationnelle avec streaming SSE.

    Reçoit une question utilisateur, lance le pipeline complet,
    et stream la réponse en temps réel.

    Format SSE des événements :
        - {"type": "step", "content": "Analyse en cours..."}
        - {"type": "token", "content": "mot "}
        - {"type": "report", "content": "{...}"}
        - {"type": "done", "content": ""}
        - {"type": "error", "content": "message d'erreur"}

    Args:
        request: ChatRequest avec le message utilisateur.

    Returns:
        StreamingResponse avec les événements SSE.
    """
    logger.info("Chat request: %s", request.message[:100])

    if not request.message.strip():
        raise HTTPException(
            status_code=400,
            detail="Le message ne peut pas être vide."
        )

    # Limiter l'historique à 6 messages max (3 tours)
    history = (request.history or [])[-6:]

    return StreamingResponse(
        _stream_chat_response(request.message, history),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/chat/simple")
async def chat_simple(request: ChatRequest) -> dict:
    """
    Version non-streaming du chat.

    Utile pour les tests ou si le client ne supporte pas SSE.

    Args:
        request: ChatRequest avec le message utilisateur.

    Returns:
        Dictionnaire avec l'interprétation et le rapport.
    """
    logger.info("Chat simple request: %s", request.message[:100])

    if not request.message.strip():
        raise HTTPException(
            status_code=400,
            detail="Le message ne peut pas être vide."
        )

    from backend.agents.graph import run_graph_async

    try:
        final_state = await run_graph_async(user_question=request.message)
        report = final_state.get("report", {})
        if report:
            try:
                save_report(report)
            except Exception as e:
                logger.warning("Impossible de sauvegarder le rapport depuis /chat/simple: %s", e)

        return {
            "success": True,
            "interpretation": final_state.get("interpretation", ""),
            "recommendations": final_state.get("recommendations", []),
            "report": report,
            "errors": final_state.get("errors", []),
        }

    except Exception as e:
        logger.exception("Erreur chat simple: %s", e)
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du traitement: {str(e)}"
        )
