"""
Détecteur de domaine métier — classifie un dataset en finance, marketing,
sales, support, logistics, HR ou product.

Stratégie en cascade :
    1. Scoring par mots-clés (déterministe, rapide, O(n))
    2. Si ambigu : tie-break par règles métier (présence de concepts forts
       comme invoice_id, ca_total, ...)
    3. Si toujours ambigu et LLM activé : fallback DeepSeek (1 appel)

Le détecteur retourne un DomainPrediction avec score de confiance et
explication, utilisable directement par l'orchestrateur de normalisation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from backend.normalization.profiler import (
    ColumnKind,
    DatasetProfile,
    DatasetProfiler,
)
from backend.normalization.schemas import BusinessDomain
from backend.normalization.synonyms import DOMAIN_KEYWORDS, _normalize_term

logger = logging.getLogger(__name__)


# ============================================================
# Résultat de la détection
# ============================================================


@dataclass
class DomainPrediction:
    """
    Prédiction du domaine métier d'un dataset.

    Attributes:
        domain:        Domaine retenu (BusinessDomain).
        confidence:    Score de confiance dans [0, 1].
        method:        Méthode utilisée pour la décision ("keywords",
                       "tie_break", "llm_fallback").
        scores_by_domain: Scores bruts par domaine (pour debug/explicabilité).
        explanation:   Texte explicatif (utilisé dans le rapport).
    """

    domain: BusinessDomain
    confidence: float
    method: str
    scores_by_domain: Dict[str, float] = field(default_factory=dict)
    explanation: str = ""

    def to_dict(self) -> Dict[str, object]:
        return {
            "domain": self.domain.value,
            "confidence": round(self.confidence, 4),
            "method": self.method,
            "scores_by_domain": {
                k: round(v, 4) for k, v in self.scores_by_domain.items()
            },
            "explanation": self.explanation,
        }


# ============================================================
# Détecteur principal
# ============================================================


class BusinessDomainDetector:
    """
    Détecte le domaine métier d'un dataset.

    Le détecteur n'utilise pas le LLM par défaut (économies d'API).
    Pour activer le fallback LLM, passer use_llm_fallback=True.

    Le scoring est pondéré pour favoriser les concepts forts :
        - Une colonne "invoice_id" pèse plus qu'une colonne "date"
          dans la décision "sales".
        - Des colonnes très typées (NUMERIC + nom métier) pèsent plus
          qu'une colonne TEXT générique.

    Attributes:
        min_confidence_threshold:  Si le meilleur score est sous ce seuil,
                                   l'intention "unknown" est retournée.
        margin_for_tie:            Si écart entre top-1 et top-2 < margin,
                                   le tie-break est déclenché.
        use_llm_fallback:          Active le fallback LLM si tie-break
                                   ne suffit pas.
    """

    # Mapping interne : nom de domaine (str) → BusinessDomain
    _DOMAIN_MAP: Dict[str, BusinessDomain] = {
        "finance":   BusinessDomain.FINANCE,
        "marketing": BusinessDomain.MARKETING,
        "sales":     BusinessDomain.SALES,
        "product":   BusinessDomain.PRODUCT,
        "regional":  BusinessDomain.REGIONAL,
        "support":   BusinessDomain.SUPPORT,
        "logistics": BusinessDomain.LOGISTICS,
        "hr":        BusinessDomain.HR,
    }

    # Concepts "forts" qui forcent un domaine s'ils sont présents.
    # Format : domaine → set de colonnes normalisées discriminantes.
    _STRONG_SIGNALS: Dict[str, frozenset] = {
        "sales": frozenset({
            "invoice_id", "facture_id", "sale_date", "revenue_tnd",
            "unit_price_tnd",
        }),
        "marketing": frozenset({
            "campaign_id", "conversion_rate", "ctr", "ad_spend", "clicks",
            "sales_channel",
        }),
        "regional": frozenset({
            "customer_region", "region", "gouvernorat", "wilaya",
        }),
        "product": frozenset({
            "category", "categorie", "quantite_vendue", "sku", "prix_moyen",
        }),
        "support": frozenset({
            "ticket_id", "satisfaction_score", "csat", "churn_risk",
        }),
        "logistics": frozenset({
            "shipment", "lead_time", "warehouse", "inventory",
        }),
        "hr": frozenset({
            "employee_id", "salary", "salaire", "headcount", "hire_date",
        }),
        "finance": frozenset({
            "indicateur", "valeur",  # format clé-valeur KPIs globaux
        }),
    }

    def __init__(
        self,
        min_confidence_threshold: float = 0.20,
        margin_for_tie: float = 0.10,
        use_llm_fallback: bool = False,
    ) -> None:
        self.min_confidence_threshold = min_confidence_threshold
        self.margin_for_tie = margin_for_tie
        self.use_llm_fallback = use_llm_fallback
        self._profiler = DatasetProfiler()

    # ----------------------------------------------------------
    # API publique
    # ----------------------------------------------------------

    def detect(
        self,
        df_or_profile,
    ) -> DomainPrediction:
        """
        Détecte le domaine métier d'un dataset.

        Args:
            df_or_profile: DataFrame Pandas brut ou DatasetProfile pré-calculé.
                            Profile pré-calculé recommandé pour éviter de
                            re-profiler le DataFrame.

        Returns:
            DomainPrediction avec domaine, confiance et explication.
        """
        # Accepter soit un DataFrame, soit un profil pré-calculé
        if isinstance(df_or_profile, DatasetProfile):
            profile = df_or_profile
        else:
            profile = self._profiler.profile(df_or_profile)

        # Phase 1 : scoring par mots-clés
        scores = self._score_by_keywords(profile)

        if not scores or max(scores.values()) == 0:
            logger.info("Aucun signal métier détecté — domaine UNKNOWN")
            return DomainPrediction(
                domain=BusinessDomain.UNKNOWN,
                confidence=0.0,
                method="keywords",
                scores_by_domain=scores,
                explanation="Aucun mot-clé métier identifié dans les colonnes.",
            )

        # Phase 2 : applique les signaux forts (boost)
        scores = self._apply_strong_signals(scores, profile)

        # Normalisation des scores en [0, 1]
        total = sum(scores.values())
        normalized = {k: v / total for k, v in scores.items()} if total > 0 else scores

        ranked = sorted(normalized.items(), key=lambda x: x[1], reverse=True)
        top_name, top_score = ranked[0]
        second_score = ranked[1][1] if len(ranked) > 1 else 0.0
        margin = top_score - second_score

        # Sous le seuil minimum → UNKNOWN
        if top_score < self.min_confidence_threshold:
            return DomainPrediction(
                domain=BusinessDomain.UNKNOWN,
                confidence=top_score,
                method="keywords",
                scores_by_domain=normalized,
                explanation=(
                    f"Score insuffisant ({top_score:.2f} < "
                    f"{self.min_confidence_threshold:.2f})."
                ),
            )

        # Ambiguïté : tie-break
        if margin < self.margin_for_tie:
            tie_result = self._break_tie(ranked, profile)
            if tie_result is not None:
                domain_str, confidence = tie_result
                return DomainPrediction(
                    domain=self._DOMAIN_MAP[domain_str],
                    confidence=confidence,
                    method="tie_break",
                    scores_by_domain=normalized,
                    explanation=(
                        f"Décision par règle métier (tie-break entre "
                        f"{ranked[0][0]} et {ranked[1][0]})."
                    ),
                )

            # Fallback LLM si activé
            if self.use_llm_fallback:
                llm_result = self._llm_fallback(profile, ranked[:3])
                if llm_result is not None:
                    return llm_result

        # Cas nominal : un domaine domine clairement
        return DomainPrediction(
            domain=self._DOMAIN_MAP[top_name],
            confidence=top_score,
            method="keywords",
            scores_by_domain=normalized,
            explanation=(
                f"Domaine '{top_name}' identifié par "
                f"{int(top_score * 100)}% de mots-clés correspondants."
            ),
        )

    # ----------------------------------------------------------
    # Scoring par mots-clés
    # ----------------------------------------------------------

    def _score_by_keywords(self, profile: DatasetProfile) -> Dict[str, float]:
        """
        Calcule le score de chaque domaine par recherche de mots-clés.

        Pondération :
            - colonne avec match exact         : +1.0
            - colonne avec match partiel        : +0.5
            - colonne typée NUMERIC + pertinente : +0.2 bonus
        """
        scores: Dict[str, float] = {domain: 0.0 for domain in DOMAIN_KEYWORDS}

        normalized_cols = [c.normalized_name for c in profile.columns]

        for domain, keywords in DOMAIN_KEYWORDS.items():
            for col_name in normalized_cols:
                if col_name in keywords:
                    scores[domain] += 1.0
                else:
                    # Match partiel (substring)
                    for kw in keywords:
                        if kw in col_name or col_name in kw:
                            scores[domain] += 0.5
                            break

        return scores

    def _apply_strong_signals(
        self,
        scores: Dict[str, float],
        profile: DatasetProfile,
    ) -> Dict[str, float]:
        """
        Boost le score d'un domaine si des colonnes "signal fort" sont présentes.

        Exemple : la présence de "invoice_id" booste fortement "sales".
        """
        normalized_cols = {c.normalized_name for c in profile.columns}

        for domain, signals in self._STRONG_SIGNALS.items():
            matches = signals & normalized_cols
            if matches:
                # Boost proportionnel au nombre de signaux matchés
                scores[domain] = scores.get(domain, 0.0) + 2.0 * len(matches)
                logger.debug(
                    "Signal fort pour domaine '%s' : %s",
                    domain, matches,
                )

        return scores

    # ----------------------------------------------------------
    # Tie-break par règles métier
    # ----------------------------------------------------------

    def _break_tie(
        self,
        ranked: List[Tuple[str, float]],
        profile: DatasetProfile,
    ) -> Optional[Tuple[str, float]]:
        """
        Résout une ambiguïté entre les 2 premiers domaines.

        Règles métier (ordonnées par priorité) :
            1. Format clé-valeur (2 colonnes "indicateur"/"valeur") → finance
            2. Présence d'invoice_id → sales (prioritaire sur product/regional)
            3. Plusieurs colonnes numériques agrégées sans dimension régionale
               → product/marketing/finance selon contexte
        """
        normalized_cols = {c.normalized_name for c in profile.columns}

        # Règle 1 : format clé-valeur strict
        if normalized_cols == {"indicateur", "valeur"}:
            return ("finance", 0.95)

        # Règle 2 : invoice_id présent → priorité absolue à sales
        if "invoice_id" in normalized_cols and "sales" in {r[0] for r in ranked[:2]}:
            return ("sales", 0.85)

        # Règle 3 : présence de region/gouvernorat
        if {"customer_region", "region", "gouvernorat"} & normalized_cols:
            if "regional" in {r[0] for r in ranked[:2]}:
                return ("regional", 0.80)

        # Règle 4 : catégorie produit + agrégats
        if "category" in normalized_cols or "categorie" in normalized_cols:
            if "product" in {r[0] for r in ranked[:2]}:
                return ("product", 0.80)

        # Pas de tie-break possible → laisser le top-1 gagner
        return (ranked[0][0], ranked[0][1])

    # ----------------------------------------------------------
    # Fallback LLM (optionnel)
    # ----------------------------------------------------------

    def _llm_fallback(
        self,
        profile: DatasetProfile,
        top_candidates: List[Tuple[str, float]],
    ) -> Optional[DomainPrediction]:
        """
        Appelle DeepSeek pour trancher entre les domaines candidats.

        Cette méthode n'est appelée que si :
            - use_llm_fallback=True à l'instanciation
            - le tie-break par règles n'a pas tranché

        L'appel est synchrone et limité à 200 tokens en sortie pour
        contrôler le coût.
        """
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.messages import SystemMessage, HumanMessage

            from backend.config import (
                AZURE_OPENAI_API_KEY,
                AZURE_OPENAI_ENDPOINT,
                AZURE_OPENAI_MODEL,
            )

            candidate_names = [c[0] for c in top_candidates]
            column_list = ", ".join(c.normalized_name for c in profile.columns)
            sample_data = self._format_sample_for_llm(profile)

            system_prompt = (
                "Tu es un expert en classification de datasets métier. "
                "Tu reçois la liste des colonnes d'un dataset et un échantillon "
                "de valeurs. Ton rôle est de choisir le domaine métier le plus "
                "probable parmi les candidats fournis.\n\n"
                "Réponds UNIQUEMENT par un mot parmi la liste fournie, "
                "sans explication, sans ponctuation."
            )

            user_prompt = (
                f"Colonnes : {column_list}\n\n"
                f"Échantillon :\n{sample_data}\n\n"
                f"Candidats possibles : {', '.join(candidate_names)}\n\n"
                f"Domaine choisi :"
            )

            llm = ChatOpenAI(
                base_url=AZURE_OPENAI_ENDPOINT,
                api_key=AZURE_OPENAI_API_KEY,
                model=AZURE_OPENAI_MODEL,
                temperature=0.0,
                max_tokens=20,
            )

            response = llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ])

            choice = response.content.strip().lower()

            # Validation : la réponse doit être dans les candidats
            if choice in candidate_names and choice in self._DOMAIN_MAP:
                return DomainPrediction(
                    domain=self._DOMAIN_MAP[choice],
                    confidence=0.70,
                    method="llm_fallback",
                    scores_by_domain={k: v for k, v in top_candidates},
                    explanation=f"LLM a tranché en faveur de '{choice}'.",
                )

            logger.warning("LLM a retourné une réponse invalide : %s", choice)
            return None

        except Exception as e:
            logger.warning("Échec du fallback LLM : %s", e)
            return None

    @staticmethod
    def _format_sample_for_llm(profile: DatasetProfile) -> str:
        """Formate l'échantillon des données pour le prompt LLM."""
        lines = []
        for col in profile.columns[:8]:  # max 8 colonnes pour limiter tokens
            sample_str = ", ".join(str(v) for v in col.sample_values[:3])
            lines.append(f"  {col.name} ({col.kind.value}) : {sample_str}")
        return "\n".join(lines)
