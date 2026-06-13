"""
Routeur d'intention — classifie une question comme "sql" ou "strategic".

Logique :
    - Score basé sur des patterns regex pondérés pour chaque intention.
    - L'intention avec le score le plus élevé gagne.
    - En cas d'égalité, l'intention "strategic" est privilégiée
      (comportement plus sûr : le pipeline LangGraph est plus complet).

Intentions :
    "sql"       → exploration de données, requêtes, agrégations, filtres
    "strategic" → recommandations, stratégie, interprétation, analyse globale
"""

import logging
import re
from typing import Literal, List, Tuple

logger = logging.getLogger(__name__)

IntentType = Literal["sql", "strategic"]

# ── Opérations destructives ou de modification — toujours refusées ──────────
# Détectées AVANT le routage pour retourner un message de refus immédiat.
_DESTRUCTIVE_PATTERNS: List[str] = [
    # DDL (structure)
    r"\b(drop|alter|truncate)\b",
    r"\bsupprimer?\s+(la\s+)?(colonne|table|base|champ|index)\b",
    r"\bsupprime[z\s]\s+(la\s+)?(colonne|table|base|champ)\b",
    r"\befface[z\s]?\s+(la\s+)?(colonne|table|base)\b",
    r"\bmodifi[eé][z\s]?\s+(la\s+)?(colonne|table|structure)\b",
    r"\brenomnr?e[z\s]?\s+(la\s+)?(colonne|table)\b",
    r"\bajoute[z\s]?\s+une?\s+(colonne|champ)\b",
    r"\bcr[eé][eé][z\s]?\s+(une?\s+)?(table|base|index)\b",
    # DML (données)
    r"\b(delete|update|insert)\b",
    r"\bsupprimer?\s+(les?\s+)?(lignes?|enregistrements?|donn[eé]es?)\b",
    r"\beffac[eé]?\s+(les?\s+)?(lignes?|enregistrements?|donn[eé]es?)\b",
    r"\bmodifi[eé][z\s]?\s+(les?\s+)?(lignes?|valeurs?|donn[eé]es?)\b",
    r"\bmettre?\s+[aà]\s+jour\b",
    r"\binsérer?\b",
    r"\bvider?\s+(la\s+)?(table|base)\b",
]


def is_destructive_operation(question: str) -> bool:
    """
    Détecte si la question demande une opération destructive ou de modification.

    Returns:
        True si l'opération doit être refusée (non-SELECT).
    """
    q_lower = question.lower()
    return any(re.search(p, q_lower) for p in _DESTRUCTIVE_PATTERNS)


# ── Patterns SQL pondérés : (regex, poids) ───────────────────────────────────
# Poids 2 = signal fort et non ambigu → exploration de données directe
# Poids 1 = signal faible ou partageable avec d'autres intentions
_SQL_WEIGHTED: List[Tuple[str, int]] = [

    # ── Verbes d'affichage (avec ou sans -z) ─────────────────────────────────
    (r"\bmontre[z\s-]", 2),
    (r"\bmontre\s+moi\b", 2),
    (r"\baffiche[z\s-]", 2),
    (r"\baffiche\s+moi\b", 2),
    (r"\bliste[z\s-]", 2),
    (r"\bdonne[z\s-]\s*moi\b", 2),
    (r"\bdonne[z\s-].{0,30}\bdonn[eé]es?\b", 2),
    (r"\bexporte[z\s-]", 2),
    (r"\bt[eé]l[eé]charge[z\s-]", 2),
    (r"\bidentifi[ez\s-]", 1),
    (r"\btrouve[z\s-]", 1),

    # ── Requêtes SQL explicites ───────────────────────────────────────────────
    (r"\bselect\b", 2),
    (r"\bsql\b", 2),

    # ── Agrégations et calculs ────────────────────────────────────────────────
    (r"\btop\s+\d+", 2),
    (r"\bcombien\b", 2),
    (r"\bnombre\s+de\b", 2),
    (r"\bmax(imum)?\b", 2),
    (r"\bmin(imum)?\b", 2),
    (r"\bmoyenne\b", 2),
    (r"\bsomme?\b", 1),
    (r"\btotal\b.{0,20}\bpar\b", 2),
    (r"\bcompte[z\s-]", 2),
    (r"\bcompter\b", 2),
    (r"\bcalcule[z\s-]", 1),

    # ── Tri et classement ─────────────────────────────────────────────────────
    (r"\btrie[z\s-]", 2),
    (r"\bclasse[z\s-]", 2),
    (r"\brang(s|er)?\b", 1),
    (r"\bclassement\b", 2),
    (r"\bpalmar[eè]s\b", 2),

    # ── Filtres et comparaisons ───────────────────────────────────────────────
    (r"\bfiltre[z\s-]", 2),
    (r"\bsup[eé]rieur(e?\s+[aà])\b", 2),
    (r"\binf[eé]rieur(e?\s+[aà])\b", 2),
    (r"\bcompar(e[z\s]|aison|er)\b", 1),
    (r"\bentre\s+\d", 2),
    (r"\btoutes?\s+les?\s+(lignes?|entr[eé]es?|tickets?|factures?|transactions?)\b", 2),
    (r"\bquel(le)?s?\s+sont\s+les?\s+\d+", 2),

    # ── Questions superlatives "quel est le X le plus Y" ─────────────────────
    (r"\bquel(le)?s?\s+sont\s+les?\b", 1),
    (r"\bplus\s+(vendu[e]?s?|achet[eé][e]?s?|demand[eé][e]?s?|rentable[s]?|performant[e]?s?|populaire[s]?|[eé]lev[eé][e]?s?|faible[s]?|bas|basse[s]?)\b", 2),
    (r"\bmeilleur(e)?s?\b", 1),
    (r"\bpire[s]?\b", 1),
    (r"\bquel(le)?[s]?\b.{0,15}\b(produit|client|r[eé]gion|canal|cat[eé]gorie)\b", 1),

    # ── Données par dimension (grouping) ─────────────────────────────────────
    (r"\bpar\s+(mois|canal|type|semaine|jour|ann[eé]e|r[eé]gion|cat[eé]gorie|produit|client|mode\s+de\s+paiement)\b", 2),
    (r"\bpar\s+(campagne|churn|ticket)\b", 2),
    (r"\bventil[eé]\s+par\b", 2),
    (r"\br[eé]parti(tion|r)\b.{0,20}\bpar\b", 2),

    # ── Périodes et dates ─────────────────────────────────────────────────────
    (r"\ben\s+(janvier|f[eé]vrier|mars|avril|mai|juin|juillet|ao[uû]t|septembre|octobre|novembre|d[eé]cembre)\b", 2),
    (r"\ben\s+\d{4}\b", 2),
    (r"\bce\s+(mois|trimestre|semestre|an)\b", 2),
    (r"\ble\s+mois\s+(dernier|pr[eé]c[eé]dent|pass[eé])\b", 2),
    (r"\bcette\s+(semaine|ann[eé]e)\b", 2),
    (r"\bentre\s+le\b", 2),
    (r"\bdepuis\s+(le|janvier|f[eé]vrier|\d)", 2),
    (r"\bavant\s+le\b", 2),
    (r"\bapr[eè]s\s+le\b", 2),
    (r"\bq[1-4]\b", 2),
    (r"\btrimestre\b", 1),

    # ── Entités métier spécifiques (colonnes / domaine tunisien) ─────────────
    (r"\b(invoice_id|product_name|unit_price|revenue_tnd|customer_id|sale_date|estimated_profit)\b", 2),
    (r"\b(ca_total|profit_total|nb_transactions|panier_moyen|quantite_vendue|prix_moyen)\b", 2),
    (r"\b(mobilier|[eé]lectronique|fournitures|divers)\b", 1),
    (r"\b(site\s+web|magasin\s+physique|t[eé]l[eé]phone)\b", 1),
    (r"\b(carte\s+bancaire|esp[eè]ces?|virement)\b", 1),
    (r"\b(tunis|ariana|sfax|sousse|monastir|gab[eè]s|biz(erte|erta)|nabeul)\b", 1),
    (r"\btransactions?\b", 1),
    (r"\bfactures?\b", 1),
    (r"\bcommandes?\b", 1),
    (r"\bventes?\b.{0,15}\b(par|de|en|du)\b", 1),
    (r"\bchiffre\s+d['']affaires?\b", 1),
    (r"\b\bca\b.{0,10}\b(par|de|en|du|total)\b", 1),

    # ── Produits / clients spécifiques ───────────────────────────────────────
    (r"\bproduit[s]?\b.{0,30}\b(vendu[e]?|achet[eé]|populaire|rentable)\b", 2),
    (r"\b(vendu[e]?|achet[eé]).{0,30}\bproduit[s]?\b", 2),
    (r"\bclient[s]?\b.{0,20}\b(plus|meilleur|top|fid[eè]le|actif)\b", 2),
    (r"\br[eé]gion[s]?\b.{0,20}\b(plus|meilleur|top|performant)\b", 2),
]

# ── Patterns stratégiques pondérés : (regex, poids) ──────────────────────────
# Poids 2 = signal fort et non ambigu → analyse qualitative / conseil
# Poids 1 = signal modéré, peut chevaucher avec SQL
_STRATEGIC_WEIGHTED: List[Tuple[str, int]] = [

    # ── Recommandations et conseils ───────────────────────────────────────────
    (r"\brecommand", 2),
    (r"\bconseille[z\s-]", 2),
    (r"\bque\s+(faire|proposez|conseillez|recommandez)\b", 2),
    (r"\bvotre\s+avis\b", 2),
    (r"\bqu['']est[- ]ce\s+que\s+vous\b", 2),
    (r"\bque\s+pensez[- ]vous\b", 2),
    (r"\bqu['']est[- ]ce\s+qu['']on\s+devrait\b", 2),

    # ── Stratégie et plan d'action ────────────────────────────────────────────
    (r"\bstrat[eé]gie\b", 2),
    (r"\bplan\s+d['']action\b", 2),
    (r"\baction[s]?\s+(prioritaire|concr[eè]te)\b", 2),
    (r"\bfeuille\s+de\s+route\b", 2),
    (r"\bpriorit[eé][s]?\b", 1),
    (r"\binvestir\b", 1),
    (r"\bfocaliser\b", 1),
    (r"\bprioriser\b", 2),

    # ── Problèmes et solutions ────────────────────────────────────────────────
    (r"\bprobl[eè]me[s]?\b", 2),
    (r"\bsolution[s]?\b", 2),
    (r"\bcause[s]?\b", 1),
    (r"\bpourquoi\b", 2),
    (r"\bqu['']est[- ]ce\s+qui\s+(explique|cause|provoque)\b", 2),

    # ── Interprétation et analyse qualitative ─────────────────────────────────
    (r"\banalyse[z\s-]", 2),
    (r"\binterpr[eè]te[z\s-]", 2),
    (r"\bexplique[z\s-]", 2),
    (r"\bsignifie\b", 2),
    (r"\bque\s+veut\s+dire\b", 2),
    (r"\bcomment\s+interpr[eé]ter\b", 2),

    # ── Amélioration et optimisation ─────────────────────────────────────────
    (r"\bam[eé]liore[z\s-]", 2),
    (r"\boptimise[z\s-]", 2),
    (r"\baugmenter\b", 1),
    (r"\br[eé]duire\b", 1),
    (r"\bcomment\s+(am[eé]liorer|augmenter|r[eé]duire|optimiser|booster)\b", 2),

    # ── Synthèse et rapport global ────────────────────────────────────────────
    (r"\bbilan\b", 2),
    (r"\bsynth[eè]se\b", 2),
    (r"\br[eé]sum[eé]\b", 2),
    (r"\bvue\s+d['']ensemble\b", 2),
    (r"\brapport\s+(global|complet|final|g[eé]n[eé]ral)\b", 2),
    (r"\b[eé]tat\s+des?\s+lieux\b", 2),
    (r"\bperformance[s]?\b.{0,20}\bglobal", 2),

    # ── Tendances et prévisions ───────────────────────────────────────────────
    (r"\btendance[s]?\b", 2),
    (r"\b[eé]volution\b.{0,20}\b(global|g[eé]n[eé]ral|ensemble)\b", 1),
    (r"\bpr[eé]vision[s]?\b", 2),
    (r"\bprojection[s]?\b", 2),
    (r"\bpr[eé]voir\b", 2),
    (r"\banticiper\b", 2),
    (r"\bforecast\b", 2),

    # ── Diagnostic et audit ───────────────────────────────────────────────────
    (r"\bdiagnostic\b", 2),
    (r"\bauditer?\b", 2),
    (r"\b[eé]valuer?\b", 1),
    (r"\bforces?\b.{0,20}\bfaiblesses?\b", 2),
    (r"\bswot\b", 2),
    (r"\bavantage[s]?\s+concurrentiel[s]?\b", 2),

    # ── Contexte business / marché ────────────────────────────────────────────
    (r"\bopportunit[eé][s]?\b", 2),
    (r"\brisque[s]?\b", 2),
    (r"\bperspective[s]?\b", 2),
    (r"\bstagnation\b", 2),
    (r"\bchute\b.{0,20}\b(ventes?|ca|profit)\b", 1),
    (r"\bcroissance\b.{0,20}\b(global|lente|rapide|faible)\b", 1),
]

def classify_intent(question: str) -> IntentType:
    """
    Classifie l'intention d'une question en langage naturel.

    Utilise un scoring pondéré : chaque pattern SQL ou stratégique
    contribue à un score selon son poids (1 ou 2).
    En cas d'égalité, "strategic" est retenu (réponse plus complète).

    Args:
        question: Question de l'utilisateur.

    Returns:
        "sql" pour une exploration de données,
        "strategic" pour une analyse stratégique.
    """
    q_lower = question.lower()

    sql_score = sum(w for p, w in _SQL_WEIGHTED if re.search(p, q_lower))
    strategic_score = sum(w for p, w in _STRATEGIC_WEIGHTED if re.search(p, q_lower))

    # En cas d'égalité (dont 0/0), privilégier "strategic"
    intent: IntentType = "sql" if sql_score > strategic_score else "strategic"

    if logger.isEnabledFor(logging.DEBUG):
        matched_sql = [p for p, _ in _SQL_WEIGHTED if re.search(p, q_lower)]
        matched_str = [p for p, _ in _STRATEGIC_WEIGHTED if re.search(p, q_lower)]
        logger.debug("SQL patterns matchés : %s", matched_sql)
        logger.debug("Strategic patterns matchés : %s", matched_str)

    logger.info(
        "Intent '%s' (sql=%d, strategic=%d) — question: %.80s",
        intent, sql_score, strategic_score, question,
    )
    return intent
