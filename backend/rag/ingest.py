"""
Ingestion des documents — stratégie hybride en 2 passes.

Ce module charge les 5 guides tunisiens (fichiers Markdown) et les
indexe dans ChromaDB avec une stratégie de chunking optimisée.

Stratégie de chunking :
    Passe 1 — MarkdownHeaderTextSplitter
        Découpe par sections logiques (titres Markdown #, ##, ###)
        Chaque chunk parle d'un seul sujet cohérent.

    Passe 2 — RecursiveCharacterTextSplitter
        Re-découpe les sections trop longues.
        chunk_size=500, chunk_overlap=50
        Garantit que chaque chunk ≤ 512 tokens (limite T5).

Métadonnées stockées :
    - titre : titre principal du document (H1)
    - section : section (H2)
    - sous_section : sous-section (H3)
    - source : nom du fichier d'origine

Usage :
    python -m backend.rag.ingest
"""

import logging
import sys
from pathlib import Path
from typing import List, Dict, Any

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)
from langchain_chroma import Chroma
from langchain_core.documents import Document

from backend.config import (
    DOCUMENTS_DIR,
    CHROMA_DB_PATH,
    RAG_CHUNK_SIZE,
    RAG_CHUNK_OVERLAP,
)
from backend.rag.embeddings import get_embedding_model

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Configuration du MarkdownHeaderTextSplitter
HEADERS_TO_SPLIT_ON = [
    ("#", "titre"),
    ("##", "section"),
    ("###", "sous_section"),
]

# Collection ChromaDB
COLLECTION_NAME = "guides_tunisiens"


def _load_markdown_files() -> List[Dict[str, Any]]:
    """
    Charge tous les fichiers .md depuis DOCUMENTS_DIR.

    Returns:
        Liste de dicts {"content": str, "source": str}.
    """
    documents = []
    md_files = list(DOCUMENTS_DIR.glob("*.md"))

    if not md_files:
        logger.warning("Aucun fichier .md trouvé dans %s", DOCUMENTS_DIR)
        return documents

    logger.info("Chargement de %d fichiers Markdown...", len(md_files))

    for md_file in md_files:
        try:
            content = md_file.read_text(encoding="utf-8")
            documents.append({
                "content": content,
                "source": md_file.name,
            })
            logger.debug("  ✓ %s (%d caractères)", md_file.name, len(content))
        except Exception as e:
            logger.error("  ✗ Erreur lors du chargement de %s : %s", md_file.name, e)

    return documents


def _split_markdown_by_headers(content: str, source: str) -> List[Document]:
    """
    Passe 1 : découpe le Markdown par sections (headers).

    Args:
        content: Contenu brut du fichier Markdown.
        source: Nom du fichier source.

    Returns:
        Liste de Documents avec métadonnées de section.
    """
    splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=HEADERS_TO_SPLIT_ON,
        strip_headers=False,  # Garde les headers dans le contenu
    )

    splits = splitter.split_text(content)

    # Ajouter la source aux métadonnées
    for doc in splits:
        doc.metadata["source"] = source

    return splits


def _split_long_chunks(documents: List[Document]) -> List[Document]:
    """
    Passe 2 : re-découpe les chunks trop longs.

    Garantit que chaque chunk fait au maximum RAG_CHUNK_SIZE caractères
    (avec un overlap de RAG_CHUNK_OVERLAP pour le contexte).

    Args:
        documents: Documents issus de la passe 1.

    Returns:
        Documents re-découpés si nécessaire.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=RAG_CHUNK_SIZE,
        chunk_overlap=RAG_CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " "],
        length_function=len,
    )

    final_docs = []

    for doc in documents:
        if len(doc.page_content) > RAG_CHUNK_SIZE:
            # Re-découper ce chunk
            sub_chunks = splitter.split_text(doc.page_content)
            for chunk_text in sub_chunks:
                new_doc = Document(
                    page_content=chunk_text,
                    metadata=doc.metadata.copy(),
                )
                final_docs.append(new_doc)
        else:
            final_docs.append(doc)

    return final_docs


def ingest_documents() -> Dict[str, int]:
    """
    Exécute le pipeline complet d'ingestion.

    1. Charge les fichiers .md depuis DOCUMENTS_DIR
    2. Applique le chunking hybride (headers + recursive)
    3. Génère les embeddings via sentence-t5-base
    4. Stocke dans ChromaDB

    Returns:
        Dictionnaire {nom_fichier: nombre_chunks} pour chaque document.
    """
    logger.info("=== Début de l'ingestion des documents ===")
    logger.info("Dossier source : %s", DOCUMENTS_DIR)
    logger.info("Base ChromaDB : %s", CHROMA_DB_PATH)

    # Charger les fichiers Markdown
    raw_documents = _load_markdown_files()

    if not raw_documents:
        logger.error("Aucun document à ingérer. Abandon.")
        return {}

    # Chunking hybride
    all_chunks: List[Document] = []
    chunks_per_file: Dict[str, int] = {}

    for doc in raw_documents:
        source = doc["source"]
        content = doc["content"]

        # Passe 1 : split par headers
        header_chunks = _split_markdown_by_headers(content, source)
        logger.debug("  [%s] Passe 1 : %d sections", source, len(header_chunks))

        # Passe 2 : re-split les chunks trop longs
        final_chunks = _split_long_chunks(header_chunks)
        logger.debug("  [%s] Passe 2 : %d chunks finaux", source, len(final_chunks))

        all_chunks.extend(final_chunks)
        chunks_per_file[source] = len(final_chunks)

    logger.info("Total : %d chunks à indexer", len(all_chunks))

    # Charger le modèle d'embeddings
    embedding_model = get_embedding_model()

    # Supprimer l'ancienne collection si elle existe
    persist_path = str(CHROMA_DB_PATH)

    # Créer la nouvelle collection ChromaDB
    logger.info("Création de la collection ChromaDB '%s'...", COLLECTION_NAME)

    vectorstore = Chroma.from_documents(
        documents=all_chunks,
        embedding=embedding_model,
        collection_name=COLLECTION_NAME,
        persist_directory=persist_path,
    )

    logger.info("=== Ingestion terminée avec succès ===")

    # Afficher le résumé
    logger.info("Résumé par document :")
    for source, count in chunks_per_file.items():
        logger.info("  • %s : %d chunks", source, count)

    return chunks_per_file


def main() -> None:
    """Point d'entrée pour l'exécution en ligne de commande."""
    logger.info("Lancement de l'ingestion RAG...")

    try:
        result = ingest_documents()

        if result:
            print("\n[OK] Ingestion reussie !")
            print(f"  - {sum(result.values())} chunks indexes")
            print(f"  - Base ChromaDB : {CHROMA_DB_PATH}")
        else:
            print("\n[ERREUR] Aucun document ingere.")
            sys.exit(1)

    except Exception as e:
        logger.exception("Erreur fatale lors de l'ingestion : %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
