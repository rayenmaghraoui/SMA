"""
Route /chat — interface conversationnelle avec streaming SSE.

Cette route permet aux utilisateurs de poser des questions en langage
naturel et reçoit les réponses en streaming (Server-Sent Events).
"""

import json
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from backend.models.request_models import ChatRequest
from backend.agents.graph import run_graph_streaming, get_pipeline_steps
from backend.routes.report import save_report

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


async def _stream_chat_response(message: str) -> AsyncGenerator[str, None]:
    """
    Générateur asynchrone pour le streaming de la réponse.

    Args:
        message: Question de l'utilisateur.

    Yields:
        Événements SSE formatés.
    """
    steps = get_pipeline_steps()
    step_labels = {
        "analysis_agent": "Analyse des données en cours...",
        "interpretation_agent": "Interprétation des KPIs...",
        "rag_agent": "Recherche dans les guides tunisiens...",
        "recommendation_agent": "Génération des recommandations...",
        "report_agent": "Structuration du rapport final...",
    }

    try:
        # Envoyer le début
        yield _format_sse("step", "Démarrage de l'analyse...")

        # Exécuter le pipeline en streaming
        async for event in run_graph_streaming(user_question=message):
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

    return StreamingResponse(
        _stream_chat_response(request.message),
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
