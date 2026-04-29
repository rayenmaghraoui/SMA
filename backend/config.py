"""
Configuration globale du projet AI Business Consultant.
Charge les variables d'environnement depuis le fichier .env
et expose tous les chemins et constantes du projet.
"""

import os
import logging
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv

# Chargement du fichier .env depuis la racine du projet
_ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(_ROOT_DIR / ".env")

logger = logging.getLogger(__name__)


# ============================================================
# Fonctions utilitaires internes
# ============================================================

def _resolve_path(env_var: str, default: str) -> Path:
    """
    Résout un chemin relatif (depuis le .env) par rapport à la racine du projet.

    Args:
        env_var: Nom de la variable d'environnement.
        default: Valeur par défaut si la variable n'est pas définie.

    Returns:
        Chemin absolu résolu depuis ROOT_DIR.
    """
    raw = os.getenv(env_var, default)
    # Path() reconnaît les chemins relatifs type "./data" ou "data"
    relative = Path(raw)
    return (_ROOT_DIR / relative).resolve()


# ============================================================
# Chemins
# ============================================================

ROOT_DIR: Path = _ROOT_DIR

DATA_DIR: Path = _resolve_path("DATA_DIR", "./data")
DOCUMENTS_DIR: Path = _resolve_path("DOCUMENTS_DIR", "./documents")
CHROMA_DB_PATH: Path = _resolve_path("CHROMA_DB_PATH", "./backend/rag/chroma_db")
UPLOADS_DIR: Path = _resolve_path("UPLOADS_DIR", "./data/uploads")

# Fichiers CSV attendus
FINANCE_CSV: Path = DATA_DIR / "01_finance_performance.csv"
MARKETING_CSV: Path = DATA_DIR / "02_marketing_campaigns.csv"
SUPPORT_CSV: Path = DATA_DIR / "03_customer_support.csv"


# ============================================================
# LLM (Azure AI Foundry — DeepSeek-V3.2)
# ============================================================

AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY", "")
AZURE_OPENAI_ENDPOINT: str = os.getenv(
    "AZURE_OPENAI_ENDPOINT",
    "https://selim-mdosvfln-eastus2.services.ai.azure.com/openai/v1/",
)
AZURE_OPENAI_MODEL: str = os.getenv("AZURE_OPENAI_MODEL", "DeepSeek-V3.2")
LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.3"))
LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "2048"))


# ============================================================
# Embeddings
# ============================================================

EMBEDDING_MODEL: str = os.getenv(
    "EMBEDDING_MODEL", "sentence-transformers/sentence-t5-base"
)


# ============================================================
# RAG
# ============================================================

RAG_CHUNK_SIZE: int = int(os.getenv("RAG_CHUNK_SIZE", "500"))
RAG_CHUNK_OVERLAP: int = int(os.getenv("RAG_CHUNK_OVERLAP", "50"))
RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "3"))


# ============================================================
# API
# ============================================================

API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
API_PORT: int = int(os.getenv("API_PORT", "8000"))
FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")


# ============================================================
# Environnement
# ============================================================

DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"


def _ensure_directories() -> None:
    """Crée les répertoires nécessaires s'ils n'existent pas."""
    for directory in [DATA_DIR, UPLOADS_DIR, DOCUMENTS_DIR, CHROMA_DB_PATH]:
        directory.mkdir(parents=True, exist_ok=True)


def get_config() -> Dict[str, Any]:
    """
    Retourne un dictionnaire contenant toute la configuration du projet.

    Returns:
        dict contenant tous les chemins, constantes LLM, RAG et API.
    """
    return {
        # Chemins
        "root_dir": str(ROOT_DIR),
        "data_dir": str(DATA_DIR),
        "documents_dir": str(DOCUMENTS_DIR),
        "chroma_db_path": str(CHROMA_DB_PATH),
        "uploads_dir": str(UPLOADS_DIR),
        "finance_csv": str(FINANCE_CSV),
        "marketing_csv": str(MARKETING_CSV),
        "support_csv": str(SUPPORT_CSV),
        # LLM
        "azure_openai_endpoint": AZURE_OPENAI_ENDPOINT,
        "azure_openai_model": AZURE_OPENAI_MODEL,
        "llm_temperature": LLM_TEMPERATURE,
        "llm_max_tokens": LLM_MAX_TOKENS,
        # Embeddings
        "embedding_model": EMBEDDING_MODEL,
        # RAG
        "rag_chunk_size": RAG_CHUNK_SIZE,
        "rag_chunk_overlap": RAG_CHUNK_OVERLAP,
        "rag_top_k": RAG_TOP_K,
        # API
        "api_host": API_HOST,
        "api_port": API_PORT,
        "frontend_url": FRONTEND_URL,
        # Environnement
        "debug": DEBUG,
    }


# Création automatique des dossiers au chargement du module
_ensure_directories()

logger.debug("Configuration chargée depuis %s", _ROOT_DIR / ".env")
