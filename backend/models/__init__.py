"""Package models \u2014 sch\u00e9mas Pydantic pour l'API."""

from backend.models.request_models import (
    AnalyzeRequest,
    ChatRequest,
    UploadRequest,
)
from backend.models.response_models import (
    AnalyzeResponse,
    HealthResponse,
    UploadResponse,
    ReportResponse,
    Anomaly,
    FinanceKPIs,
    MarketingKPIs,
    SupportKPIs,
    AllKPIs,
)

__all__ = [
    # Request models
    "AnalyzeRequest",
    "ChatRequest",
    "UploadRequest",
    # Response models
    "AnalyzeResponse",
    "HealthResponse",
    "UploadResponse",
    "ReportResponse",
    "Anomaly",
    "FinanceKPIs",
    "MarketingKPIs",
    "SupportKPIs",
    "AllKPIs",
]
