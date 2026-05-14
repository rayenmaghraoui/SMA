"""Package analysis — chargement, validation et analyse des données."""

from backend.analysis import finance_analyzer as kpis_analyzer
from backend.analysis import marketing_analyzer as canaux_analyzer
from backend.analysis import support_analyzer as categories_analyzer
from backend.analysis import anomaly_detector

__all__ = [
    "kpis_analyzer",
    "canaux_analyzer",
    "categories_analyzer",
    "anomaly_detector",
]
