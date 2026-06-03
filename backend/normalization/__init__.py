"""
Couche de normalisation sémantique des datasets.

Cette couche convertit automatiquement des datasets hétérogènes uploadés
par l'utilisateur vers les schémas internes standardisés attendus par les
analyzers existants. Les analyzers restent inchangés.

Architecture :
    DatasetProfiler         → analyse structure et types
    BusinessDomainDetector  → classifie en finance/marketing/.../produits
    SchemaMapper            → mappe colonnes inconnues → concepts canoniques
    SafeDataTransformer     → applique transformations préservant l'original
    NormalizationPipeline   → orchestre l'ensemble

Usage :
    from backend.normalization import NormalizationPipeline

    pipeline = NormalizationPipeline()
    result = pipeline.normalize(df)

    # result.normalized_df       → DataFrame prêt pour les analyzers
    # result.domain              → "finance" | "marketing" | ...
    # result.mapping_report      → métadonnées d'explicabilité
    # result.compatible_schemas  → liste des analyzers compatibles
"""

from backend.normalization.pipeline import (
    NormalizationPipeline,
    NormalizationResult,
)
from backend.normalization.schemas import (
    BusinessDomain,
    CanonicalConcept,
    InternalSchema,
    get_schema_for_domain,
)
from backend.normalization.profiler import DatasetProfile, DatasetProfiler
from backend.normalization.domain_detector import BusinessDomainDetector
from backend.normalization.schema_mapper import ColumnMapping, SchemaMapper
from backend.normalization.transformer import (
    SafeDataTransformer,
    TransformationReport,
)

__all__ = [
    "NormalizationPipeline",
    "NormalizationResult",
    "BusinessDomain",
    "CanonicalConcept",
    "InternalSchema",
    "get_schema_for_domain",
    "DatasetProfile",
    "DatasetProfiler",
    "BusinessDomainDetector",
    "ColumnMapping",
    "SchemaMapper",
    "SafeDataTransformer",
    "TransformationReport",
]
