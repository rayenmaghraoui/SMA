"""
Validateur de sécurité SQL.

Règles de sécurité appliquées :
    1. Seules les requêtes SELECT sont autorisées.
    2. Les mots-clés dangereux (DROP, DELETE, UPDATE...) sont interdits.
    3. Un LIMIT maximum est imposé (MAX_ROWS = 500).
    4. Les commentaires SQL sont interdits (tentative d'injection).
    5. Pas de point-virgule multiple (séparation de requêtes).
"""

import logging
import re
from typing import Tuple

logger = logging.getLogger(__name__)

# Limite maximale de lignes retournées
MAX_ROWS: int = 500

# Mots-clés SQL dangereux interdits (liste exhaustive)
_FORBIDDEN_KEYWORDS: frozenset = frozenset({
    "DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE",
    "ATTACH", "DETACH", "CREATE", "REPLACE", "MERGE", "CALL",
    "EXEC", "EXECUTE", "GRANT", "REVOKE", "PRAGMA", "VACUUM",
    "COPY", "IMPORT", "EXPORT", "LOAD", "INSTALL", "UNLOAD",
    "CHECKPOINT", "FORCE", "ROLLBACK", "COMMIT", "BEGIN",
    "TRANSACTION", "SAVEPOINT",
})


def validate_sql(sql: str) -> Tuple[bool, str]:
    """
    Valide une requête SQL selon les règles de sécurité.

    Args:
        sql: Requête SQL à valider.

    Returns:
        (is_valid, error_message) — error_message est vide si valide.
    """
    sql_clean = sql.strip()

    if not sql_clean:
        return False, "La requête SQL est vide."

    # Règle 1 : doit commencer par SELECT
    if not re.match(r"^\s*SELECT\b", sql_clean, re.IGNORECASE):
        return False, "Seules les requêtes SELECT sont autorisées."

    # Règle 2 : pas de mots-clés dangereux
    tokens = set(re.findall(r"\b[A-Z_]+\b", sql_clean.upper()))
    forbidden_found = tokens & _FORBIDDEN_KEYWORDS
    if forbidden_found:
        return False, f"Mot-clé interdit détecté : {', '.join(sorted(forbidden_found))}"

    # Règle 3 : pas de commentaires SQL (-- ou /* */)
    if "--" in sql_clean or "/*" in sql_clean:
        return False, "Les commentaires SQL ne sont pas autorisés."

    # Règle 4 : pas de point-virgule multiple (injection par séparation)
    if sql_clean.count(";") > 1:
        return False, "Les requêtes multiples (point-virgule) ne sont pas autorisées."

    return True, ""


def enforce_limit(sql: str, max_rows: int = MAX_ROWS) -> str:
    """
    Impose un LIMIT sur la requête SQL.

    Si un LIMIT est déjà présent et supérieur à max_rows, il est réduit.
    Si aucun LIMIT n'est présent, il est ajouté.

    Args:
        sql: Requête SQL validée.
        max_rows: Limite maximale de lignes.

    Returns:
        Requête SQL avec LIMIT respecté.
    """
    sql_clean = sql.strip().rstrip(";")

    limit_match = re.search(r"\bLIMIT\s+(\d+)\b", sql_clean, re.IGNORECASE)

    if limit_match:
        existing = int(limit_match.group(1))
        if existing > max_rows:
            sql_clean = re.sub(
                r"\bLIMIT\s+\d+\b",
                f"LIMIT {max_rows}",
                sql_clean,
                flags=re.IGNORECASE,
            )
    else:
        sql_clean = f"{sql_clean} LIMIT {max_rows}"

    return sql_clean
