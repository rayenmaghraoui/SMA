"""
Route /report — récupération du dernier rapport généré.

Cette route permet de récupérer le rapport complet de la dernière
analyse effectuée.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException

from backend.config import DATA_DIR

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["Report"])

# Stockage en mémoire du dernier rapport
_last_report: Optional[Dict[str, Any]] = None

# Chemin du fichier de sauvegarde
REPORT_FILE = DATA_DIR / "last_report.json"


def save_report(report: Dict[str, Any]) -> None:
    """
    Sauvegarde le rapport en mémoire et sur disque.

    Args:
        report: Rapport à sauvegarder.
    """
    global _last_report
    _last_report = report

    # Sauvegarder aussi sur disque
    try:
        with open(REPORT_FILE, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        logger.info("Rapport sauvegardé: %s", REPORT_FILE)
    except Exception as e:
        logger.warning("Impossible de sauvegarder le rapport: %s", e)


def get_last_report() -> Optional[Dict[str, Any]]:
    """
    Récupère le dernier rapport (mémoire ou disque).

    Returns:
        Dernier rapport ou None si aucun.
    """
    global _last_report

    if _last_report is not None:
        return _last_report

    # Essayer de charger depuis le disque
    if REPORT_FILE.exists():
        try:
            with open(REPORT_FILE, "r", encoding="utf-8") as f:
                _last_report = json.load(f)
            return _last_report
        except Exception as e:
            logger.warning("Impossible de charger le rapport: %s", e)

    return None


@router.get("/report")
async def get_report() -> dict:
    """
    Récupère le dernier rapport généré.

    Returns:
        Le rapport complet avec toutes les sections.

    Raises:
        HTTPException 404: Si aucun rapport n'est disponible.
    """
    report = get_last_report()

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Aucun rapport disponible. Lancez d'abord une analyse via /analyze ou /chat."
        )

    return {
        "success": True,
        "report": report,
    }


@router.get("/report/latest")
async def get_report_latest() -> dict:
    """
    Récupère le dernier rapport sans erreur 404 si absent.

    Returns:
        Un objet indiquant si un rapport est disponible.
    """
    report = get_last_report()

    if report is None:
        return {
            "success": True,
            "has_report": False,
            "report": None,
        }

    return {
        "success": True,
        "has_report": True,
        "report": report,
    }


@router.get("/report/summary")
async def get_report_summary() -> dict:
    """
    Récupère un résumé du dernier rapport.

    Version allégée avec seulement les informations essentielles.

    Returns:
        Résumé du rapport.
    """
    report = get_last_report()

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Aucun rapport disponible."
        )

    # Extraire les informations clés
    recommendations = report.get("recommendations", [])
    high_priority = [r for r in recommendations if r.get("priorite", 5) <= 2]

    return {
        "success": True,
        "summary": {
            "resume_executif": report.get("resume_executif", ""),
            "nombre_anomalies": report.get("anomalies", {}).get("total", 0),
            "nombre_recommandations": len(recommendations),
            "recommandations_prioritaires": high_priority,
            "date_generation": report.get("metadata", {}).get("date_generation", ""),
        },
    }


@router.get("/report/recommendations")
async def get_recommendations() -> dict:
    """
    Récupère uniquement les recommandations du dernier rapport.

    Returns:
        Liste des recommandations triées par priorité.
    """
    report = get_last_report()

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Aucun rapport disponible."
        )

    recommendations = report.get("recommendations", [])

    return {
        "success": True,
        "recommendations": recommendations,
        "count": len(recommendations),
    }


@router.get("/report/kpis")
async def get_report_kpis() -> dict:
    """
    Récupère uniquement les KPIs du dernier rapport.

    Returns:
        KPIs structurés par domaine.
    """
    report = get_last_report()

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Aucun rapport disponible."
        )

    return {
        "success": True,
        "kpis": report.get("kpis", {}),
    }


@router.delete("/report")
async def delete_report() -> dict:
    """
    Supprime le rapport actuel.

    Returns:
        Confirmation de suppression.
    """
    global _last_report
    _last_report = None

    if REPORT_FILE.exists():
        REPORT_FILE.unlink()
        logger.info("Rapport supprimé: %s", REPORT_FILE)

    return {
        "success": True,
        "message": "Rapport supprimé.",
    }
