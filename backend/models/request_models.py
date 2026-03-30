"""
Sch\u00e9mas Pydantic pour les requ\u00eates entrantes de l'API.
"""

from typing import Optional

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    """
    Requ\u00eate pour lancer l'analyse des donn\u00e9es.

    Attributes:
        use_defaults: Si True, utilise les fichiers CSV par d\u00e9faut.
                      Si False, attend un upload pr\u00e9alable.
    """

    use_defaults: bool = Field(
        default=True,
        description="Utiliser les fichiers CSV par d\u00e9faut (data/)"
    )


class ChatRequest(BaseModel):
    """
    Requ\u00eate pour le chat en langage naturel.

    Attributes:
        message: Question de l'utilisateur en fran\u00e7ais.
    """

    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Question de l'utilisateur"
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
