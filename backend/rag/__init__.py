"""Package RAG — système de Retrieval-Augmented Generation."""

# Imports lazy pour éviter les erreurs circulaires
# Utiliser : from backend.rag.embeddings import get_embedding_model
# Utiliser : from backend.rag.retriever import search

__all__ = ["embeddings", "ingest", "retriever"]
