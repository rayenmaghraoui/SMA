"""
Route /upload — gestion de l'upload de fichiers CSV.

Cette route permet aux utilisateurs d'uploader leurs propres fichiers
CSV pour analyse personnalisée.
"""

import logging
from pathlib import Path
from typing import List

import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.config import UPLOADS_DIR
from backend.models.response_models import UploadResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["Upload"])

# Colonnes attendues par type de fichier (correspondance par similarité ≥70%)
EXPECTED_COLUMNS = {
    "ventes": [
        "invoice_id", "product_name", "category", "quantity",
        "unit_price_tnd", "revenue_tnd", "customer_id", "customer_region",
        "sale_date", "sales_channel", "payment_method", "estimated_profit",
    ],
    "regions": [
        "customer_region", "ca_total", "profit_total",
        "nb_transactions", "panier_moyen",
    ],
    "categories": [
        "category", "ca_total", "profit_total",
        "nb_transactions", "quantite_vendue", "prix_moyen",
    ],
    "canaux": [
        "sales_channel", "ca_total", "nb_transactions", "panier_moyen",
    ],
    "kpis": [
        "indicateur", "valeur",
    ],
}

# Taille maximale: 10 MB
MAX_FILE_SIZE = 10 * 1024 * 1024


def _detect_file_type(columns: List[str]) -> str:
    """
    Détecte le type de fichier basé sur les colonnes.

    Args:
        columns: Liste des noms de colonnes.

    Returns:
        Type de fichier ("finance", "marketing", "support", "unknown").
    """
    columns_set = set(col.lower().strip() for col in columns)

    for file_type, expected_cols in EXPECTED_COLUMNS.items():
        expected_set = set(col.lower() for col in expected_cols)
        # Match si au moins 70% des colonnes attendues sont présentes
        match_ratio = len(columns_set & expected_set) / len(expected_set)
        if match_ratio >= 0.7:
            return file_type

    return "unknown"


def _validate_csv(df: pd.DataFrame, file_type: str) -> List[str]:
    """
    Valide le contenu du CSV.

    Args:
        df: DataFrame chargé.
        file_type: Type de fichier détecté.

    Returns:
        Liste des erreurs de validation (vide si OK).
    """
    errors = []

    # Vérifier que le fichier n'est pas vide
    if df.empty:
        errors.append("Le fichier est vide.")
        return errors

    # Vérifications spécifiques par type
    if file_type == "finance":
        if "revenue" in df.columns:
            if (df["revenue"] < 0).any():
                errors.append("Certaines valeurs de 'revenue' sont négatives.")

    elif file_type == "marketing":
        if "conversion_rate" in df.columns:
            if (df["conversion_rate"] < 0).any() or (df["conversion_rate"] > 100).any():
                errors.append("'conversion_rate' doit être entre 0 et 100.")

    elif file_type == "support":
        if "satisfaction_score" in df.columns:
            if (df["satisfaction_score"] < 1).any() or (df["satisfaction_score"] > 5).any():
                errors.append("'satisfaction_score' doit être entre 1 et 5.")

    return errors


@router.post("/upload", response_model=UploadResponse)
async def upload_csv(file: UploadFile = File(...)) -> UploadResponse:
    """
    Upload un fichier CSV pour analyse.

    Le fichier est validé (format, colonnes, contenu) puis sauvegardé
    dans le dossier uploads pour utilisation ultérieure.

    Args:
        file: Fichier CSV uploadé (multipart/form-data).

    Returns:
        UploadResponse avec le nom du fichier, le type détecté et les colonnes.

    Raises:
        HTTPException 400: Si le fichier n'est pas un CSV valide.
        HTTPException 413: Si le fichier est trop volumineux.
    """
    logger.info("Upload de fichier: %s", file.filename)

    # Vérifier l'extension
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Seuls les fichiers CSV sont acceptés."
        )

    # Lire le contenu
    try:
        content = await file.read()

        # Vérifier la taille
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"Fichier trop volumineux. Maximum: {MAX_FILE_SIZE // (1024*1024)} MB."
            )

        # Charger avec pandas
        from io import BytesIO
        df = pd.read_csv(BytesIO(content))

    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="Le fichier CSV est vide.")
    except pd.errors.ParserError as e:
        raise HTTPException(status_code=400, detail=f"Erreur de parsing CSV: {str(e)}")
    except Exception as e:
        logger.exception("Erreur lors de la lecture du fichier")
        raise HTTPException(status_code=400, detail=f"Erreur: {str(e)}")

    # Détecter le type de fichier
    columns = df.columns.tolist()
    file_type = _detect_file_type(columns)

    logger.info(
        "Fichier détecté: type=%s, colonnes=%d, lignes=%d",
        file_type, len(columns), len(df)
    )

    # Valider le contenu
    validation_errors = _validate_csv(df, file_type)

    if validation_errors:
        logger.warning("Erreurs de validation: %s", validation_errors)

    # Sauvegarder le fichier
    save_path = UPLOADS_DIR / file.filename
    with open(save_path, "wb") as f:
        f.write(content)

    logger.info("Fichier sauvegardé: %s", save_path)

    return UploadResponse(
        success=True,
        filename=file.filename,
        file_type=file_type,
        dataset_type=file_type,
        columns=columns,
        row_count=len(df),
        rows=len(df),
        validation_errors=validation_errors,
        message=f"Fichier uploadé avec succès ({len(df)} lignes).",
    )


@router.get("/uploads")
async def list_uploads() -> dict:
    """
    Liste les fichiers uploadés disponibles.

    Returns:
        Liste des fichiers dans le dossier uploads.
    """
    files = []

    for f in UPLOADS_DIR.glob("*.csv"):
        files.append({
            "filename": f.name,
            "size": f.stat().st_size,
            "modified": f.stat().st_mtime,
        })

    return {
        "files": files,
        "count": len(files),
    }
