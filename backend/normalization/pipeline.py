"""
NormalizationPipeline — orchestrateur de la couche de normalisation.

Pipeline complet :
    1. DatasetProfiler        → profil structurel du DataFrame
    2. BusinessDomainDetector → domaine métier détecté
    3. SchemaMapper           → mappings colonnes → concepts canoniques
    4. SafeDataTransformer    → DataFrame normalisé + rapport

Sortie : NormalizationResult contenant le DataFrame normalisé, le rapport
de transformation, et toutes les métadonnées d'explicabilité.

Usage typique :
    pipeline = NormalizationPipeline()
    result = pipeline.normalize(df_uploaded)

    if result.success:
        # result.normalized_df peut être passé à l'analyzer correspondant
        # à result.schema.name
        analyzer.analyze(result.normalized_df)
    else:
        # result.report.errors décrit pourquoi la normalisation a échoué
        log.error(result.report.errors)

Pour un mode "best-effort multi-schémas" :
    results = pipeline.normalize_all_schemas(df_uploaded)
    # results : Dict[schema_name, NormalizationResult]
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import pandas as pd

from backend.normalization.domain_detector import (
    BusinessDomainDetector,
    DomainPrediction,
)
from backend.normalization.profiler import DatasetProfile, DatasetProfiler
from backend.normalization.schema_mapper import (
    ColumnMapping,
    SchemaMapper,
)
from backend.normalization.schemas import (
    BusinessDomain,
    InternalSchema,
    get_all_schemas,
    get_schema_by_name,
    get_schema_for_domain,
)
from backend.normalization.transformer import (
    SafeDataTransformer,
    TransformationReport,
)

logger = logging.getLogger(__name__)


# ============================================================
# Résultat global de la normalisation
# ============================================================


@dataclass
class NormalizationResult:
    """
    Résultat complet de la normalisation d'un dataset.

    Attributes:
        success:             True si le dataset normalisé est prêt à être analysé.
        normalized_df:       DataFrame transformé (None si échec irrécupérable).
        schema:              Schéma cible utilisé (None si aucun schéma compatible).
        domain_prediction:   Domaine métier détecté.
        profile:             Profil structurel du dataset.
        mappings:            Liste des mappings colonne → concept.
        report:              Rapport de transformation.
        compatible_schemas:  Liste des schémas potentiellement compatibles
                             (pour suggérer des alternatives à l'utilisateur).
    """

    success: bool
    normalized_df: Optional[pd.DataFrame]
    schema: Optional[InternalSchema]
    domain_prediction: DomainPrediction
    profile: DatasetProfile
    mappings: List[ColumnMapping]
    report: TransformationReport
    compatible_schemas: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        """Sérialise le résultat (sans le DataFrame) pour l'API."""
        return {
            "success": self.success,
            "schema": self.schema.name if self.schema else None,
            "domain": self.domain_prediction.to_dict(),
            "profile": self.profile.to_dict(),
            "mappings": [m.to_dict() for m in self.mappings],
            "report": self.report.to_dict(),
            "compatible_schemas": self.compatible_schemas,
        }

    def get_explanation(self) -> str:
        """Texte explicatif court pour l'utilisateur final (frontend)."""
        if self.success and self.schema is not None:
            mapped = sum(1 for m in self.mappings if m.is_mapped)
            return (
                f"Dataset reconnu comme '{self.domain_prediction.domain.value}' "
                f"(confiance {self.domain_prediction.confidence:.0%}). "
                f"Normalisé vers le schéma '{self.schema.name}' : "
                f"{mapped}/{len(self.mappings)} colonnes mappées."
            )

        if self.schema is None:
            return (
                f"Aucun schéma compatible. "
                f"Domaine détecté : {self.domain_prediction.domain.value}."
            )

        missing = ", ".join(self.report.missing_required[:3])
        return (
            f"Normalisation incomplète vers '{self.schema.name}' : "
            f"colonnes requises manquantes ({missing}...)."
        )


# ============================================================
# Pipeline principal
# ============================================================


class NormalizationPipeline:
    """
    Orchestre les 4 étapes : profilage → détection → mapping → transformation.

    Le pipeline est stateless (peut être instancié une seule fois et réutilisé).
    Les sous-composants (mapper, detector) sont configurables individuellement.

    Attributes:
        profiler:    DatasetProfiler (instance ou None pour défaut).
        detector:    BusinessDomainDetector.
        mapper:      SchemaMapper.
        transformer: SafeDataTransformer.
    """

    def __init__(
        self,
        profiler: Optional[DatasetProfiler] = None,
        detector: Optional[BusinessDomainDetector] = None,
        mapper: Optional[SchemaMapper] = None,
        transformer: Optional[SafeDataTransformer] = None,
        use_llm_fallback: bool = False,
        use_semantic: bool = True,
    ) -> None:
        self.profiler = profiler or DatasetProfiler()
        self.detector = detector or BusinessDomainDetector(
            use_llm_fallback=use_llm_fallback
        )
        self.mapper = mapper or SchemaMapper(
            use_llm_fallback=use_llm_fallback,
            use_semantic=use_semantic,
        )
        self.transformer = transformer or SafeDataTransformer()

    # ----------------------------------------------------------
    # API publique
    # ----------------------------------------------------------

    def normalize(
        self,
        df: pd.DataFrame,
        target_schema_name: Optional[str] = None,
    ) -> NormalizationResult:
        """
        Pipeline complet : profilage → détection → mapping → transformation.

        Args:
            df:                  DataFrame uploadé (préservé, jamais modifié).
            target_schema_name:  Si fourni, force le schéma cible. Sinon, le
                                 schéma est déterminé par le domaine détecté.

        Returns:
            NormalizationResult.
        """
        logger.info(
            "=== Démarrage du pipeline de normalisation : %d × %d ===",
            len(df), len(df.columns),
        )

        # Étape 1 : profilage
        profile = self.profiler.profile(df)

        # Étape 2 : détection du domaine métier
        domain_prediction = self.detector.detect(profile)
        logger.info(
            "Domaine détecté : %s (confiance %.2f)",
            domain_prediction.domain.value, domain_prediction.confidence,
        )

        # Étape 3 : sélection du schéma cible
        target_schema = self._select_target_schema(
            target_schema_name, domain_prediction.domain, profile
        )

        if target_schema is None:
            return self._build_failure_result(
                profile=profile,
                domain_prediction=domain_prediction,
                reason="Aucun schéma compatible pour le domaine détecté.",
            )

        # Étape 4 : mapping des colonnes
        mappings = self.mapper.map_columns(
            profile,
            target_schema=target_schema,
        )

        # Étape 5 : transformation et validation
        normalized_df, report = self.transformer.transform(
            df, mappings, target_schema
        )

        # Schémas compatibles (suggestion pour l'utilisateur)
        compatible = self._find_compatible_schemas(mappings)

        result = NormalizationResult(
            success=report.success,
            normalized_df=normalized_df if report.success else None,
            schema=target_schema,
            domain_prediction=domain_prediction,
            profile=profile,
            mappings=mappings,
            report=report,
            compatible_schemas=compatible,
        )

        logger.info(
            "=== Normalisation terminée : success=%s, schema=%s ===",
            result.success, target_schema.name,
        )
        return result

    def normalize_all_schemas(
        self,
        df: pd.DataFrame,
    ) -> Dict[str, NormalizationResult]:
        """
        Tente la normalisation contre chaque schéma enregistré.

        Utile quand le domaine est ambigu : retourne tous les résultats pour
        que l'appelant choisisse celui qui réussit le mieux.

        Returns:
            Dict {schema_name: NormalizationResult}.
        """
        results: Dict[str, NormalizationResult] = {}

        # Pré-calcul (mutualise le profilage et la détection)
        profile = self.profiler.profile(df)
        domain_prediction = self.detector.detect(profile)

        for schema in get_all_schemas():
            mappings = self.mapper.map_columns(profile, target_schema=schema)
            normalized_df, report = self.transformer.transform(df, mappings, schema)

            results[schema.name] = NormalizationResult(
                success=report.success,
                normalized_df=normalized_df if report.success else None,
                schema=schema,
                domain_prediction=domain_prediction,
                profile=profile,
                mappings=mappings,
                report=report,
                compatible_schemas=[],
            )

        return results

    # ----------------------------------------------------------
    # Sélection du schéma cible
    # ----------------------------------------------------------

    @staticmethod
    def _select_target_schema(
        target_schema_name: Optional[str],
        detected_domain: BusinessDomain,
        profile: DatasetProfile,
    ) -> Optional[InternalSchema]:
        """
        Sélectionne le schéma cible.

        Priorité :
            1. Nom de schéma explicite (paramètre user)
            2. Heuristique format clé-valeur littéral (indicateur / valeur)
            3. Heuristique format clé-valeur sémantique (2 colonnes dont une
               mappable sur INDICATOR_NAME et l'autre sur INDICATOR_VALUE)
            4. Premier schéma associé au domaine détecté
        """
        from backend.normalization.synonyms import find_concept_by_synonym
        from backend.normalization.schemas import CanonicalConcept

        if target_schema_name is not None:
            schema = get_schema_by_name(target_schema_name)
            if schema is None:
                logger.warning(
                    "Schéma demandé inconnu : %s", target_schema_name,
                )
            return schema

        # Heuristique 1 : clé-valeur littéral (français exact)
        col_names = {c.normalized_name for c in profile.columns}
        if "indicateur" in col_names and "valeur" in col_names:
            return get_schema_by_name("kpis")

        # Heuristique 2 : clé-valeur sémantique (kpi_name + value, etc.)
        if len(profile.columns) == 2:
            concepts_found = {
                find_concept_by_synonym(c.name) for c in profile.columns
            }
            if (
                CanonicalConcept.INDICATOR_NAME in concepts_found
                and CanonicalConcept.INDICATOR_VALUE in concepts_found
            ):
                return get_schema_by_name("kpis")

        # Heuristique 3 : schéma par défaut du domaine détecté
        schemas = get_schema_for_domain(detected_domain)
        return schemas[0] if schemas else None

    # ----------------------------------------------------------
    # Schémas compatibles
    # ----------------------------------------------------------

    @staticmethod
    def _find_compatible_schemas(mappings: List[ColumnMapping]) -> List[str]:
        """
        Détermine quels schémas seraient satisfaits par les mappings produits.

        Un schéma est "compatible" si tous ses concepts requis ont au moins
        une colonne mappée correspondante.
        """
        mapped_concepts = {
            m.target_concept for m in mappings
            if m.is_mapped and m.target_concept is not None
        }

        compatible: List[str] = []
        for schema in get_all_schemas():
            if schema.required_concepts.issubset(mapped_concepts):
                compatible.append(schema.name)
        return compatible

    # ----------------------------------------------------------
    # Résultats d'échec
    # ----------------------------------------------------------

    @staticmethod
    def _build_failure_result(
        profile: DatasetProfile,
        domain_prediction: DomainPrediction,
        reason: str,
    ) -> NormalizationResult:
        """Construit un NormalizationResult d'échec sans transformation."""
        report = TransformationReport(
            success=False,
            target_schema_name="",
            errors=[reason],
        )
        return NormalizationResult(
            success=False,
            normalized_df=None,
            schema=None,
            domain_prediction=domain_prediction,
            profile=profile,
            mappings=[],
            report=report,
            compatible_schemas=[],
        )
