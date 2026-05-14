"""
Point d'entrée Azure Functions — adaptateur ASGI pour FastAPI.

Ce fichier expose l'application FastAPI via l'adaptateur ASGI
d'Azure Functions (v2 programming model).

PRÉREQUIS :
  - Plan Azure Function App : Premium EP1 ou Dedicated App Service Plan
    (le plan Consommation est INCOMPATIBLE avec les dépendances ML lourdes
     comme sentence-transformers ~300 Mo et ChromaDB)
  - Variable d'environnement PYTHON_ENABLE_WORKER_EXTENSIONS=1 à activer
    dans les Application Settings du Function App sur le portail Azure.
"""

import azure.functions as func
from azure.functions import AsgiFunctionApp

# Import de l'application FastAPI définie dans backend/main.py
from backend.main import app as fastapi_app

# Adaptation FastAPI → Azure Functions via l'interface ASGI
app = AsgiFunctionApp(
    app=fastapi_app,
    http_auth_level=func.AuthLevel.ANONYMOUS,
)
