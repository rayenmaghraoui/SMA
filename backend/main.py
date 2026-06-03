"""
Point d'entrée FastAPI — AI Business Consultant.

Ce module initialise l'application FastAPI, configure CORS,
et enregistre toutes les routes de l'API.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import (
    API_HOST,
    API_PORT,
    DEBUG,
    FRONTEND_URL,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_MODEL,
)
from backend.routes.analyze import router as analyze_router
from backend.routes.upload import router as upload_router
from backend.routes.chat import router as chat_router
from backend.routes.report import router as report_router
from backend.routes.sql import router as sql_router
from backend.routes.conversations import router as conversations_router
from backend.models.response_models import HealthResponse

# ============================================================
# Configuration du logging
# ============================================================

logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ============================================================
# Lifespan (startup / shutdown)
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Gestion du cycle de vie de l'application.

    - Startup : vérifie la configuration Azure OpenAI
    - Shutdown : nettoyage des ressources
    """
    # Startup
    logger.info("=== Démarrage de l'API AI Business Consultant ===")
    logger.info("Mode DEBUG : %s", DEBUG)
    logger.info("Frontend URL : %s", FRONTEND_URL)
    logger.info("Azure OpenAI endpoint : %s", AZURE_OPENAI_ENDPOINT)
    logger.info("Modèle LLM : %s", AZURE_OPENAI_MODEL)

    # Vérifier l'accessibilité de l'endpoint Azure
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                AZURE_OPENAI_ENDPOINT,
                headers={"User-Agent": "AI-Business-Consultant/1.0"},
            )
            # Un 401 ou 200 signifie que le serveur répond
            if response.status_code in (200, 401, 404):
                logger.info("Connexion à Azure AI Foundry : OK (status %d)", response.status_code)
            else:
                logger.warning("Azure répond avec status %d", response.status_code)
    except Exception as e:
        logger.warning("Impossible de contacter Azure AI Foundry : %s", e)
        logger.warning("Le LLM ne sera pas disponible pour les recommandations")

    yield

    # Shutdown
    logger.info("=== Arrêt de l'API ===")


# ============================================================
# Création de l'application FastAPI
# ============================================================

app = FastAPI(
    title="AI Business Consultant",
    description=(
        "Système multi-agents d'aide à la décision pour PME tunisiennes. "
        "Analyse les données opérationnelles, détecte les problèmes de gestion "
        "et produit des recommandations stratégiques."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


# ============================================================
# Configuration CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        FRONTEND_URL,
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
    ],
    # Permet tous les sous-domaines Vercel et Azure Static Web Apps en production
    allow_origin_regex=r"https://.*\.vercel\.app|https://.*\.azurestaticapps\.net",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Enregistrement des routes
# ============================================================

app.include_router(analyze_router)
app.include_router(upload_router)
app.include_router(chat_router)
app.include_router(report_router)
app.include_router(sql_router)
app.include_router(conversations_router)


# ============================================================
# Routes de base
# ============================================================

@app.get("/health", response_model=HealthResponse, tags=["Système"])
async def health_check() -> HealthResponse:
    """
    Vérifie l'état de santé de l'API et du LLM Azure AI Foundry.

    Returns:
        HealthResponse avec le statut de l'API et d'Azure.
    """
    api_ok = True
    azure_ok = False

    # Vérifier la joignabilité de l'endpoint Azure AI Foundry
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(AZURE_OPENAI_ENDPOINT)
            azure_ok = response.status_code < 500
    except Exception:
        azure_ok = False

    # Déterminer le statut global
    if api_ok and azure_ok:
        status = "ok"
        message = "Tous les services sont opérationnels."
    elif api_ok:
        status = "degraded"
        message = "API opérationnelle. Azure AI Foundry non joignable (vérifiez l'endpoint et la clé)."
    else:
        status = "error"
        message = "Service indisponible."

    return HealthResponse(
        status=status,
        api=api_ok,
        azure=azure_ok,
        message=message,
    )


@app.get("/", tags=["Système"])
async def root() -> dict:
    """
    Route racine — informations de base sur l'API.

    Returns:
        Dict avec le nom et la version de l'API.
    """
    return {
        "name": "AI Business Consultant API",
        "version": "1.0.0",
        "description": "Système multi-agents pour PME tunisiennes",
        "docs": "/docs",
        "endpoints": {
            "analyze": "POST /analyze - Analyse complète des données",
            "upload": "POST /upload - Upload de fichiers CSV",
            "chat": "POST /chat - Chat avec streaming SSE",
            "report": "GET /report - Récupération du rapport",
            "health": "GET /health - État de santé de l'API",
        },
    }


@app.get("/pipeline", tags=["Système"])
async def pipeline_info() -> dict:
    """
    Informations sur le pipeline d'agents.

    Returns:
        Structure du graphe LangGraph.
    """
    from backend.agents.graph import get_graph_info
    return get_graph_info()


# ============================================================
# Point d'entrée pour uvicorn
# ============================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=API_HOST,
        port=API_PORT,
        reload=DEBUG,
    )
