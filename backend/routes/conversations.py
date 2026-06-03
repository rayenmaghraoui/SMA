"""
Route /conversations — persistance des conversations côté serveur.

GET  /conversations       → charge les conversations depuis data/conversations.json
POST /conversations       → sauvegarde toutes les conversations sur disque
"""

import json
import logging
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from backend.config import DATA_DIR

logger = logging.getLogger(__name__)

CONVERSATIONS_FILE = DATA_DIR / "conversations.json"

router = APIRouter(prefix="/conversations", tags=["Conversations"])


class ConversationsSaveRequest(BaseModel):
    conversations: list[Any]


@router.post("")
async def save_conversations(request: ConversationsSaveRequest) -> dict:
    """
    Sauvegarde toutes les conversations sur le disque.

    Args:
        request: Liste des conversations à persister.

    Returns:
        Dict indiquant le succès et le nombre de conversations sauvegardées.
    """
    try:
        CONVERSATIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONVERSATIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(request.conversations, f, ensure_ascii=False, indent=2)
        logger.info("Conversations sauvegardées : %d", len(request.conversations))
        return {"success": True, "count": len(request.conversations)}
    except Exception as e:
        logger.exception("Erreur sauvegarde conversations: %s", e)
        return {"success": False, "error": str(e)}


@router.get("")
async def load_conversations() -> dict:
    """
    Charge les conversations depuis le disque.

    Returns:
        Dict avec la liste des conversations ou une liste vide si aucun fichier.
    """
    try:
        if not CONVERSATIONS_FILE.exists():
            return {"success": True, "conversations": []}
        with open(CONVERSATIONS_FILE, "r", encoding="utf-8") as f:
            conversations = json.load(f)
        logger.info("Conversations chargées : %d", len(conversations))
        return {"success": True, "conversations": conversations}
    except Exception as e:
        logger.exception("Erreur chargement conversations: %s", e)
        return {"success": True, "conversations": []}
