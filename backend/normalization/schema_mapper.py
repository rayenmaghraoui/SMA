"""
SchemaMapper — mapping intelligent colonnes uploadées → concepts canoniques.

Cœur du système de normalisation. Implémente une cascade à trois niveaux
pour chaque colonne du dataset uploadé :

    1. SYNONYME EXACT (déterministe, O(1))
       Lookup dans SYNONYM_INDEX. Score de confiance = 1.0.

    2. SIMILARITÉ SÉMANTIQUE (embeddings sentence-t5-base)
       Calcule la similarité cosinus entre le nom de la colonne et
       chaque libellé de concept canonique. Si la meilleure similarité
       dépasse semantic_threshold (par défaut 0.75), le mapping est
       retenu avec confidence = similarité.

    3. LLM FALLBACK (optionnel, désactivé par défaut)
       Si activé via use_llm_fallback=True, demande à DeepSeek de proposer
       un mapping pour les colonnes restantes. Confidence = 0.60.

Le mapping est validé par compatibilité de type : un concept numérique
ne peut être mappé sur une colonne textuelle, etc. Si l'incompatibilité
est détectée, le mapping est rejeté.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np

from backend.normalization.profiler import (
    ColumnKind,
    ColumnProfile,
    DatasetProfile,
)
from backend.normalization.schemas import (
    BusinessDomain,
    CanonicalConcept,
    InternalSchema,
    get_schema_for_domain,
    get_all_schemas,
    _CONCEPT_TO_LEGACY_COLUMN,
)
from backend.normalization.synonyms import (
    CONCEPT_SYNONYMS,
    find_concept_by_synonym,
    _normalize_term,
)

logger = logging.getLogger(__name__)

# Index inversé : nom canonique → concept (ex: "sale_date" → DATE)
# Permet de mapper directement les colonnes qui portent déjà le bon nom.
_LEGACY_NAME_TO_CONCEPT: Dict[str, CanonicalConcept] = {
    v: k for k, v in _CONCEPT_TO_LEGACY_COLUMN.items()
}


# ============================================================
# Compatibilité concept ↔ type de colonne
# ============================================================
#
# Définit les types ColumnKind acceptables pour chaque concept.
# Empêche les mappings absurdes (mapper "revenue" sur une colonne TEXT).


_CONCEPT_TYPE_COMPATIBILITY: Dict[CanonicalConcept, frozenset] = {

    # Identifiants : objet ou identifier (parfois numérique en stockage)
    CanonicalConcept.INVOICE_ID:    frozenset({ColumnKind.IDENTIFIER, ColumnKind.TEXT}),
    CanonicalConcept.CUSTOMER_ID:   frozenset({ColumnKind.IDENTIFIER, ColumnKind.TEXT}),
    CanonicalConcept.PRODUCT_ID:    frozenset({ColumnKind.IDENTIFIER, ColumnKind.TEXT}),
    CanonicalConcept.CAMPAIGN_ID:   frozenset({ColumnKind.IDENTIFIER, ColumnKind.TEXT}),
    CanonicalConcept.TICKET_ID:     frozenset({ColumnKind.IDENTIFIER, ColumnKind.TEXT}),

    # Tous les montants : NUMERIC strict
    CanonicalConcept.REVENUE:        frozenset({ColumnKind.NUMERIC}),
    CanonicalConcept.PROFIT:         frozenset({ColumnKind.NUMERIC}),
    CanonicalConcept.COST:           frozenset({ColumnKind.NUMERIC}),
    CanonicalConcept.UNIT_PRICE:     frozenset({ColumnKind.NUMERIC}),
    CanonicalConcept.AVG_PRICE:      frozenset({ColumnKind.NUMERIC}),
    CanonicalConcept.AVG_BASKET:     frozenset({ColumnKind.NUMERIC}),
    CanonicalConcept.PROFIT_MARGIN:  frozenset({ColumnKind.NUMERIC}),
    CanonicalConcept.GROWTH_RATE:    frozenset({ColumnKind.NUMERIC}),
    CanonicalConcept.BUDGET:         frozenset({ColumnKind.NUMERIC}),
    CanonicalConcept.CONVERSION_RATE: frozenset({ColumnKind.NUMERIC}),

    # Volumes : NUMERIC
    CanonicalConcept.QUANTITY:        frozenset({ColumnKind.NUMERIC}),
    CanonicalConcept.TOTAL_QUANTITY:  frozenset({ColumnKind.NUMERIC}),
    CanonicalConcept.NB_TRANSACTIONS: frozenset({ColumnKind.NUMERIC}),
    CanonicalConcept.NB_CUSTOMERS:    frozenset({ColumnKind.NUMERIC}),
    CanonicalConcept.CLICKS:          frozenset({ColumnKind.NUMERIC}),
    CanonicalConcept.CONVERSIONS:     frozenset({ColumnKind.NUMERIC}),

    # Indicateur/valeur (format clé-valeur) : nom = TEXT/CAT, valeur = NUMERIC
    CanonicalConcept.INDICATOR_NAME:  frozenset({ColumnKind.CATEGORICAL, ColumnKind.TEXT, ColumnKind.IDENTIFIER}),
    CanonicalConcept.INDICATOR_VALUE: frozenset({ColumnKind.NUMERIC}),

    # Dimensions : CATEGORICAL / TEXT
    CanonicalConcept.PRODUCT_NAME:   frozenset({ColumnKind.TEXT, ColumnKind.CATEGORICAL, ColumnKind.IDENTIFIER}),
    CanonicalConcept.CATEGORY:       frozenset({ColumnKind.CATEGORICAL, ColumnKind.TEXT}),
    CanonicalConcept.REGION:         frozenset({ColumnKind.CATEGORICAL, ColumnKind.TEXT}),
    CanonicalConcept.SALES_CHANNEL:  frozenset({ColumnKind.CATEGORICAL, ColumnKind.TEXT}),
    CanonicalConcept.PAYMENT_METHOD: frozenset({ColumnKind.CATEGORICAL, ColumnKind.TEXT}),
    CanonicalConcept.ISSUE_TYPE:     frozenset({ColumnKind.CATEGORICAL, ColumnKind.TEXT}),
    CanonicalConcept.CHURN_RISK:     frozenset({ColumnKind.CATEGORICAL, ColumnKind.TEXT}),

    # Temps
    CanonicalConcept.DATE:           frozenset({ColumnKind.DATE, ColumnKind.TEXT}),

    # Satisfaction : numérique ou catégorielle (1-5, "high", ...)
    CanonicalConcept.SATISFACTION_SCORE: frozenset({ColumnKind.NUMERIC, ColumnKind.CATEGORICAL}),
    CanonicalConcept.RESOLUTION_HOURS:   frozenset({ColumnKind.NUMERIC}),
}


def _is_compatible(concept: CanonicalConcept, column_kind: ColumnKind) -> bool:
    """Vérifie qu'un concept peut être mappé sur une colonne d'un type donné."""
    allowed = _CONCEPT_TYPE_COMPATIBILITY.get(concept)
    if allowed is None:
        return True  # concept sans contrainte de type
    return column_kind in allowed


# ============================================================
# Résultat d'un mapping individuel
# ============================================================


@dataclass
class ColumnMapping:
    """
    Mapping d'une colonne uploadée vers un concept canonique.

    Attributes:
        source_column:    Nom original de la colonne dans le dataset.
        target_concept:   Concept canonique cible (ou None si non mappé).
        confidence:       Score de confiance dans [0, 1].
        method:           "synonym" | "semantic" | "llm" | "unmapped".
        reason:           Texte explicatif (utilisé dans le rapport).
        rejected_reason:  Si le mapping a été rejeté (incompatibilité type),
                          raison du rejet.
    """

    source_column: str
    target_concept: Optional[CanonicalConcept]
    confidence: float
    method: str
    reason: str = ""
    rejected_reason: Optional[str] = None

    @property
    def is_mapped(self) -> bool:
        return self.target_concept is not None

    def to_dict(self) -> Dict[str, object]:
        return {
            "source_column": self.source_column,
            "target_concept": (
                self.target_concept.value if self.target_concept else None
            ),
            "confidence": round(self.confidence, 4),
            "method": self.method,
            "reason": self.reason,
            "rejected_reason": self.rejected_reason,
        }


# ============================================================
# Mapper principal
# ============================================================


class SchemaMapper:
    """
    Mappe les colonnes d'un dataset vers les concepts canoniques.

    Workflow standard :
        mapper = SchemaMapper()
        mappings = mapper.map_columns(profile)

    Pour cibler un schéma spécifique (et n'extraire que les concepts pertinents) :
        mappings = mapper.map_columns(profile, target_schema=KPIS_SCHEMA)

    Attributes:
        semantic_threshold:  Seuil de similarité pour validation sémantique.
        use_llm_fallback:    Active le LLM pour les colonnes non mappées.
        use_semantic:        Active la similarité sémantique (peut être
                             désactivé pour tests rapides sans embeddings).
    """

    def __init__(
        self,
        semantic_threshold: float = 0.75,
        use_llm_fallback: bool = False,
        use_semantic: bool = True,
    ) -> None:
        self.semantic_threshold = semantic_threshold
        self.use_llm_fallback = use_llm_fallback
        self.use_semantic = use_semantic

        # Embeddings et cache des libellés de concepts (calculé à la demande)
        self._embeddings = None
        self._concept_embeddings: Optional[Dict[CanonicalConcept, np.ndarray]] = None
        self._concept_labels: Optional[Dict[CanonicalConcept, str]] = None

    # ----------------------------------------------------------
    # API publique
    # ----------------------------------------------------------

    def map_columns(
        self,
        profile: DatasetProfile,
        target_schema: Optional[InternalSchema] = None,
        target_domain: Optional[BusinessDomain] = None,
    ) -> List[ColumnMapping]:
        """
        Mappe toutes les colonnes d'un dataset vers les concepts canoniques.

        Args:
            profile:        Profil du dataset.
            target_schema:  Schéma cible — restreint les concepts candidats
                            (gain de précision si fourni).
            target_domain:  Alternative au schéma : domaine cible.

        Returns:
            Liste de ColumnMapping (un par colonne uploadée).
        """
        logger.info(
            "Mapping de %d colonnes (target_schema=%s, target_domain=%s)",
            profile.n_columns,
            target_schema.name if target_schema else None,
            target_domain.value if target_domain else None,
        )

        # Détermine l'univers de concepts candidats
        candidate_concepts = self._get_candidate_concepts(
            target_schema, target_domain
        )

        mappings: List[ColumnMapping] = []
        used_concepts: set = set()

        for column in profile.columns:
            mapping = self._map_single_column(
                column,
                candidate_concepts=candidate_concepts,
                excluded_concepts=used_concepts,
            )
            mappings.append(mapping)

            if mapping.is_mapped and mapping.target_concept is not None:
                used_concepts.add(mapping.target_concept)

        # LLM fallback : tenter de mapper les colonnes restantes
        if self.use_llm_fallback:
            self._llm_fallback_unmapped(profile, mappings, candidate_concepts)

        self._log_summary(mappings)
        return mappings

    # ----------------------------------------------------------
    # Univers de concepts candidats
    # ----------------------------------------------------------

    @staticmethod
    def _get_candidate_concepts(
        target_schema: Optional[InternalSchema],
        target_domain: Optional[BusinessDomain],
    ) -> Optional[frozenset]:
        """
        Calcule l'ensemble des concepts éligibles pour le mapping.

        Si ni schéma ni domaine n'est fourni, retourne None (= tous les
        concepts sont éligibles).
        """
        if target_schema is not None:
            return target_schema.all_concepts

        if target_domain is not None:
            schemas = get_schema_for_domain(target_domain)
            if schemas:
                concepts: set = set()
                for s in schemas:
                    concepts |= s.all_concepts
                return frozenset(concepts)

        return None

    # ----------------------------------------------------------
    # Mapping d'une colonne individuelle
    # ----------------------------------------------------------

    def _map_single_column(
        self,
        column: ColumnProfile,
        candidate_concepts: Optional[frozenset],
        excluded_concepts: set,
    ) -> ColumnMapping:
        """
        Applique la cascade synonyme → sémantique → unmapped pour une colonne.

        excluded_concepts : concepts déjà attribués à une autre colonne (un
        concept ne peut être mappé qu'une seule fois par dataset, sauf pour
        les indicateurs/valeurs qui ont chacun leur colonne distincte).
        """
        # --- Niveau 0 : correspondance nom canonique direct -------------
        # Si la colonne porte EXACTEMENT le nom attendu par les analyzers
        # (ex: "sale_date", "revenue_tnd"), on la mappe directement.
        # On vérifie seulement que le concept n'est pas déjà utilisé et
        # qu'il est dans le périmètre du schéma — on ignore la compatibilité
        # de type car le nom est une preuve suffisante d'intention.
        legacy_concept = _LEGACY_NAME_TO_CONCEPT.get(column.name)
        if legacy_concept is not None:
            already_used = legacy_concept in excluded_concepts
            out_of_scope = (
                candidate_concepts is not None
                and legacy_concept not in candidate_concepts
            )
            if not already_used and not out_of_scope:
                return ColumnMapping(
                    source_column=column.name,
                    target_concept=legacy_concept,
                    confidence=1.0,
                    method="synonym",
                    reason=(
                        f"'{column.name}' est le nom canonique exact "
                        f"de '{legacy_concept.value}'."
                    ),
                )

        # --- Niveau 1 : synonyme exact ----------------------------------
        synonym_concept = find_concept_by_synonym(column.name)

        if synonym_concept is not None:
            if self._is_acceptable(
                synonym_concept, column, candidate_concepts, excluded_concepts
            ):
                return ColumnMapping(
                    source_column=column.name,
                    target_concept=synonym_concept,
                    confidence=1.0,
                    method="synonym",
                    reason=(
                        f"'{column.name}' correspond exactement au synonyme "
                        f"de '{synonym_concept.value}'."
                    ),
                )

            # Incompatibilité de type (rare) → continuer en sémantique
            logger.debug(
                "Synonyme exact rejeté pour '%s' → '%s' (type incompatible)",
                column.name, synonym_concept.value,
            )

        # --- Niveau 2 : similarité sémantique ---------------------------
        if self.use_semantic:
            semantic_mapping = self._map_by_semantic_similarity(
                column, candidate_concepts, excluded_concepts
            )
            if semantic_mapping is not None:
                return semantic_mapping

        # --- Aucun mapping trouvé ---------------------------------------
        return ColumnMapping(
            source_column=column.name,
            target_concept=None,
            confidence=0.0,
            method="unmapped",
            reason="Aucun synonyme exact ni similarité suffisante trouvée.",
        )

    def _is_acceptable(
        self,
        concept: CanonicalConcept,
        column: ColumnProfile,
        candidate_concepts: Optional[frozenset],
        excluded_concepts: set,
    ) -> bool:
        """Vérifie qu'un concept candidat est utilisable pour la colonne."""
        # Exclu (déjà mappé)
        if concept in excluded_concepts:
            return False

        # Hors périmètre du schéma cible
        if candidate_concepts is not None and concept not in candidate_concepts:
            return False

        # Incompatibilité de type
        if not _is_compatible(concept, column.kind):
            return False

        return True

    # ----------------------------------------------------------
    # Similarité sémantique (sentence-t5-base)
    # ----------------------------------------------------------

    def _map_by_semantic_similarity(
        self,
        column: ColumnProfile,
        candidate_concepts: Optional[frozenset],
        excluded_concepts: set,
    ) -> Optional[ColumnMapping]:
        """Mappe une colonne via similarité cosinus avec les libellés de concepts."""
        try:
            self._ensure_embeddings_loaded()
        except Exception as e:
            logger.warning("Embeddings indisponibles, sémantique désactivée : %s", e)
            return None

        # Embedding de la colonne (à partir du nom + échantillon)
        query_text = self._build_query_text(column)
        query_embedding = self._embed(query_text)

        # Score chaque concept candidat
        best_concept: Optional[CanonicalConcept] = None
        best_score = 0.0

        assert self._concept_embeddings is not None  # garanti par _ensure_embeddings_loaded
        for concept, embedding in self._concept_embeddings.items():
            if not self._is_acceptable(concept, column, candidate_concepts, excluded_concepts):
                continue

            score = float(np.dot(query_embedding, embedding))
            if score > best_score:
                best_score = score
                best_concept = concept

        if best_concept is None or best_score < self.semantic_threshold:
            return None

        return ColumnMapping(
            source_column=column.name,
            target_concept=best_concept,
            confidence=best_score,
            method="semantic",
            reason=(
                f"Similarité sémantique avec '{best_concept.value}' = "
                f"{best_score:.2f} (≥ {self.semantic_threshold:.2f})."
            ),
        )

    def _ensure_embeddings_loaded(self) -> None:
        """Charge le modèle d'embeddings et précalcule les embeddings concepts."""
        if self._concept_embeddings is not None:
            return

        # Réutilise le singleton sentence-t5-base déjà utilisé par le RAG
        from backend.rag.embeddings import get_embedding_model

        self._embeddings = get_embedding_model()

        # Pour chaque concept, on construit un libellé descriptif riche
        # qui combine la valeur enum et un échantillon de synonymes.
        self._concept_labels = {
            concept: self._build_concept_label(concept)
            for concept in CanonicalConcept
        }

        labels_list = list(self._concept_labels.values())
        concepts_list = list(self._concept_labels.keys())

        # Embedding batch
        vectors = self._embeddings.embed_documents(labels_list)
        vectors_np = [np.array(v, dtype=np.float32) for v in vectors]

        # Normalisation L2 (déjà fait par sentence-t5-base mais sécurise)
        vectors_np = [v / (np.linalg.norm(v) + 1e-12) for v in vectors_np]

        self._concept_embeddings = {
            concept: vec for concept, vec in zip(concepts_list, vectors_np)
        }
        logger.info(
            "Embeddings concepts précalculés : %d concepts",
            len(self._concept_embeddings),
        )

    @staticmethod
    def _build_concept_label(concept: CanonicalConcept) -> str:
        """
        Construit un libellé descriptif pour un concept (pour embedding).

        Combine le nom canonique et 3 synonymes représentatifs.
        """
        synonyms = CONCEPT_SYNONYMS.get(concept, frozenset())
        sample_syns = list(synonyms)[:3]
        return " ".join([concept.value.replace("_", " ")] + sample_syns)

    def _build_query_text(self, column: ColumnProfile) -> str:
        """Construit le texte à embedder pour une colonne uploadée."""
        # Nom + (optionnel) échantillon de valeurs catégorielles
        parts = [column.normalized_name.replace("_", " ")]

        if column.kind == ColumnKind.CATEGORICAL and column.sample_values:
            sample_str = " ".join(str(v) for v in column.sample_values[:3])
            parts.append(sample_str)

        return " ".join(parts)

    def _embed(self, text: str) -> np.ndarray:
        """Calcule un embedding normalisé d'un texte."""
        assert self._embeddings is not None  # garanti par _ensure_embeddings_loaded
        vector = np.array(self._embeddings.embed_query(text), dtype=np.float32)
        return vector / (np.linalg.norm(vector) + 1e-12)

    # ----------------------------------------------------------
    # Fallback LLM (optionnel)
    # ----------------------------------------------------------

    def _llm_fallback_unmapped(
        self,
        profile: DatasetProfile,
        mappings: List[ColumnMapping],
        candidate_concepts: Optional[frozenset],
    ) -> None:
        """
        Tente de mapper les colonnes restantes via DeepSeek (1 seul appel batch).

        Modifie la liste mappings en place.
        """
        unmapped_indices = [i for i, m in enumerate(mappings) if not m.is_mapped]
        if not unmapped_indices:
            return

        unmapped_columns = [profile.columns[i] for i in unmapped_indices]
        logger.info(
            "Fallback LLM pour %d colonnes non mappées",
            len(unmapped_columns),
        )

        try:
            llm_mappings = self._call_llm_for_mapping(
                unmapped_columns, candidate_concepts
            )
        except Exception as e:
            logger.warning("Échec du fallback LLM : %s", e)
            return

        # Met à jour les mappings non résolus
        used = {m.target_concept for m in mappings if m.is_mapped}
        for idx, col in zip(unmapped_indices, unmapped_columns):
            proposed = llm_mappings.get(col.name)
            if proposed is None:
                continue
            if proposed in used:
                continue
            if not _is_compatible(proposed, col.kind):
                continue
            mappings[idx] = ColumnMapping(
                source_column=col.name,
                target_concept=proposed,
                confidence=0.60,
                method="llm",
                reason=f"Proposé par LLM (fallback).",
            )
            used.add(proposed)

    def _call_llm_for_mapping(
        self,
        columns: List[ColumnProfile],
        candidate_concepts: Optional[frozenset],
    ) -> Dict[str, CanonicalConcept]:
        """Appelle DeepSeek pour proposer des mappings."""
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage
        import json

        from backend.config import (
            AZURE_OPENAI_API_KEY,
            AZURE_OPENAI_ENDPOINT,
            AZURE_OPENAI_MODEL,
        )

        # Concepts disponibles (avec leurs valeurs enum)
        available = candidate_concepts or set(CanonicalConcept)
        concept_list = [c.value for c in available]

        # Description des colonnes à mapper
        col_lines = []
        for c in columns:
            sample = ", ".join(str(v) for v in c.sample_values[:3])
            col_lines.append(
                f"- {c.name} (type={c.kind.value}, exemples: {sample})"
            )
        cols_desc = "\n".join(col_lines)

        system_prompt = (
            "Tu es un expert en analyse de données business. "
            "On te donne des colonnes d'un dataset et une liste de concepts "
            "canoniques. Tu dois proposer pour chaque colonne le concept "
            "le plus approprié, ou null si aucun ne convient.\n\n"
            "Réponds UNIQUEMENT par un JSON valide sur une seule ligne, "
            "sans markdown, format :\n"
            '{"nom_colonne": "concept_canonique_ou_null", ...}'
        )

        user_prompt = (
            f"Colonnes à mapper :\n{cols_desc}\n\n"
            f"Concepts disponibles : {', '.join(concept_list)}\n\n"
            "Mapping :"
        )

        llm = ChatOpenAI(
            base_url=AZURE_OPENAI_ENDPOINT,
            api_key=AZURE_OPENAI_API_KEY,
            model=AZURE_OPENAI_MODEL,
            temperature=0.0,
            max_tokens=512,
        )

        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ])

        # Parse JSON robuste
        raw = response.content.strip()
        if raw.startswith("```"):
            raw = raw.strip("`")
            if raw.lower().startswith("json"):
                raw = raw[4:].strip()

        try:
            mapping_dict = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("LLM a retourné un JSON invalide : %s", raw[:200])
            return {}

        # Convertit en enums
        result: Dict[str, CanonicalConcept] = {}
        valid_values = {c.value for c in available}
        for col_name, concept_value in mapping_dict.items():
            if concept_value and concept_value in valid_values:
                result[col_name] = CanonicalConcept(concept_value)
        return result

    # ----------------------------------------------------------
    # Logging
    # ----------------------------------------------------------

    @staticmethod
    def _log_summary(mappings: List[ColumnMapping]) -> None:
        """Log un résumé du mapping pour debug."""
        mapped = sum(1 for m in mappings if m.is_mapped)
        by_method: Dict[str, int] = {}
        for m in mappings:
            by_method[m.method] = by_method.get(m.method, 0) + 1
        logger.info(
            "Mapping terminé : %d/%d colonnes mappées — détail : %s",
            mapped, len(mappings), by_method,
        )
