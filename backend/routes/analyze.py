"""
Route /analyze — lance l'analyse complète des données.

Cette route déclenche le pipeline LangGraph et retourne les KPIs
calculés ainsi que les anomalies détectées.
"""

import logging

from fastapi import APIRouter, HTTPException

from backend.agents.graph import run_graph_async
from backend.analysis import loader
from backend.analysis.cache import get_cached_result, save_to_cache
from backend.models.request_models import AnalyzeRequest
from backend.models.response_models import AnalyzeResponse
from backend.routes.report import save_report

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Analyse"])


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_data(request: AnalyzeRequest = AnalyzeRequest()) -> AnalyzeResponse:
    """
    Lance l'analyse complète des données d'entreprise.

    Cette route :
        1. Vérifie le cache (retourne immédiatement si les CSV n'ont pas changé)
        2. Sinon, lance le pipeline LangGraph (5 agents)
        3. Calcule les KPIs de chaque domaine
        4. Détecte les anomalies via la méthode IQR
        5. Sauvegarde le résultat en cache et retourne les résultats en JSON

    Args:
        request: Configuration de l'analyse.
                 - use_defaults=True : utilise les CSV dans data/
                 - use_defaults=False : utilise les fichiers uploadés
    """
    logger.info("Reçu POST /analyze — use_defaults=%s", request.use_defaults)

    try:
        # ── Cache hit : retourner immédiatement sans relancer le pipeline ──
        # Ignoré si force=True (l'utilisateur demande explicitement une re-analyse)
        cached = None if request.force else get_cached_result()
        if cached:
            kpis      = cached.get("kpis", {})
            anomalies = cached.get("anomalies", [])
            report    = cached.get("report", {})
            if report:
                try:
                    save_report(report)
                except Exception:
                    pass
            return AnalyzeResponse(
                success=True,
                kpis=kpis,
                anomalies=anomalies,
                errors=[],
                message=f"Résultats chargés depuis le cache. {len(anomalies)} anomalie(s) détectée(s).",
            )

        # ── Cache miss : lancer le pipeline LangGraph ──
        if request.use_defaults:
            final_state = await run_graph_async(raw_data=None)
        else:
            logger.warning("use_defaults=False non implémenté, utilisation des défauts")
            final_state = await run_graph_async(raw_data=None)

        # Extraire les résultats
        errors    = final_state.get("errors", [])
        kpis      = final_state.get("kpis", {})
        anomalies = final_state.get("anomalies", [])
        report    = final_state.get("report", {})

        if report:
            try:
                save_report(report)
            except Exception as e:
                logger.warning("Impossible de sauvegarder le rapport après /analyze: %s", e)

        # Déterminer le succès (has_kpis doit être défini AVANT save_to_cache)
        has_kpis = bool(kpis)
        success  = has_kpis and len(errors) == 0

        # Mettre en cache si le pipeline a produit des KPIs
        if has_kpis:
            save_to_cache(final_state)

        # Message descriptif
        if success:
            message = f"Analyse terminée avec succès. {len(anomalies)} anomalie(s) détectée(s)."
        elif has_kpis:
            message = f"Analyse terminée avec {len(errors)} avertissement(s)."
        else:
            message = "L'analyse a échoué. Vérifiez les erreurs."

        logger.info("Analyse terminée — success=%s, anomalies=%d", success, len(anomalies))

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
            detail=f"Fichier de données introuvable : {e}"
        )

    except Exception as e:
        logger.exception("Erreur lors de l'analyse : %s", e)
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'analyse : {str(e)}"
        )
