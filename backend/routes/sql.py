"""
Route POST /sql/query — exploration de données via SQL généré par le LLM.
Route POST /sql/query/export — téléchargement des résultats en CSV.

Sécurité : seuls les SELECT sont autorisés (voir sql_agent/validator.py).
"""

import csv
import io
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from backend.models.request_models import SqlQueryRequest
from backend.models.response_models import ChartData, SqlQueryResponse
from backend.sql_agent.executor import execute_sql
from backend.sql_agent.generator import generate_sql

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sql", tags=["SQL Agent"])


@router.post("/query", response_model=SqlQueryResponse)
async def sql_query(request: SqlQueryRequest) -> SqlQueryResponse:
    """
    Génère une requête SQL depuis une question en langage naturel,
    l'exécute sur les datasets SMA (finance / marketing / support)
    et retourne les résultats avec données graphique.

    Args:
        request: Question en langage naturel.

    Returns:
        SqlQueryResponse avec SQL généré, résultats et données graphique.
    """
    errors: List[str] = []
    sql = ""

    # Étape 1 : génération SQL + viz_type depuis la question
    try:
        sql, viz_type = await generate_sql(request.question)
    except Exception as e:
        errors.append(f"Erreur génération SQL : {str(e)}")
        return SqlQueryResponse(
            success=False,
            question=request.question,
            sql="",
            rows_preview=[],
            total_rows=0,
            csv_path=None,
            chart_data=None,
            message="Impossible de générer la requête SQL. Vérifiez que les données sont chargées.",
            errors=errors,
        )

    # Étape 2 : exécution sécurisée
    rows, exec_errors = await execute_sql(sql)
    errors.extend(exec_errors)

    if exec_errors:
        return SqlQueryResponse(
            success=False,
            question=request.question,
            sql=sql,
            rows_preview=[],
            total_rows=0,
            csv_path=None,
            chart_data=None,
            message=exec_errors[0],
            errors=errors,
        )

    # Étape 3 : construire les données graphique selon viz_type
    chart_data = _build_chart_data(rows, viz_type)

    logger.info(
        "SQL query OK — question='%.60s' — %d lignes", request.question, len(rows)
    )

    return SqlQueryResponse(
        success=True,
        question=request.question,
        sql=sql,
        rows_preview=rows[:100],
        total_rows=len(rows),
        csv_path=f"/sql/query/export",  # URL relative pour le bouton download
        chart_data=chart_data,
        message=f"{len(rows)} ligne(s) retournée(s).",
        errors=errors,
    )


@router.post("/query/export")
async def sql_query_export(request: SqlQueryRequest) -> StreamingResponse:
    """
    Génère, exécute et exporte les résultats en CSV téléchargeable.

    Args:
        request: Question en langage naturel.

    Returns:
        Fichier CSV en streaming.
    """
    try:
        sql, _ = await generate_sql(request.question)
        rows, _ = await execute_sql(sql)
    except Exception as e:
        logger.error("Erreur export CSV: %s", e)
        rows = [{"error": str(e)}]

    if not rows:
        rows = [{"message": "Aucun résultat"}]

    # Générer le CSV en mémoire
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="resultats.csv"'},
    )


def _build_chart_data(rows: List[Dict[str, Any]], viz_type: str = "table") -> Optional[ChartData]:
    """
    Construit les données graphique pour Recharts depuis les résultats SQL.

    Adapté du visual_generator.py du projet sql_agent original,
    mais retourne des données JSON (pas de PNG matplotlib).

    viz_type supportés : bar, line, pie, scatter, table.
    Pour "table", retourne None (le frontend affiche directement le tableau).

    Args:
        rows: Résultats de la requête SQL.
        viz_type: Type de visualisation recommandé par le LLM.

    Returns:
        ChartData pour Recharts, ou None si tableau ou données insuffisantes.
    """
    if viz_type == "table" or not rows or len(rows[0]) < 2:
        return None

    keys = list(rows[0].keys())

    # Détecter les colonnes numériques
    numeric_cols = [
        k for k in keys
        if isinstance(rows[0].get(k), (int, float)) and rows[0].get(k) is not None
    ]

    if not numeric_cols:
        return None

    # Axe X = première colonne non numérique
    x_col = next((k for k in keys if k not in numeric_cols), keys[0])

    # Pour pie : une seule série (première colonne numérique)
    if viz_type == "pie":
        y_cols = [numeric_cols[0]]
    elif viz_type == "scatter":
        y_cols = numeric_cols[:2]  # X et Y pour le scatter
    else:
        y_cols = [c for c in numeric_cols if c != x_col][:3]  # Max 3 séries

    if not y_cols:
        return None

    # Convertir en types JSON-compatibles
    chart_rows = []
    for row in rows[:50]:
        point: Dict[str, Any] = {x_col: str(row.get(x_col, ""))}
        for y in y_cols:
            val = row.get(y)
            point[y] = round(float(val), 2) if val is not None else 0
        chart_rows.append(point)

    return ChartData(x_key=x_col, y_keys=y_cols, data=chart_rows)
