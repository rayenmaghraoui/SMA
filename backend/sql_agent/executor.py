"""
Exécution sécurisée des requêtes SQL avec timeout.

Utilise asyncio.wait_for pour le timeout et run_in_executor
car DuckDB est synchrone.
"""

import asyncio
import logging
from typing import Any, Dict, List, Tuple

from backend.sql_agent.db import get_connection
from backend.sql_agent.validator import enforce_limit, validate_sql

logger = logging.getLogger(__name__)

# Timeout d'exécution SQL en secondes
SQL_TIMEOUT_SECONDS: int = 10


async def execute_sql(sql: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Valide et exécute une requête SQL de manière sécurisée.

    Étapes :
        1. Validation de sécurité (SELECT only, mots-clés interdits)
        2. Application du LIMIT maximum
        3. Exécution avec timeout dans un thread séparé

    Args:
        sql: Requête SQL à exécuter.

    Returns:
        (rows, errors) — rows est la liste des résultats en dicts,
        errors est vide si succès.
    """
    errors: List[str] = []

    # Étape 1 : validation de sécurité
    is_valid, error_msg = validate_sql(sql)
    if not is_valid:
        logger.warning("Requête SQL refusée : %s — raison : %s", sql[:80], error_msg)
        return [], [error_msg]

    # Étape 2 : appliquer le LIMIT de sécurité
    sql_safe = enforce_limit(sql)

    # Étape 3 : exécution avec timeout
    try:
        rows = await asyncio.wait_for(
            _run_query(sql_safe),
            timeout=SQL_TIMEOUT_SECONDS,
        )
        logger.info("Requête exécutée avec succès — %d lignes", len(rows))
        return rows, []

    except asyncio.TimeoutError:
        msg = f"Timeout dépassé ({SQL_TIMEOUT_SECONDS}s) — requête trop complexe."
        logger.error(msg)
        return [], [msg]

    except Exception as e:
        msg = f"Erreur d'exécution SQL : {str(e)}"
        logger.error("Erreur SQL pour '%s': %s", sql[:80], e)
        return [], [msg]


async def _run_query(sql: str) -> List[Dict[str, Any]]:
    """
    Exécute la requête dans un thread séparé.
    DuckDB est synchrone, on évite de bloquer la boucle asyncio.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _sync_query, sql)


def _sync_query(sql: str) -> List[Dict[str, Any]]:
    """
    Exécution synchrone DuckDB.

    Args:
        sql: Requête SQL validée et limitée.

    Returns:
        Liste de dicts {colonne: valeur}.
    """
    conn = get_connection()
    result = conn.execute(sql)
    columns = [desc[0] for desc in result.description]
    rows = result.fetchall()
    return [dict(zip(columns, row)) for row in rows]
