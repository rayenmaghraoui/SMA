"""
Profileur de datasets — analyse structurelle d'un DataFrame uploadé.

Le DatasetProfiler génère un profil exhaustif d'un dataset :
    - typage des colonnes (numérique / catégoriel / date / texte)
    - statistiques descriptives (min, max, mean, median, std)
    - taux de valeurs manquantes par colonne
    - cardinalité (nombre de valeurs uniques)
    - détection d'anomalies structurelles (colonnes vides, types mélangés)

Le profil est ensuite consommé par :
    - BusinessDomainDetector → pour pondérer la détection par les types
    - SchemaMapper           → pour confirmer/réfuter les mappings (un concept
                                 numérique ne peut pas être mappé sur une
                                 colonne textuelle)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ============================================================
# Types de colonnes
# ============================================================


class ColumnKind(str, Enum):
    """
    Type sémantique d'une colonne, distinct du dtype Pandas brut.

    NUMERIC      : valeurs numériques continues (int/float)
    CATEGORICAL  : texte avec cardinalité limitée (< 10% du nb de lignes)
    DATE         : dates ou timestamps
    TEXT         : texte libre (cardinalité élevée)
    IDENTIFIER   : identifiants uniques ou quasi-uniques
    BOOLEAN      : booléens
    UNKNOWN      : non identifiable (ex : colonne vide)
    """

    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    DATE = "date"
    TEXT = "text"
    IDENTIFIER = "identifier"
    BOOLEAN = "boolean"
    UNKNOWN = "unknown"


# ============================================================
# Profil d'une colonne individuelle
# ============================================================


@dataclass
class ColumnProfile:
    """
    Profil structurel et statistique d'une seule colonne.

    Attributes:
        name:             Nom original de la colonne (avant normalisation).
        normalized_name:  Nom en lowercase/underscores (utilisé pour le mapping).
        kind:             Type sémantique inféré.
        dtype:            dtype Pandas brut ("int64", "object", ...).
        non_null_count:   Nombre de valeurs non nulles.
        null_count:       Nombre de valeurs nulles.
        null_ratio:       Ratio de valeurs nulles (0.0 - 1.0).
        unique_count:     Nombre de valeurs distinctes.
        unique_ratio:     unique_count / non_null_count.
        sample_values:    Échantillon de valeurs (max 5, pour debug/LLM).
        stats:            Statistiques descriptives (numérique uniquement).
    """

    name: str
    normalized_name: str
    kind: ColumnKind
    dtype: str
    non_null_count: int
    null_count: int
    null_ratio: float
    unique_count: int
    unique_ratio: float
    sample_values: List[Any] = field(default_factory=list)
    stats: Optional[Dict[str, float]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Conversion en dict sérialisable JSON."""
        return {
            "name": self.name,
            "normalized_name": self.normalized_name,
            "kind": self.kind.value,
            "dtype": self.dtype,
            "non_null_count": self.non_null_count,
            "null_count": self.null_count,
            "null_ratio": round(self.null_ratio, 4),
            "unique_count": self.unique_count,
            "unique_ratio": round(self.unique_ratio, 4),
            "sample_values": [_to_jsonable(v) for v in self.sample_values],
            "stats": self.stats,
        }


# ============================================================
# Profil global du dataset
# ============================================================


@dataclass
class DatasetProfile:
    """
    Profil global d'un dataset.

    Attributes:
        n_rows:          Nombre de lignes.
        n_columns:       Nombre de colonnes.
        columns:         Profils individuels (1 par colonne).
        structural_issues: Liste d'anomalies structurelles (DataFrame vide,
                           colonnes 100% nulles, doublons d'en-tête, ...).
    """

    n_rows: int
    n_columns: int
    columns: List[ColumnProfile]
    structural_issues: List[str] = field(default_factory=list)

    @property
    def numeric_columns(self) -> List[ColumnProfile]:
        """Colonnes typées NUMERIC."""
        return [c for c in self.columns if c.kind == ColumnKind.NUMERIC]

    @property
    def categorical_columns(self) -> List[ColumnProfile]:
        """Colonnes typées CATEGORICAL."""
        return [c for c in self.columns if c.kind == ColumnKind.CATEGORICAL]

    @property
    def date_columns(self) -> List[ColumnProfile]:
        """Colonnes typées DATE."""
        return [c for c in self.columns if c.kind == ColumnKind.DATE]

    def get_column(self, name: str) -> Optional[ColumnProfile]:
        """Retourne le profil d'une colonne par son nom original."""
        for col in self.columns:
            if col.name == name:
                return col
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Conversion en dict sérialisable JSON."""
        return {
            "n_rows": self.n_rows,
            "n_columns": self.n_columns,
            "columns": [c.to_dict() for c in self.columns],
            "structural_issues": self.structural_issues,
        }


# ============================================================
# Profileur principal
# ============================================================


class DatasetProfiler:
    """
    Profile un DataFrame pour préparer la normalisation sémantique.

    Le profilage est purement structurel : aucun appel LLM, aucun
    chargement de modèle. Il ne lit que le DataFrame fourni.

    Attributes:
        max_unique_for_categorical:  Au-delà, une colonne object est
                                     considérée TEXT plutôt que CATEGORICAL.
        identifier_unique_ratio:     Ratio minimal pour qualifier une
                                     colonne d'IDENTIFIER (par défaut 0.95).
        sample_size:                 Nombre de valeurs échantillonnées
                                     par colonne (pour debug/LLM fallback).
    """

    def __init__(
        self,
        max_unique_for_categorical: int = 50,
        identifier_unique_ratio: float = 0.95,
        sample_size: int = 5,
    ) -> None:
        self.max_unique_for_categorical = max_unique_for_categorical
        self.identifier_unique_ratio = identifier_unique_ratio
        self.sample_size = sample_size

    # ----------------------------------------------------------
    # API publique
    # ----------------------------------------------------------

    def profile(self, df: pd.DataFrame) -> DatasetProfile:
        """
        Génère le profil complet d'un DataFrame.

        Args:
            df: DataFrame à analyser.

        Returns:
            DatasetProfile contenant les profils de chaque colonne et
            la liste des anomalies structurelles détectées.
        """
        logger.info(
            "Profilage du dataset : %d lignes × %d colonnes",
            len(df), len(df.columns),
        )

        structural_issues = self._detect_structural_issues(df)

        column_profiles: List[ColumnProfile] = []
        for col in df.columns:
            try:
                profile = self._profile_column(df[col], str(col))
                column_profiles.append(profile)
            except Exception as e:
                logger.warning("Échec du profilage de la colonne '%s' : %s", col, e)
                structural_issues.append(
                    f"Colonne '{col}' : échec du profilage ({type(e).__name__})"
                )

        return DatasetProfile(
            n_rows=len(df),
            n_columns=len(df.columns),
            columns=column_profiles,
            structural_issues=structural_issues,
        )

    # ----------------------------------------------------------
    # Détection des anomalies structurelles
    # ----------------------------------------------------------

    def _detect_structural_issues(self, df: pd.DataFrame) -> List[str]:
        """Détecte les problèmes globaux : DataFrame vide, doublons, ..."""
        issues: List[str] = []

        if df.empty:
            issues.append("Le DataFrame est vide (aucune ligne).")
            return issues

        if len(df.columns) == 0:
            issues.append("Le DataFrame ne contient aucune colonne.")
            return issues

        # Doublons d'en-tête
        if df.columns.duplicated().any():
            duplicates = df.columns[df.columns.duplicated()].tolist()
            issues.append(f"Colonnes dupliquées détectées : {duplicates}")

        # Colonnes 100% nulles
        fully_null = [c for c in df.columns if df[c].isna().all()]
        if fully_null:
            issues.append(f"Colonnes entièrement nulles : {fully_null}")

        # Lignes 100% nulles
        if df.isna().all(axis=1).any():
            issues.append("Certaines lignes sont entièrement nulles.")

        return issues

    # ----------------------------------------------------------
    # Profilage colonne par colonne
    # ----------------------------------------------------------

    def _profile_column(self, series: pd.Series, name: str) -> ColumnProfile:
        """Profile une seule colonne."""
        non_null = series.dropna()
        non_null_count = len(non_null)
        null_count = int(series.isna().sum())
        total = len(series)
        null_ratio = null_count / total if total > 0 else 0.0

        unique_count = int(non_null.nunique()) if non_null_count > 0 else 0
        unique_ratio = unique_count / non_null_count if non_null_count > 0 else 0.0

        kind = self._infer_kind(series, non_null, unique_count, unique_ratio)
        stats = self._compute_stats(non_null) if kind == ColumnKind.NUMERIC else None
        sample = self._sample_values(non_null)

        return ColumnProfile(
            name=name,
            normalized_name=_normalize_column_name(name),
            kind=kind,
            dtype=str(series.dtype),
            non_null_count=non_null_count,
            null_count=null_count,
            null_ratio=null_ratio,
            unique_count=unique_count,
            unique_ratio=unique_ratio,
            sample_values=sample,
            stats=stats,
        )

    def _infer_kind(
        self,
        series: pd.Series,
        non_null: pd.Series,
        unique_count: int,
        unique_ratio: float,
    ) -> ColumnKind:
        """
        Infère le type sémantique d'une colonne.

        Ordre des règles :
            1. dtype booléen     → BOOLEAN
            2. dtype datetime    → DATE
            3. dtype numérique   → NUMERIC (sauf si quasi-unique → IDENTIFIER)
            4. dtype object      → tentative conversion datetime → DATE
            5. dtype object      → cardinalité faible → CATEGORICAL
            6. dtype object      → cardinalité quasi-totale → IDENTIFIER
            7. dtype object      → autre → TEXT
            8. Aucun cas         → UNKNOWN
        """
        if len(non_null) == 0:
            return ColumnKind.UNKNOWN

        dtype = series.dtype

        # 1. Booléen
        if pd.api.types.is_bool_dtype(dtype):
            return ColumnKind.BOOLEAN

        # 2. Datetime natif
        if pd.api.types.is_datetime64_any_dtype(dtype):
            return ColumnKind.DATE

        # 3. Numérique
        if pd.api.types.is_numeric_dtype(dtype):
            # Une colonne numérique quasi-unique est probablement un ID
            # (ex : invoice_id stocké en int) — mais peu fréquent en pratique.
            if unique_ratio >= self.identifier_unique_ratio and len(non_null) >= 10:
                return ColumnKind.IDENTIFIER
            return ColumnKind.NUMERIC

        # 4. Object → tentative conversion datetime
        if dtype == object or pd.api.types.is_string_dtype(dtype):
            if self._looks_like_date(non_null):
                return ColumnKind.DATE

            # 5/6/7. Discrimination CATEGORICAL / IDENTIFIER / TEXT
            if unique_ratio >= self.identifier_unique_ratio and len(non_null) >= 10:
                return ColumnKind.IDENTIFIER

            if unique_count <= self.max_unique_for_categorical:
                return ColumnKind.CATEGORICAL

            return ColumnKind.TEXT

        return ColumnKind.UNKNOWN

    @staticmethod
    def _looks_like_date(non_null: pd.Series) -> bool:
        """
        Heuristique pour détecter une colonne date stockée en string.

        Tente une conversion to_datetime sur un échantillon de 20 valeurs.
        Si > 80% sont convertibles, la colonne est considérée date.
        """
        sample = non_null.head(20)
        try:
            converted = pd.to_datetime(sample, errors="coerce", format="mixed")
            success_ratio = converted.notna().mean()
            return bool(success_ratio >= 0.8)
        except Exception:
            return False

    @staticmethod
    def _compute_stats(non_null: pd.Series) -> Dict[str, float]:
        """Calcule min/max/mean/median/std pour une colonne numérique."""
        try:
            return {
                "min":    float(non_null.min()),
                "max":    float(non_null.max()),
                "mean":   round(float(non_null.mean()), 4),
                "median": round(float(non_null.median()), 4),
                "std":    round(float(non_null.std()), 4) if len(non_null) > 1 else 0.0,
            }
        except Exception as e:
            logger.debug("Échec du calcul des stats : %s", e)
            return {}

    def _sample_values(self, non_null: pd.Series) -> List[Any]:
        """Retourne un échantillon de valeurs pour le LLM fallback."""
        if len(non_null) == 0:
            return []
        sample_n = min(self.sample_size, len(non_null))
        return non_null.head(sample_n).tolist()


# ============================================================
# Utilitaires
# ============================================================


def _normalize_column_name(name: str) -> str:
    """
    Normalise un nom de colonne pour matching.

    Reproduit la convention utilisée par synonyms._normalize_term().
    Centralisé ici pour éviter une dépendance circulaire.
    """
    if not name:
        return ""

    normalized = str(name).strip().lower()
    normalized = normalized.replace(" ", "_").replace("-", "_")

    accents = {
        "à": "a", "â": "a", "ä": "a",
        "é": "e", "è": "e", "ê": "e", "ë": "e",
        "î": "i", "ï": "i",
        "ô": "o", "ö": "o",
        "ù": "u", "û": "u", "ü": "u",
        "ç": "c",
    }
    for a, b in accents.items():
        normalized = normalized.replace(a, b)
    return normalized


def _to_jsonable(value: Any) -> Any:
    """Convertit une valeur Pandas en quelque chose de JSON-sérialisable."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()
    if isinstance(value, (np.bool_,)):
        return bool(value)
    return value
