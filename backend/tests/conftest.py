"""
Fixtures partagées entre tous les fichiers de tests.

Usage : pytest backend/tests/ -v
"""

import pandas as pd
import pytest


# ============================================================
# Fixtures DataFrames
# ============================================================


@pytest.fixture
def finance_df() -> pd.DataFrame:
    """DataFrame finance minimal et cohérent pour les tests."""
    return pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=12, freq="MS"),
        "revenue": [100_000, 110_000, 90_000, 120_000, 115_000,
                    105_000, 130_000, 125_000, 95_000, 140_000, 135_000, 150_000],
        "cost":    [70_000,  75_000,  65_000,  80_000,  78_000,
                    72_000,  88_000,  85_000,  68_000,  90_000,  92_000, 100_000],
        "profit":  [30_000,  35_000,  25_000,  40_000,  37_000,
                    33_000,  42_000,  40_000,  27_000,  50_000,  43_000,  50_000],
        "growth_rate": [0.0, 10.0, -18.2, 33.3, -4.2,
                        -8.7, 23.8, -3.8, -24.0, 47.4, -3.6, 11.1],
    })


@pytest.fixture
def marketing_df() -> pd.DataFrame:
    """DataFrame marketing minimal pour les tests."""
    return pd.DataFrame({
        "date":            ["2024-01-01", "2024-01-01", "2024-02-01", "2024-02-01"],
        "campaign_id":     ["C001", "C002", "C003", "C004"],
        "channel":         ["social_media", "email", "SEO", "social_media"],
        "budget":          [5_000.0, 3_000.0, 2_000.0, 4_000.0],
        "clicks":          [1_000, 800, 600, 900],
        "conversions":     [50, 80, 30, 45],
        "conversion_rate": [5.0, 10.0, 5.0, 5.0],
    })


@pytest.fixture
def support_df() -> pd.DataFrame:
    """DataFrame support client minimal pour les tests."""
    return pd.DataFrame({
        "date":               pd.date_range("2024-01-01", periods=6, freq="W"),
        "ticket_id":          ["T001", "T002", "T003", "T004", "T005", "T006"],
        "issue_type":         ["billing", "technical", "billing", "shipping", "technical", "billing"],
        "resolution_hours":   [12.0, 36.0, 8.0, 20.0, 48.0, 5.0],
        "satisfaction_score": [4.0, 2.0, 5.0, 3.0, 1.0, 5.0],
        "churn_risk":         ["low", "high", "low", "medium", "high", "low"],
    })


@pytest.fixture
def finance_df_with_anomaly(finance_df: pd.DataFrame) -> pd.DataFrame:
    """DataFrame finance avec une anomalie revenue évidente (valeur ×10)."""
    df = finance_df.copy()
    df.loc[5, "revenue"] = 1_050_000.0  # anomalie haute × 10
    return df
