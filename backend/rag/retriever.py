"""
Retriever — recherche de similarité dans ChromaDB.

Ce module fournit une fonction de recherche sémantique dans la base
vectorielle des guides tunisiens indexés.

Méthode : similarité cosinus sur les embeddings sentence-t5-base.
Top-k : configurable (défaut = 3 via RAG_TOP_K).
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from langchain_chroma import Chroma

from backend.config import CHROMA_DB_PATH, RAG_TOP_K
from backend.rag.embeddings import get_embedding_model

logger = logging.getLogger(__name__)

# Nom de la collection (doit correspondre à ingest.py)
COLLECTION_NAME = "guides_tunisiens"

# Cache du vectorstore
_vectorstore: Optional[Chroma] = None


def _get_vectorstore() -> Chroma:
    """
    Charge ou retourne le vectorstore ChromaDB.

    Returns:
        Instance Chroma connectée à la collection des guides.

    Raises:
        FileNotFoundError: Si la base ChromaDB n'existe pas.
    """
    global _vectorstore

    if _vectorstore is not None:
        return _vectorstore

    persist_path = str(CHROMA_DB_PATH)

    if not Path(persist_path).exists():
        raise FileNotFoundError(
            f"Base ChromaDB non trouvée : {persist_path}. "
            "Lancez d'abord 'python -m backend.rag.ingest' pour indexer les documents."
        )

    logger.info("Chargement de la collection ChromaDB '%s'...", COLLECTION_NAME)

    embedding_model = get_embedding_model()

    _vectorstore = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embedding_model,
        persist_directory=persist_path,
    )

    logger.info("Collection chargée avec succès")
    return _vectorstore


def search(query: str, k: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Recherche les k documents les plus pertinents pour une query.

    Utilise la similarité cosinus sur les embeddings sentence-t5-base
    pour trouver les passages les plus proches sémantiquement.

    Args:
        query: Requête textuelle en français.
        k: Nombre de résultats à retourner (défaut: RAG_TOP_K = 3).

    Returns:
        Liste de dictionnaires contenant :
            - page_content : texte du chunk
            - source : nom du fichier d'origine
            - section : section du document (si disponible)
            - sous_section : sous-section (si disponible)
            - score : score de similarité (0-1)

    Example:
        >>> results = search("gestion financière PME Tunisie")
        >>> for r in results:
        ...     print(f"[{r['source']}] {r['page_content'][:100]}...")
    """
    if k is None:
        k = RAG_TOP_K

    logger.debug("Recherche RAG : '%s' (top-%d)", query[:50], k)

    try:
        vectorstore = _get_vectorstore()

        # Recherche avec scores
        results_with_scores = vectorstore.similarity_search_with_score(
            query=query,
            k=k,
        )

        formatted_results: List[Dict[str, Any]] = []

        for doc, score in results_with_scores:
            result = {
                "page_content": doc.page_content,
                "source": doc.metadata.get("source", "inconnu"),
                "titre": doc.metadata.get("titre", ""),
                "section": doc.metadata.get("section", ""),
                "sous_section": doc.metadata.get("sous_section", ""),
                # ChromaDB retourne une distance, on la convertit en similarité
                # Plus le score est bas, plus c'est similaire
                "score": round(1 - score, 4) if score <= 1 else round(1 / (1 + score), 4),
            }
            formatted_results.append(result)

        logger.debug("  → %d résultats trouvés", len(formatted_results))

        return formatted_results

    except FileNotFoundError as e:
        logger.error("Base RAG non initialisée : %s", e)
        return []

    except Exception as e:
        logger.exception("Erreur lors de la recherche RAG : %s", e)
        return []


def search_with_filter(
    query: str,
    source_filter: Optional[str] = None,
    k: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Recherche avec filtrage par source.

    Permet de limiter la recherche à un guide spécifique.

    Args:
        query: Requête textuelle.
        source_filter: Nom du fichier source (ex: "guide_gestion_financiere_tunisie.md").
        k: Nombre de résultats.

    Returns:
        Liste de résultats filtrés.
    """
    if k is None:
        k = RAG_TOP_K

    logger.debug(
        "Recherche RAG filtrée : '%s' (source=%s, top-%d)",
        query[:50], source_filter, k
    )

    try:
        vectorstore = _get_vectorstore()

        # Construire le filtre
        where_filter = None
        if source_filter:
            where_filter = {"source": source_filter}

        results_with_scores = vectorstore.similarity_search_with_score(
            query=query,
            k=k,
            filter=where_filter,
        )

        formatted_results = []
        for doc, score in results_with_scores:
            result = {
                "page_content": doc.page_content,
                "source": doc.metadata.get("source", "inconnu"),
                "titre": doc.metadata.get("titre", ""),
                "section": doc.metadata.get("section", ""),
                "sous_section": doc.metadata.get("sous_section", ""),
                "score": round(1 - score, 4) if score <= 1 else round(1 / (1 + score), 4),
            }
            formatted_results.append(result)

        return formatted_results

    except Exception as e:
        logger.exception("Erreur lors de la recherche RAG filtrée : %s", e)
        return []


def get_collection_stats() -> Dict[str, Any]:
    """
    Retourne des statistiques sur la collection indexée.

    Returns:
        Dictionnaire avec le nombre de documents, les sources, etc.
    """
    try:
        vectorstore = _get_vectorstore()
        collection = vectorstore._collection

        return {
            "collection_name": COLLECTION_NAME,
            "document_count": collection.count(),
            "persist_directory": str(CHROMA_DB_PATH),
        }

    except Exception as e:
        logger.error("Impossible de récupérer les stats : %s", e)
        return {
            "error": str(e),
            "collection_name": COLLECTION_NAME,
        }
