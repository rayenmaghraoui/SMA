"""
Connexion DuckDB en mémoire — charge les 5 CSV comme tables SQL.

Tables disponibles :
    - ventes     : transactions de vente (product_name, category, revenue_tnd, customer_region...)
    - regions    : analyse par région (customer_region, CA_Total, Profit_Total...)
    - categories : analyse par catégorie (category, CA_Total, Profit_Total...)
    - canaux     : analyse par canal de vente (sales_channel, CA_Total, Nb_Transactions...)
    - kpis       : indicateurs globaux (Indicateur, Valeur)
"""

import logging
from typing import Optional

import duckdb
import pandas as pd

from backend.config import DATA_DIR

logger = logging.getLogger(__name__)

# Connexion singleton
_connection: Optional[duckdb.DuckDBPyConnection] = None

# Mapping table_name → fichier CSV
_TABLES = {
    "ventes":     DATA_DIR / "uploads" / "01_donnees_vente.csv",
    "regions":    DATA_DIR / "uploads" / "02_analyse_region.csv",
    "categories": DATA_DIR / "uploads" / "03_analyse_categorie.csv",
    "canaux":     DATA_DIR / "uploads" / "04_analyse_canaux.csv",
    "kpis":       DATA_DIR / "uploads" / "05_kpis_globaux.csv",
}


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
    """Crée une base DuckDB en mémoire et charge les 5 CSV."""
    conn = duckdb.connect(":memory:")

    for table_name, csv_path in _TABLES.items():
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

    for table_name in _TABLES:
        try:
            result = conn.execute(f"DESCRIBE {table_name}").fetchall()
            cols = ", ".join(f"{row[0]} ({row[1]})" for row in result)
            lines.append(f"Table '{table_name}': {cols}")
        except Exception:
            pass

    return "\n".join(lines) if lines else "Aucune table disponible."
