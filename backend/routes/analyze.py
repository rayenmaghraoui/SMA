"""
Route /analyze \u2014 lance l'analyse compl\u00e8te des donn\u00e9es.

Cette route d\u00e9clenche le pipeline LangGraph et retourne les KPIs
calcul\u00e9s ainsi que les anomalies d\u00e9tect\u00e9es.
"""

import logging

from fastapi import APIRouter, HTTPException

from backend.agents.graph import run_graph_async
from backend.analysis import loader
from backend.models.request_models import AnalyzeRequest
from backend.models.response_models import AnalyzeResponse
from backend.routes.report import save_report

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Analyse"])


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_data(request: AnalyzeRequest = AnalyzeRequest()) -> AnalyzeResponse:
    """
    Lance l'analyse compl\u00e8te des donn\u00e9es d'entreprise.

    Cette route :
        1. Charge les trois datasets (finance, marketing, support)
        2. Calcule les KPIs de chaque domaine
        3. D\u00e9tecte les anomalies via la m\u00e9thode IQR
        4. Retourne les r\u00e9sultats en JSON

    Args:
        request: Configuration de l'analyse.
                 - use_defaults=True : utilise les CSV dans data/
                 - use_defaults=False : utilise les fichiers upload\u00e9s

    Returns:
            # Utiliser les CSV uploadés depuis data/uploads/.
            uploaded_datasets = loader.load_uploaded_datasets()
            serialized_raw_data = {
                key: df.to_dict(orient="records")
                for key, df in uploaded_datasets.items()
            }
            final_state = await run_graph_async(raw_data=serialized_raw_data)
    """
    logger.info("Re\u00e7u POST /analyze \u2014 use_defaults=%s", request.use_defaults)

    try:
        # Lancer le pipeline LangGraph (version async)
        if request.use_defaults:
            # Utiliser les donn\u00e9es par d\u00e9faut
            final_state = await run_graph_async(raw_data=None)
        else:
            # TODO Phase 3 : supporter les fichiers upload\u00e9s
            # Pour l'instant, m\u00eame comportement que use_defaults=True
            logger.warning("use_defaults=False non impl\u00e9ment\u00e9, utilisation des d\u00e9fauts")
            final_state = await run_graph_async(raw_data=None)

        # V\u00e9rifier s'il y a eu des erreurs bloquantes
        errors = final_state.get("errors", [])
        kpis = final_state.get("kpis", {})
        anomalies = final_state.get("anomalies", [])
        report = final_state.get("report", {})

        if report:
            try:
                save_report(report)
            except Exception as e:
                logger.warning("Impossible de sauvegarder le rapport après /analyze: %s", e)

        # D\u00e9terminer le succ\u00e8s
        has_kpis = bool(kpis)
        success = has_kpis and len(errors) == 0

        # Message descriptif
        if success:
            message = f"Analyse termin\u00e9e avec succ\u00e8s. {len(anomalies)} anomalie(s) d\u00e9tect\u00e9e(s)."
        elif has_kpis:
            message = f"Analyse termin\u00e9e avec {len(errors)} avertissement(s)."
        else:
            message = "L'analyse a \u00e9chou\u00e9. V\u00e9rifiez les erreurs."

        logger.info("Analyse termin\u00e9e \u2014 success=%s, anomalies=%d", success, len(anomalies))

        return AnalyzeResponse(
            success=success,
            kpis=kpis,
            anomalies=anomalies,
            errors=errors,
            message=message,
        )

    except FileNotFoundError as e:
        logger.error("Fichier introuvable : %s", e)
        raise HTTPException(
            status_code=404,
            detail=f"Fichier de donn\u00e9es introuvable : {e}"
        )

    except Exception as e:
        logger.exception("Erreur lors de l'analyse : %s", e)
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'analyse : {str(e)}"
        )
