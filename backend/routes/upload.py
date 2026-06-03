"""
Route /upload — gestion de l'upload de fichiers CSV avec normalisation sémantique.

Cette route accepte des CSV au schéma hétérogène et applique automatiquement
la couche de normalisation pour les rendre compatibles avec les analyzers
existants (kpis_analyzer, canaux_analyzer, categories_analyzer, ...).

Pipeline :
    1. Validation extension + taille
    2. Parsing CSV → DataFrame
    3. NormalizationPipeline → DataFrame normalisé + rapport
    4. Sauvegarde du fichier original ET du fichier normalisé
    5. Réponse avec métadonnées d'explicabilité
"""

import logging
from io import BytesIO
from pathlib import Path
from typing import List

import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.analysis.cache import invalidate_cache
from backend.config import UPLOADS_DIR
from backend.models.response_models import UploadResponse
from backend.normalization import NormalizationPipeline, NormalizationResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["Upload"])


# ============================================================
# Configuration
# ============================================================

# Taille maximale : 10 MB
MAX_FILE_SIZE = 10 * 1024 * 1024

# Mapping schéma → nom de fichier canonique attendu par loader.py
SCHEMA_TO_CANONICAL_FILENAME = {
    "ventes":     "01_donnees_vente.csv",
    "regions":    "02_analyse_region.csv",
    "categories": "03_analyse_categorie.csv",
    "canaux":     "04_analyse_canaux.csv",
    "kpis":       "05_kpis_globaux.csv",
}

# Pipeline singleton (instancié une seule fois pour réutiliser les embeddings)
_pipeline: NormalizationPipeline | None = None


def _get_pipeline() -> NormalizationPipeline:
    """Retourne le pipeline de normalisation (singleton)."""
    global _pipeline
    if _pipeline is None:
        _pipeline = NormalizationPipeline(
            use_semantic=True,
            use_llm_fallback=False,  # Activable via .env si besoin
        )
    return _pipeline


# ============================================================
# Route principale
# ============================================================


@router.post("/upload", response_model=UploadResponse)
async def upload_csv(file: UploadFile = File(...)) -> UploadResponse:
    """
    Upload un fichier CSV et le normalise automatiquement.

    Le fichier uploadé est analysé pour :
        - détecter son domaine métier (finance, marketing, sales, ...)
        - mapper ses colonnes vers les concepts canoniques internes
        - le transformer en un schéma compatible avec les analyzers

    Le fichier original est préservé. Une copie normalisée est sauvegardée
    sous le nom canonique attendu par le pipeline d'analyse.

    Args:
        file: Fichier CSV uploadé (multipart/form-data).

    Returns:
        UploadResponse avec métadonnées d'explicabilité :
            - file_type : schéma détecté ou "unknown"
            - columns   : colonnes du dataset normalisé
            - rows      : nombre de lignes
            - normalization_summary : explication user-friendly
            - mappings : détail des renommages appliqués (debug)

    Raises:
        HTTPException 400: Fichier non-CSV, vide ou malformé.
        HTTPException 413: Fichier trop volumineux.
    """
    logger.info("Upload de fichier : %s", file.filename)

    # ----- Validation extension -----
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Seuls les fichiers CSV sont acceptés.",
        )

    # ----- Lecture et taille -----
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=(
                f"Fichier trop volumineux. Maximum : "
                f"{MAX_FILE_SIZE // (1024 * 1024)} MB."
            ),
        )

    # ----- Parsing CSV -----
    try:
        df = pd.read_csv(BytesIO(content))
    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="Le fichier CSV est vide.")
    except pd.errors.ParserError as e:
        raise HTTPException(
            status_code=400, detail=f"Erreur de parsing CSV : {e}",
        )
    except Exception as e:
        logger.exception("Erreur lors de la lecture du fichier")
        raise HTTPException(status_code=400, detail=f"Erreur : {e}")

    if df.empty:
        raise HTTPException(status_code=400, detail="Le CSV ne contient aucune ligne.")

    # ----- Normalisation sémantique -----
    pipeline = _get_pipeline()
    try:
        result: NormalizationResult = pipeline.normalize(df)
    except Exception as e:
        logger.exception("Échec de la normalisation sémantique")
        # On ne bloque pas l'upload : le fichier original est gardé
        result = None  # type: ignore

    # ----- Sauvegarde -----
    # Toujours sauvegarder l'original sous son nom uploadé
    original_path = UPLOADS_DIR / file.filename
    original_path.write_bytes(content)
    logger.info("Original sauvegardé : %s", original_path)

    # Si la normalisation a réussi, sauvegarder aussi sous le nom canonique
    file_type = "unknown"
    normalized_columns: List[str] = list(df.columns)
    normalized_rows = len(df)
    validation_errors: List[str] = []
    normalization_summary = ""
    mappings_detail: List[dict] = []

    if result is not None:
        file_type = result.schema.name if result.schema else "unknown"
        normalization_summary = result.get_explanation()
        mappings_detail = [m.to_dict() for m in result.mappings]
        validation_errors = list(result.report.errors)

        if result.success and result.normalized_df is not None and result.schema:
            normalized_columns = list(result.normalized_df.columns)
            normalized_rows = len(result.normalized_df)

            canonical_name = SCHEMA_TO_CANONICAL_FILENAME.get(result.schema.name)
            if canonical_name:
                canonical_path = UPLOADS_DIR / canonical_name
                result.normalized_df.to_csv(canonical_path, index=False)
                logger.info(
                    "Version normalisée sauvegardée : %s (%d lignes)",
                    canonical_path, normalized_rows,
                )
        else:
            # Normalisation incomplète : ajouter les warnings/errors visibles
            validation_errors.extend(result.report.warnings)

    # Invalider le cache car les données ont changé
    invalidate_cache()

    return UploadResponse(
        success=True,
        filename=file.filename,
        file_type=file_type,
        dataset_type=file_type,
        columns=normalized_columns,
        row_count=normalized_rows,
        rows=normalized_rows,
        validation_errors=validation_errors,
        message=(
            normalization_summary
            or f"Fichier uploadé ({normalized_rows} lignes)."
        ),
        # Ces champs additionnels permettent au frontend d'afficher
        # l'explicabilité du mapping si le modèle de réponse le supporte.
        normalization_summary=normalization_summary,
        mappings=mappings_detail,
    )


# ============================================================
# Route de listing (inchangée)
# ============================================================


@router.get("/uploads")
async def list_uploads() -> dict:
    """
    Liste les fichiers uploadés disponibles.

    Returns:
        Liste des fichiers dans le dossier uploads avec leur taille
        et date de dernière modification.
    """
    files = []
    for f in UPLOADS_DIR.glob("*.csv"):
        files.append({
            "filename": f.name,
            "size": f.stat().st_size,
            "modified": f.stat().st_mtime,
        })

    return {"files": files, "count": len(files)}
