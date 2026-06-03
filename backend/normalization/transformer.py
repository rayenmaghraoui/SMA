"""
SafeDataTransformer — application sûre des mappings sur un DataFrame.

Responsabilités :
    - Créer une COPIE du DataFrame uploadé (l'original n'est jamais touché).
    - Renommer les colonnes selon les mappings validés (concept → nom legacy).
    - Convertir les types si nécessaire (date strings → datetime, etc.).
    - Valider que les colonnes requises par le schéma cible sont présentes.
    - Générer un TransformationReport explicite avec décisions et warnings.

Principes :
    - Aucune perte de données : les colonnes non mappées sont préservées
      (renommées avec préfixe "_unmapped_" pour signaler leur état).
    - Échec sûr : si le mapping rend le DataFrame incompatible avec le
      schéma cible, on génère un rapport d'erreur SANS lever d'exception
      (l'appelant décide de la suite).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import pandas as pd

from backend.normalization.schema_mapper import ColumnMapping
from backend.normalization.schemas import (
    CanonicalConcept,
    InternalSchema,
    get_column_for_schema,
)

logger = logging.getLogger(__name__)


# ============================================================
# Rapport de transformation
# ============================================================


@dataclass
class TransformationReport:
    """
    Rapport explicite de la transformation appliquée.

    Attributes:
        success:                  True si le DataFrame transformé satisfait
                                  le schéma cible (toutes colonnes requises
                                  présentes, types compatibles).
        target_schema_name:       Nom du schéma cible.
        applied_renames:          Dict {source_column: target_column}.
        unmapped_columns:         Colonnes uploadées non mappées (préservées).
        missing_required:         Concepts requis non disponibles dans le dataset.
        warnings:                 Avertissements non bloquants.
        errors:                   Erreurs bloquantes.
        mapping_confidences:      Confidence de chaque mapping appliqué.
    """

    success: bool
    target_schema_name: str
    applied_renames: Dict[str, str] = field(default_factory=dict)
    unmapped_columns: List[str] = field(default_factory=list)
    missing_required: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    mapping_confidences: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "target_schema_name": self.target_schema_name,
            "applied_renames": self.applied_renames,
            "unmapped_columns": self.unmapped_columns,
            "missing_required": self.missing_required,
            "warnings": self.warnings,
            "errors": self.errors,
            "mapping_confidences": {
                k: round(v, 4) for k, v in self.mapping_confidences.items()
            },
        }


# ============================================================
# Transformer principal
# ============================================================


class SafeDataTransformer:
    """
    Applique les mappings sur un DataFrame de façon sûre et tracée.

    Garanties :
        - L'objet DataFrame original n'est jamais modifié (copie systématique).
        - Tout renommage produit un nom de colonne distinct des originaux
          pour éviter les collisions.
        - Les colonnes non mappées sont préservées avec un préfixe.
        - Le rapport contient suffisamment d'information pour reconstruire
          la transformation à la main si nécessaire.

    Attributes:
        keep_unmapped:               Conserve les colonnes non mappées (préfixe).
        coerce_dates:                Convertit les colonnes mappées sur DATE.
        coerce_numerics:             Convertit les colonnes mappées sur NUMERIC.
        unmapped_prefix:             Préfixe pour les colonnes non mappées.
    """

    def __init__(
        self,
        keep_unmapped: bool = True,
        coerce_dates: bool = True,
        coerce_numerics: bool = True,
        unmapped_prefix: str = "_unmapped_",
    ) -> None:
        self.keep_unmapped = keep_unmapped
        self.coerce_dates = coerce_dates
        self.coerce_numerics = coerce_numerics
        self.unmapped_prefix = unmapped_prefix

    # ----------------------------------------------------------
    # API publique
    # ----------------------------------------------------------

    def transform(
        self,
        df: pd.DataFrame,
        mappings: List[ColumnMapping],
        target_schema: InternalSchema,
    ) -> tuple[pd.DataFrame, TransformationReport]:
        """
        Transforme un DataFrame selon les mappings et valide vs le schéma.

        Args:
            df:             DataFrame source (jamais modifié).
            mappings:       Liste de ColumnMapping (issu de SchemaMapper).
            target_schema:  Schéma cible à satisfaire.

        Returns:
            Tuple (DataFrame normalisé, TransformationReport).
        """
        logger.info(
            "Transformation vers schéma '%s' : %d colonnes source, %d mappings",
            target_schema.name, len(df.columns), len(mappings),
        )

        # Copie défensive de l'original
        normalized = df.copy()

        # Construction des renommages cohérents avec le schéma cible
        rename_map: Dict[str, str] = {}
        confidences: Dict[str, float] = {}

        for mapping in mappings:
            if not mapping.is_mapped or mapping.target_concept is None:
                continue

            # Le nom de colonne cible dépend du schéma (overrides legacy)
            target_col = get_column_for_schema(
                target_schema.name, mapping.target_concept
            )

            # Évite les collisions : si la cible existe déjà dans le DataFrame
            # source, on ne renomme pas (la colonne source est ignorée).
            if target_col in normalized.columns and target_col != mapping.source_column:
                logger.debug(
                    "Collision : '%s' existe déjà → '%s' non renommée",
                    target_col, mapping.source_column,
                )
                continue

            rename_map[mapping.source_column] = target_col
            confidences[target_col] = mapping.confidence

        # Application des renommages
        normalized = normalized.rename(columns=rename_map)

        # Colonnes non mappées : préfixage pour les distinguer visuellement
        unmapped_source = [
            m.source_column for m in mappings
            if not m.is_mapped and m.source_column in normalized.columns
        ]

        if not self.keep_unmapped and unmapped_source:
            normalized = normalized.drop(columns=unmapped_source, errors="ignore")
        elif unmapped_source:
            unmapped_rename = {
                col: f"{self.unmapped_prefix}{col}" for col in unmapped_source
            }
            normalized = normalized.rename(columns=unmapped_rename)

        # Coercition de types pour les colonnes mappées
        warnings: List[str] = []
        if self.coerce_dates or self.coerce_numerics:
            normalized, type_warnings = self._coerce_types(
                normalized, mappings, target_schema
            )
            warnings.extend(type_warnings)

        # Validation : toutes les colonnes requises sont-elles présentes ?
        missing = self._validate_required_columns(normalized, target_schema)

        success = len(missing) == 0
        errors: List[str] = []
        if missing:
            errors.append(
                f"Colonnes requises manquantes pour le schéma "
                f"'{target_schema.name}' : {missing}"
            )

        report = TransformationReport(
            success=success,
            target_schema_name=target_schema.name,
            applied_renames=rename_map,
            unmapped_columns=unmapped_source,
            missing_required=missing,
            warnings=warnings,
            errors=errors,
            mapping_confidences=confidences,
        )

        logger.info(
            "Transformation terminée : success=%s, %d renames, %d non-mappés, %d manquants",
            success, len(rename_map), len(unmapped_source), len(missing),
        )

        return normalized, report

    # ----------------------------------------------------------
    # Coercition de types
    # ----------------------------------------------------------

    def _coerce_types(
        self,
        df: pd.DataFrame,
        mappings: List[ColumnMapping],
        target_schema: InternalSchema,
    ) -> tuple[pd.DataFrame, List[str]]:
        """
        Convertit les colonnes mappées vers leur type attendu.

        Cette étape est best-effort : si la conversion échoue, on émet un
        warning et on conserve la colonne en l'état (l'analyzer cible
        décidera de son sort).
        """
        warnings: List[str] = []

        # Concepts qui DOIVENT être numériques (par tout schéma)
        numeric_concepts = {
            CanonicalConcept.REVENUE, CanonicalConcept.PROFIT, CanonicalConcept.COST,
            CanonicalConcept.UNIT_PRICE, CanonicalConcept.AVG_PRICE,
            CanonicalConcept.AVG_BASKET, CanonicalConcept.PROFIT_MARGIN,
            CanonicalConcept.GROWTH_RATE, CanonicalConcept.BUDGET,
            CanonicalConcept.QUANTITY, CanonicalConcept.TOTAL_QUANTITY,
            CanonicalConcept.NB_TRANSACTIONS, CanonicalConcept.NB_CUSTOMERS,
            CanonicalConcept.CLICKS, CanonicalConcept.CONVERSIONS,
            CanonicalConcept.CONVERSION_RATE, CanonicalConcept.INDICATOR_VALUE,
            CanonicalConcept.RESOLUTION_HOURS,
        }
        date_concepts = {CanonicalConcept.DATE}

        for mapping in mappings:
            if not mapping.is_mapped or mapping.target_concept is None:
                continue

            target_col = get_column_for_schema(
                target_schema.name, mapping.target_concept
            )
            if target_col not in df.columns:
                continue

            try:
                if self.coerce_numerics and mapping.target_concept in numeric_concepts:
                    if not pd.api.types.is_numeric_dtype(df[target_col]):
                        df[target_col] = pd.to_numeric(
                            df[target_col], errors="coerce"
                        )
                elif self.coerce_dates and mapping.target_concept in date_concepts:
                    if not pd.api.types.is_datetime64_any_dtype(df[target_col]):
                        df[target_col] = pd.to_datetime(
                            df[target_col], errors="coerce", format="mixed"
                        )
            except Exception as e:
                warnings.append(
                    f"Coercition échouée pour '{target_col}' ({mapping.target_concept.value}) : {e}"
                )

        return df, warnings

    # ----------------------------------------------------------
    # Validation
    # ----------------------------------------------------------

    @staticmethod
    def _validate_required_columns(
        df: pd.DataFrame,
        target_schema: InternalSchema,
    ) -> List[str]:
        """
        Vérifie que toutes les colonnes requises par le schéma sont présentes.

        Returns:
            Liste des colonnes manquantes (vide si tout est OK).
        """
        present = set(df.columns)
        required = [
            get_column_for_schema(target_schema.name, c)
            for c in target_schema.required_concepts
        ]
        missing = [col for col in required if col not in present]
        return missing
