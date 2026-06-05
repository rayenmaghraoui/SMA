"""
Sch\u00e9mas Pydantic pour les requ\u00eates entrantes de l'API.
"""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    """
    Requ\u00eate pour lancer l'analyse des donn\u00e9es.

    Attributes:
        use_defaults: Si True, utilise les fichiers CSV par d\u00e9faut.
        force: Si True, ignore le cache et relance le pipeline complet.
    """

    use_defaults: bool = Field(
        default=True,
        description="Utiliser les fichiers CSV par d\u00e9faut (data/)"
    )
    force: bool = Field(
        default=False,
        description="Forcer une nouvelle analyse en ignorant le cache"
    )


class ChatRequest(BaseModel):
    """
    Requ\u00eate pour le chat en langage naturel.

    Attributes:
        message: Question de l'utilisateur en fran\u00e7ais.
        history: Historique des 3 derniers \u00e9changes (max 6 messages).
    """

    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Question de l'utilisateur"
    )
    history: List[Dict[str, str]] = Field(
        default=[],
        description="Historique [{role, content}] \u2014 max 3 tours (6 messages)"
    )


class UploadRequest(BaseModel):
    """
    M\u00e9tadonn\u00e9es pour l'upload de fichiers.

    Note: Le fichier lui-m\u00eame est envoy\u00e9 via multipart/form-data,
    ce mod\u00e8le est utilis\u00e9 pour les m\u00e9tadonn\u00e9es optionnelles.

    Attributes:
        dataset_type: Type de dataset ("finance", "marketing", "support").
    """

    dataset_type: Optional[str] = Field(
        default=None,
        pattern="^(finance|marketing|support)$",
        description="Type de dataset : finance, marketing ou support"
    )


class SqlQueryRequest(BaseModel):
    """
    Requête pour l'exploration de données via SQL généré par le LLM.

    Attributes:
        question: Question en langage naturel à convertir en SQL.
    """

    question: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Question en langage naturel sur les données",
        examples=["Montre-moi les 10 meilleures campagnes par conversions"],
    )


class ForecastRequest(BaseModel):
    """
    Requête pour la prévision des ventes futures.

    Attributes:
        horizon: Nombre de mois à prévoir (entre 1 et 12).
    """

    horizon: int = Field(
        default=3,
        ge=1,
        le=12,
        description="Nombre de mois futurs à prévoir",
    )


class ComparePeriodsRequest(BaseModel):
    """
    Requête pour la comparaison de deux périodes.

    Attributes:
        period_a_start: Date de début de la période A (YYYY-MM-DD).
        period_a_end:   Date de fin de la période A (YYYY-MM-DD).
        period_b_start: Date de début de la période B (YYYY-MM-DD).
        period_b_end:   Date de fin de la période B (YYYY-MM-DD).
    """

    period_a_start: str = Field(..., description="Début période A (YYYY-MM-DD)")
    period_a_end: str = Field(..., description="Fin période A (YYYY-MM-DD)")
    period_b_start: str = Field(..., description="Début période B (YYYY-MM-DD)")
    period_b_end: str = Field(..., description="Fin période B (YYYY-MM-DD)")
