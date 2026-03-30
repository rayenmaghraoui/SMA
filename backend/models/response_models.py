"""
Sch\u00e9mas Pydantic pour les r\u00e9ponses sortantes de l'API.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ============================================================
# KPIs par domaine
# ============================================================

class FinanceKPIs(BaseModel):
    """KPIs financiers calcul\u00e9s par l'analyse."""

    revenue_total: float = Field(..., description="Chiffre d'affaires total (TND)")
    profit_total: float = Field(..., description="B\u00e9n\u00e9fice net total (TND)")
    profit_margin: float = Field(..., description="Marge b\u00e9n\u00e9ficiaire moyenne (%)")
    avg_growth_rate: float = Field(..., description="Taux de croissance moyen (%)")
    best_month: str = Field(..., description="Mois le plus rentable (YYYY-MM)")
    worst_month: str = Field(..., description="Mois le moins rentable (YYYY-MM)")
    trend: str = Field(..., description="Tendance : hausse | baisse | stable")
    revenue_volatility: float = Field(..., description="\u00c9cart-type du CA (TND)")


class MarketingKPIs(BaseModel):
    """KPIs marketing calcul\u00e9s par l'analyse."""

    total_budget_spent: float = Field(..., description="Budget total d\u00e9pens\u00e9 (TND)")
    total_conversions: int = Field(..., description="Nombre total de conversions")
    avg_conversion_rate: float = Field(..., description="Taux de conversion moyen (%)")
    best_channel: str = Field(..., description="Canal avec le meilleur ROI")
    roi_by_channel: Dict[str, float] = Field(..., description="ROI par canal (%)")
    cost_per_conversion: float = Field(..., description="Co\u00fbt par conversion (TND)")
    top_campaign: str = Field(..., description="Campagne la plus performante")


class SupportKPIs(BaseModel):
    """KPIs support client calcul\u00e9s par l'analyse."""

    avg_satisfaction: float = Field(..., description="Score satisfaction moyen (1-5)")
    avg_resolution_hours: float = Field(..., description="Temps r\u00e9solution moyen (h)")
    high_churn_rate: float = Field(..., description="% tickets churn risk \u00e9lev\u00e9")
    top_issue_type: str = Field(..., description="Type de probl\u00e8me le plus fr\u00e9quent")
    sla_compliance: float = Field(..., description="% tickets r\u00e9solus < 24h")
    satisfaction_trend: str = Field(..., description="Tendance satisfaction")


class AllKPIs(BaseModel):
    """Tous les KPIs regroup\u00e9s par domaine."""

    finance: Optional[FinanceKPIs] = None
    marketing: Optional[MarketingKPIs] = None
    support: Optional[SupportKPIs] = None


# ============================================================
# Anomalies
# ============================================================

class Anomaly(BaseModel):
    """Une anomalie d\u00e9tect\u00e9e dans les donn\u00e9es."""

    dataset: str = Field(..., description="Nom du dataset (finance, marketing, support)")
    colonne: str = Field(..., description="Nom de la colonne concern\u00e9e")
    index: int = Field(..., description="Index de la ligne dans le dataset")
    valeur: float = Field(..., description="Valeur aberrante d\u00e9tect\u00e9e")
    type: str = Field(..., description="Type d'anomalie : high | low")


# ============================================================
# R\u00e9ponses des routes
# ============================================================

class AnalyzeResponse(BaseModel):
    """R\u00e9ponse de la route POST /analyze."""

    success: bool = Field(..., description="Succ\u00e8s de l'analyse")
    kpis: Dict[str, Any] = Field(default_factory=dict, description="KPIs par domaine")
    anomalies: List[Anomaly] = Field(default_factory=list, description="Anomalies d\u00e9tect\u00e9es")
    errors: List[str] = Field(default_factory=list, description="Erreurs non bloquantes")
    message: str = Field(default="", description="Message descriptif")


class HealthResponse(BaseModel):
    """R\u00e9ponse de la route GET /health."""

    status: str = Field(..., description="Statut de l'API : ok | degraded | error")
    api: bool = Field(..., description="API FastAPI op\u00e9rationnelle")
    ollama: bool = Field(..., description="Serveur Ollama accessible")
    message: str = Field(default="", description="Message descriptif")


class UploadResponse(BaseModel):
    """R\u00e9ponse de la route POST /upload."""

    success: bool = Field(..., description="Succ\u00e8s de l'upload")
    filename: str = Field(..., description="Nom du fichier upload\u00e9")
    file_type: Optional[str] = Field(None, description="Type de fichier d\u00e9tect\u00e9")
    columns: List[str] = Field(default_factory=list, description="Colonnes d\u00e9tect\u00e9es")
    row_count: int = Field(default=0, description="Nombre de lignes dans le fichier")
    validation_errors: List[str] = Field(default_factory=list, description="Erreurs de validation non bloquantes")
    dataset_type: Optional[str] = Field(None, description="Alias legacy de file_type")
    rows: int = Field(default=0, description="Alias legacy de row_count")
    message: str = Field(default="", description="Message descriptif")


class ReportResponse(BaseModel):
    """R\u00e9ponse de la route GET /report."""

    success: bool = Field(..., description="Succ\u00e8s de la r\u00e9cup\u00e9ration")
    report: Dict[str, Any] = Field(default_factory=dict, description="Rapport complet")
    generated_at: Optional[str] = Field(None, description="Date de g\u00e9n\u00e9ration ISO")
    message: str = Field(default="", description="Message descriptif")
