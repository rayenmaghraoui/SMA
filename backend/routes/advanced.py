"""
Route /advanced — analyses avancées : prévisions et comparaison de périodes.

Ces endpoints exploitent le dataset des transactions (01_donnees_vente.csv)
pour fournir des analyses orientées aide à la décision, exposées dans la
page « Analyse avancée » du frontend.
"""

import logging

from fastapi import APIRouter, HTTPException

from backend.analysis import advanced_analyzer, loader
from backend.models.request_models import ComparePeriodsRequest, ForecastRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/advanced", tags=["Analyse avancée"])


def _load_ventes():
    """Charge le dataset des ventes ou lève une 404 si introuvable."""
    try:
        datasets = loader.load_datasets()
        return datasets["ventes"]
    except FileNotFoundError as e:
        logger.error("Dataset ventes introuvable : %s", e)
        raise HTTPException(
            status_code=404,
            detail="Dataset des ventes introuvable. Veuillez d'abord importer vos données.",
        )


@router.get("/date-range")
async def date_range() -> dict:
    """
    Retourne la plage de dates disponible dans le dataset des ventes.

    Utilisé par le frontend pour pré-remplir les sélecteurs de dates.
    """
    df_ventes = _load_ventes()
    try:
        return advanced_analyzer.get_date_range(df_ventes)
    except Exception as e:
        logger.exception("Erreur get_date_range : %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/forecast")
async def forecast(request: ForecastRequest = ForecastRequest()) -> dict:
    """
    Prévoit le chiffre d'affaires des prochains mois via régression linéaire.

    Args:
        request: Configuration (horizon en mois, défaut 3).

    Returns:
        Historique mensuel, prévisions encadrées et métadonnées (tendance, R²).
    """
    logger.info("Reçu POST /advanced/forecast — horizon=%d", request.horizon)
    df_ventes = _load_ventes()
    try:
        return advanced_analyzer.forecast_sales(df_ventes, horizon=request.horizon)
    except ValueError as e:
        logger.warning("Prévision impossible : %s", e)
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception("Erreur lors de la prévision : %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare")
async def compare(request: ComparePeriodsRequest) -> dict:
    """
    Compare les performances commerciales entre deux périodes.

    Args:
        request: Les quatre bornes de dates (périodes A et B).

    Returns:
        KPIs de chaque période, évolution en pourcentage et répartition
        par catégorie.
    """
    logger.info(
        "Reçu POST /advanced/compare — A=[%s→%s], B=[%s→%s]",
        request.period_a_start, request.period_a_end,
        request.period_b_start, request.period_b_end,
    )
    df_ventes = _load_ventes()
    try:
        return advanced_analyzer.compare_periods(
            df_ventes,
            request.period_a_start,
            request.period_a_end,
            request.period_b_start,
            request.period_b_end,
        )
    except ValueError as e:
        logger.warning("Comparaison impossible : %s", e)
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception("Erreur lors de la comparaison : %s", e)
        raise HTTPException(status_code=500, detail=str(e))