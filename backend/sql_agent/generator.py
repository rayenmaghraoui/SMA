"""
Génération de requêtes SQL depuis une question en langage naturel.

Utilise DeepSeek-V3.2 via Azure AI Foundry.
Température 0.0 pour des requêtes déterministes et précises.
Retourne le SQL et le type de visualisation recommandé (viz_type).
"""

import json
import logging
import re
from typing import Tuple

from langchain_openai import ChatOpenAI

from backend.config import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_MODEL,
)
from backend.sql_agent.db import get_schema

logger = logging.getLogger(__name__)

# Types de visualisation valides (hérités du projet sql_agent original)
VIZ_TYPES = {"bar", "line", "pie", "scatter", "table"}

# Prompt système — adapté du projet original (Gemini → DeepSeek, SQLite → DuckDB)
_SYSTEM_PROMPT = """Tu es un expert SQL spécialisé dans DuckDB. Tu génères des requêtes SQL précises.

Schéma des tables disponibles :
{schema}

Règles strictes :
1. Génère UNIQUEMENT une requête SELECT valide pour DuckDB.
2. N'utilise JAMAIS : DROP, DELETE, UPDATE, INSERT, ALTER, TRUNCATE.
3. Utilise EXACTEMENT les noms de colonnes et de tables du schéma ci-dessus.
4. Les montants sont en Dinars Tunisiens (TND).
5. Si la question concerne plusieurs tables, utilise des JOINs ou sous-requêtes SELECT.
6. Par défaut, ajoute ORDER BY pertinent et LIMIT 100 si aucune limite n'est demandée.
7. Retourne UNIQUEMENT un JSON valide sur une seule ligne, sans markdown, sans explication :
{{
  "sql": "SELECT ...",
  "viz_type": "bar|line|pie|scatter|table"
}}
Choix de viz_type :
- "bar"     : comparaisons par catégories (canaux, types, campagnes...)
- "pie"     : répartitions en pourcentage
- "line"    : évolutions temporelles (par date, par mois...)
- "scatter" : corrélations entre deux valeurs numériques
- "table"   : listes brutes ou résultats multi-colonnes complexes
"""


def _get_llm() -> ChatOpenAI:
    """Instancie le LLM Azure pour la génération SQL."""
    return ChatOpenAI(
        base_url=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_API_KEY,
        model=AZURE_OPENAI_MODEL,
        temperature=0.0,
        max_tokens=512,
    )


def _parse_response(raw: str) -> Tuple[str, str]:
    """
    Parse la réponse JSON du LLM pour extraire sql et viz_type.

    Gestion robuste : si le JSON est malformé, extrait le SQL avec regex.

    Args:
        raw: Réponse brute du LLM.

    Returns:
        (sql, viz_type)
    """
    # Nettoyer les balises markdown
    clean = re.sub(r"```(?:json|sql)?\s*", "", raw, flags=re.IGNORECASE)
    clean = re.sub(r"```", "", clean).strip()

    try:
        data = json.loads(clean)
        sql = data.get("sql", "").strip().rstrip(";")
        viz_type = data.get("viz_type", "table").lower()
        if viz_type not in VIZ_TYPES:
            viz_type = "table"
        return sql, viz_type
    except json.JSONDecodeError:
        # Fallback : extraire le SQL brut si le JSON est cassé
        sql_match = re.search(r"SELECT\b.+", clean, re.IGNORECASE | re.DOTALL)
        sql = sql_match.group(0).strip().rstrip(";") if sql_match else ""
        return sql, "table"


async def generate_sql(question: str) -> Tuple[str, str]:
    """
    Génère une requête SQL et un type de visualisation depuis une question NL.

    Args:
        question: Question de l'utilisateur en français.

    Returns:
        (sql, viz_type) — sql prêt à être validé et exécuté.

    Raises:
        Exception: Si le LLM est inaccessible.
    """
    schema = get_schema()
    system_content = _SYSTEM_PROMPT.format(schema=schema)

    llm = _get_llm()

    try:
        response = await llm.ainvoke([
            {"role": "system", "content": system_content},
            {"role": "user", "content": question},
        ])
        sql, viz_type = _parse_response(response.content)
        logger.info(
            "SQL généré pour '%.60s': sql=%.80s viz=%s",
            question, sql, viz_type,
        )
        return sql, viz_type

    except Exception as e:
        logger.error("Erreur génération SQL pour '%.60s': %s", question, e)
        raise
