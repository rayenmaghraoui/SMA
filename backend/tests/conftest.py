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
    """DataFrame kpis_globaux minimal pour les tests (format indicateur/valeur)."""
    return pd.DataFrame({
        "indicateur": [
            "CA Total (TND)", "Profit Total (TND)", "Marge Beneficiaire (%)",
            "Nb Transactions", "Panier Moyen (TND)", "Quantite Totale Vendue",
            "Nb Clients Uniques", "CA Moyen par Client (TND)",
        ],
        "valeur": [500_000.0, 125_000.0, 25.0, 500, 1_000.0, 1_500, 350, 1_428.57],
    })


@pytest.fixture
def marketing_df() -> pd.DataFrame:
    """DataFrame canaux marketing minimal pour les tests."""
    return pd.DataFrame({
        "sales_channel":   ["Site Web", "Magasin Physique", "Application Mobile", "Réseaux Sociaux"],
        "ca_total":        [450_000.0, 350_000.0, 200_000.0, 150_000.0],
        "nb_transactions": [450, 300, 200, 150],
        "panier_moyen":    [1_000.0, 1_166.67, 1_000.0, 1_000.0],
    })


@pytest.fixture
def support_df() -> pd.DataFrame:
    """DataFrame catégories produits minimal pour les tests."""
    return pd.DataFrame({
        "category":        ["Électronique", "Mobilier", "Vêtements"],
        "ca_total":        [500_000.0, 350_000.0, 200_000.0],
        "profit_total":    [125_000.0, 87_500.0, 50_000.0],
        "nb_transactions": [500, 300, 200],
        "quantite_vendue": [600, 350, 400],
        "prix_moyen":      [833.33, 1_166.67, 500.0],
    })


@pytest.fixture
def finance_df_with_anomaly(finance_df: pd.DataFrame) -> pd.DataFrame:
    """DataFrame kpis avec une valeur modifiée pour les tests d'anomalie."""
    df = finance_df.copy()
    # On double le CA pour créer un écart notable
    df.loc[df["indicateur"] == "CA Total (TND)", "valeur"] = 5_000_000.0
    return df
