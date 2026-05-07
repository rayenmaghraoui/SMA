"""
Routeur d'intention — classifie une question comme "sql" ou "strategic".

Logique :
    - Score basé sur des patterns regex pour chaque intention.
    - L'intention avec le score le plus élevé gagne.
    - En cas d'égalité, l'intention "strategic" est privilégiée
      (comportement plus sûr : le pipeline LangGraph est plus complet).

Intentions :
    "sql"       → exploration de données, requêtes, agrégations, filtres
    "strategic" → recommandations, stratégie, interprétation, analyse globale
"""

import logging
import re
from typing import Literal

logger = logging.getLogger(__name__)

IntentType = Literal["sql", "strategic"]

# Patterns qui suggèrent une exploration de données → SQL agent
_SQL_PATTERNS: list = [
    r"\bmontre[z\s-]",
    r"\baffiche[z\s-]",
    r"\bliste[z\s-]",
    r"\btop\s+\d+",
    r"\bcombien\b",
    r"\btrie[z\s-]",
    r"\bclasse[z\s-]",
    r"\bmax(imum)?\b",
    r"\bmin(imum)?\b",
    r"\bmoyenne\b",
    r"\bsomme?\b",
    r"\btotal\b.{0,20}\bpar\b",
    r"\bpar\s+(mois|canal|type|campagne|semaine|churn|ticket)\b",
    r"\bcompar(e[z\s]|aison)\b",
    r"\bfiltre[z\s-]",
    r"\bsup[eé]rieur(e?\s+[aà])\b",
    r"\binf[eé]rieur(e?\s+[aà])\b",
    r"\btoutes?\s+les?\s+(lignes?|entr[eé]es?|tickets?|campagnes?)\b",
    r"\bselect\b",
    r"\bsql\b",
    r"\bexporte[z\s-]",
    r"\bt[eé]l[eé]charge[z\s-]",
    r"\bdonne[z\s-].{0,30}\bdonn[eé]es?\b",
    r"\bquel(le)?s?\s+sont\s+les?\s+\d+",
    r"\brang(s|er)?\b",
]

# Patterns qui suggèrent une analyse stratégique → pipeline LangGraph
_STRATEGIC_PATTERNS: list = [
    r"\brecommand",
    r"\bstrat[eé]gie\b",
    r"\bam[eé]liore[z\s-]",
    r"\bprobl[eè]me\b",
    r"\bsolution\b",
    r"\bconseille[z\s-]",
    r"\banalyse[z\s-]",
    r"\binterpr[eè]te[z\s-]",
    r"\bexplique[z\s-]",
    r"\bpourquoi\b",
    r"\bcomment\s+(am[eé]liorer|augmenter|r[eé]duire|optimiser)\b",
    r"\bque\s+(faire|pensez)\b",
    r"\bperformance[s]?\b.{0,20}\bglobal",
    r"\bbilan\b",
    r"\bperspective[s]?\b",
    r"\bopportunit[eé][s]?\b",
    r"\brisque[s]?\b",
    r"\baction[s]?\s+(prioritaire|concr[eè]te)\b",
    r"\bplan\s+d['']action\b",
]


def classify_intent(question: str) -> IntentType:
    """
    Classifie l'intention d'une question en langage naturel.

    Args:
        question: Question de l'utilisateur.

    Returns:
        "sql" pour une exploration de données,
        "strategic" pour une analyse stratégique.
    """
    q_lower = question.lower()

    sql_score = sum(1 for p in _SQL_PATTERNS if re.search(p, q_lower))
    strategic_score = sum(1 for p in _STRATEGIC_PATTERNS if re.search(p, q_lower))

    # En cas d'égalité, privilégier "strategic"
    intent: IntentType = "sql" if sql_score > strategic_score else "strategic"

    logger.info(
        "Intent '%s' (sql=%d, strategic=%d) — question: %.60s",
        intent, sql_score, strategic_score, question,
    )
    return intent
