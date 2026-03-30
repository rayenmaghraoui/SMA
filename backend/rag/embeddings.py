"""
Configuration du modèle d'embeddings — sentence-T5-base.

Ce module fournit une instance singleton du modèle d'embeddings
utilisé pour l'indexation et la recherche dans ChromaDB.

Modèle : sentence-transformers/sentence-t5-base
    - Encodeur T5 fine-tuné pour la similarité sémantique
    - Dimension des vecteurs : 768
    - Limite : 512 tokens par chunk (ne pas dépasser)
"""

import logging
from functools import lru_cache
from typing import Optional

from langchain_huggingface import HuggingFaceEmbeddings

from backend.config import EMBEDDING_MODEL

logger = logging.getLogger(__name__)

# Instance globale (singleton)
_embedding_model: Optional[HuggingFaceEmbeddings] = None


@lru_cache(maxsize=1)
def get_embedding_model() -> HuggingFaceEmbeddings:
    """
    Retourne le modèle d'embeddings configuré pour le projet.

    Utilise sentence-transformers/sentence-t5-base avec :
        - normalize_embeddings=True : normalisation L2 des vecteurs
        - device=cpu : exécution sur CPU (compatible avec tous les environnements)
        - batch_size=32 : traitement par lots de 32 textes

    Le modèle est mis en cache (singleton) pour éviter les rechargements.

    Returns:
        Instance HuggingFaceEmbeddings prête à l'emploi.
    """
    logger.info("Chargement du modèle d'embeddings : %s", EMBEDDING_MODEL)

    model = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={
            "device": "cpu",
        },
        encode_kwargs={
            "normalize_embeddings": True,
            "batch_size": 32,
        },
    )

    logger.info("Modèle d'embeddings chargé avec succès (dimension: 768)")
    return model


def get_embedding_dimension() -> int:
    """
    Retourne la dimension des vecteurs d'embeddings.

    Pour sentence-t5-base, la dimension est toujours 768.

    Returns:
        768 (dimension fixe du modèle T5-base).
    """
    return 768
