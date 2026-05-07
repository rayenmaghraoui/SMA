"""
Connexion DuckDB en mémoire — charge les 3 CSV comme tables SQL.

Tables disponibles :
    - finance   : données financières (revenue, cost, profit, growth_rate)
    - marketing : campagnes marketing (channel, budget, clicks, conversions)
    - support   : tickets support client (issue_type, resolution_hours, satisfaction_score)
"""

import logging
from typing import Optional

import duckdb
import pandas as pd

from backend.config import FINANCE_CSV, MARKETING_CSV, SUPPORT_CSV

logger = logging.getLogger(__name__)

# Connexion singleton
_connection: Optional[duckdb.DuckDBPyConnection] = None


def get_connection() -> duckdb.DuckDBPyConnection:
    """
    Retourne la connexion DuckDB singleton.
    Crée et initialise la connexion si elle n'existe pas encore.
    """
    global _connection
    if _connection is None:
        _connection = _create_connection()
    return _connection


def _create_connection() -> duckdb.DuckDBPyConnection:
    """Crée une base DuckDB en mémoire et charge les 3 CSV."""
    conn = duckdb.connect(":memory:")

    for table_name, csv_path in [
        ("finance", FINANCE_CSV),
        ("marketing", MARKETING_CSV),
        ("support", SUPPORT_CSV),
    ]:
        try:
            df = pd.read_csv(csv_path)
            conn.register(table_name, df)
            logger.info("Table DuckDB '%s' chargée — %d lignes", table_name, len(df))
        except FileNotFoundError:
            logger.warning(
                "Fichier introuvable : %s — table '%s' non disponible", csv_path, table_name
            )
        except Exception as e:
            logger.error("Erreur chargement table '%s': %s", table_name, e)

    return conn


def reset_connection() -> None:
    """
    Réinitialise la connexion DuckDB.
    À appeler après un upload de nouveaux fichiers CSV.
    """
    global _connection
    _connection = None
    logger.info("Connexion DuckDB réinitialisée")


def get_schema() -> str:
    """
    Retourne le schéma des tables disponibles pour le prompt LLM.

    Returns:
        Description textuelle des tables et colonnes.
    """
    conn = get_connection()
    lines = []

    for table_name in ("finance", "marketing", "support"):
        try:
            result = conn.execute(f"DESCRIBE {table_name}").fetchall()
            cols = ", ".join(f"{row[0]} ({row[1]})" for row in result)
            lines.append(f"Table '{table_name}': {cols}")
        except Exception:
            pass

    return "\n".join(lines) if lines else "Aucune table disponible."
