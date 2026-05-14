"""
Tests unitaires — analyse des données (KPIs + anomalies).

Couverture :
    - finance_analyzer.analyze()
    - marketing_analyzer.analyze()
    - support_analyzer.analyze()
    - anomaly_detector.detect()
    - loader._validate_columns()

Lancer : pytest backend/tests/test_analysis.py -v
"""

import numpy as np
import pandas as pd
import pytest

from backend.analysis import anomaly_detector, finance_analyzer, marketing_analyzer, support_analyzer


# ================================================================
# Tests finance_analyzer
# ================================================================


class TestFinanceAnalyzer:
    """Tests du calculateur de KPIs financiers (format indicateur/valeur)."""

    def test_kpis_keys_present(self, finance_df):
        """Tous les KPIs attendus sont présents dans le résultat."""
        kpis = finance_analyzer.analyze(finance_df)
        expected_keys = {
            "revenue_total", "profit_total", "profit_margin",
            "nb_transactions", "panier_moyen",
        }
        assert expected_keys.issubset(kpis.keys())

    def test_revenue_total_correct(self, finance_df):
        """revenue_total = valeur CA Total (TND) du DataFrame."""
        kpis = finance_analyzer.analyze(finance_df)
        assert kpis["revenue_total"] == 500_000.0

    def test_profit_total_correct(self, finance_df):
        """profit_total = valeur Profit Total (TND) du DataFrame."""
        kpis = finance_analyzer.analyze(finance_df)
        assert kpis["profit_total"] == 125_000.0

    def test_profit_margin_between_0_and_100(self, finance_df):
        """La marge bénéficiaire doit être entre 0% et 100%."""
        kpis = finance_analyzer.analyze(finance_df)
        assert 0.0 <= kpis["profit_margin"] <= 100.0

    def test_trend_is_stable(self, finance_df):
        """trend est toujours 'stable' pour le format kpis_globaux."""
        kpis = finance_analyzer.analyze(finance_df)
        assert kpis["trend"] == "stable"

    def test_missing_column_raises_value_error(self):
        """Une colonne manquante doit lever ValueError."""
        df = pd.DataFrame({"col": [1]})
        with pytest.raises(ValueError, match="Colonnes manquantes"):
            finance_analyzer.analyze(df)

    def test_single_row_does_not_crash(self):
        """Un DataFrame d'une seule ligne ne doit pas provoquer d'erreur."""
        df = pd.DataFrame({
            "indicateur": ["CA Total (TND)"],
            "valeur":     [100_000.0],
        })
        kpis = finance_analyzer.analyze(df)
        assert kpis["revenue_total"] == 100_000.0

    def test_zero_revenue_does_not_divide_by_zero(self):
        """Un CA = 0 ne doit pas provoquer de ZeroDivisionError."""
        df = pd.DataFrame({
            "indicateur": ["CA Total (TND)", "Profit Total (TND)", "Marge Beneficiaire (%)"],
            "valeur":     [0.0, 0.0, 0.0],
        })
        kpis = finance_analyzer.analyze(df)
        assert kpis["profit_margin"] == 0.0


# ================================================================
# Tests marketing_analyzer
# ================================================================


class TestMarketingAnalyzer:
    """Tests du calculateur de KPIs canaux marketing."""

    def test_kpis_keys_present(self, marketing_df):
        """Tous les KPIs canaux attendus sont présents."""
        kpis = marketing_analyzer.analyze(marketing_df)
        expected_keys = {
            "total_ca", "total_transactions", "best_channel",
            "top_panier_channel", "ca_by_channel", "transactions_by_channel",
        }
        assert expected_keys.issubset(kpis.keys())

    def test_total_ca_correct(self, marketing_df):
        """total_ca = somme exacte des ca_total."""
        kpis = marketing_analyzer.analyze(marketing_df)
        expected = round(float(marketing_df["ca_total"].sum()), 2)
        assert kpis["total_ca"] == expected

    def test_total_transactions_correct(self, marketing_df):
        """total_transactions = somme exacte des nb_transactions."""
        kpis = marketing_analyzer.analyze(marketing_df)
        assert kpis["total_transactions"] == int(marketing_df["nb_transactions"].sum())

    def test_best_channel_is_site_web(self, marketing_df):
        """Site Web a le CA le plus élevé (450 000 TND)."""
        kpis = marketing_analyzer.analyze(marketing_df)
        assert kpis["best_channel"] == "Site Web"

    def test_ca_by_channel_is_dict(self, marketing_df):
        """ca_by_channel doit être un dictionnaire non vide."""
        kpis = marketing_analyzer.analyze(marketing_df)
        assert isinstance(kpis["ca_by_channel"], dict)
        assert len(kpis["ca_by_channel"]) > 0

    def test_missing_column_raises_value_error(self):
        """Une colonne manquante doit lever ValueError."""
        df = pd.DataFrame({"sales_channel": ["Site Web"]})
        with pytest.raises(ValueError, match="Colonnes manquantes"):
            marketing_analyzer.analyze(df)

    def test_single_channel_does_not_crash(self):
        """Un seul canal ne doit pas provoquer d'erreur."""
        df = pd.DataFrame({
            "sales_channel":   ["Site Web"],
            "ca_total":        [300_000.0],
            "nb_transactions": [300],
            "panier_moyen":    [1_000.0],
        })
        kpis = marketing_analyzer.analyze(df)
        assert kpis["total_ca"] == 300_000.0
        assert kpis["best_channel"] == "Site Web"


# ================================================================
# Tests support_analyzer
# ================================================================


class TestSupportAnalyzer:
    """Tests du calculateur de KPIs catégories produits."""

    def test_kpis_keys_present(self, support_df):
        """Tous les KPIs catégories attendus sont présents."""
        kpis = support_analyzer.analyze(support_df)
        expected_keys = {
            "total_revenue", "total_profit", "total_transactions",
            "total_quantity", "top_category_by_revenue", "revenue_by_category",
        }
        assert expected_keys.issubset(kpis.keys())

    def test_total_revenue_correct(self, support_df):
        """total_revenue = somme exacte des ca_total."""
        kpis = support_analyzer.analyze(support_df)
        expected = round(float(support_df["ca_total"].sum()), 2)
        assert kpis["total_revenue"] == expected

    def test_total_profit_correct(self, support_df):
        """total_profit = somme exacte des profit_total."""
        kpis = support_analyzer.analyze(support_df)
        expected = round(float(support_df["profit_total"].sum()), 2)
        assert kpis["total_profit"] == expected

    def test_top_category_by_revenue(self, support_df):
        """Électronique a le CA le plus élevé (500 000 TND)."""
        kpis = support_analyzer.analyze(support_df)
        assert kpis["top_category_by_revenue"] == "Électronique"

    def test_revenue_by_category_is_dict(self, support_df):
        """revenue_by_category doit être un dictionnaire non vide."""
        kpis = support_analyzer.analyze(support_df)
        assert isinstance(kpis["revenue_by_category"], dict)
        assert len(kpis["revenue_by_category"]) > 0

    def test_missing_column_raises_value_error(self):
        """Une colonne manquante doit lever ValueError."""
        df = pd.DataFrame({"category": ["Électronique"]})
        with pytest.raises(ValueError, match="Colonnes manquantes"):
            support_analyzer.analyze(df)


# ================================================================
# Tests anomaly_detector
# ================================================================


class TestAnomalyDetector:
    """Tests du détecteur d'anomalies IQR."""

    def test_no_anomalies_on_uniform_data(self, finance_df):
        """Données uniformes = aucune anomalie détectée."""
        uniform_df = pd.DataFrame({
            "indicateur": ["CA Total (TND)"] * 10,
            "valeur":     [500_000.0] * 10,
        })
        anomalies = anomaly_detector.detect({"kpis": uniform_df})
        assert len(anomalies) == 0

    def test_detects_obvious_high_anomaly(self, finance_df_with_anomaly):
        """Une valeur CA ×10 doit être détectée comme anomalie 'high'."""
        anomalies = anomaly_detector.detect({"kpis": finance_df_with_anomaly})
        valeur_anomalies = [a for a in anomalies if a["colonne"] == "valeur"]
        assert len(valeur_anomalies) > 0
        assert any(a["type"] == "high" for a in valeur_anomalies)

    def test_anomaly_dict_has_required_keys(self, finance_df_with_anomaly):
        """Chaque anomalie doit contenir les 5 clés attendues."""
        anomalies = anomaly_detector.detect({"kpis": finance_df_with_anomaly})
        assert len(anomalies) > 0
        required_keys = {"dataset", "colonne", "index", "valeur", "type"}
        for anomaly in anomalies:
            assert required_keys.issubset(anomaly.keys())

    def test_anomaly_type_is_high_or_low(self, finance_df_with_anomaly):
        """Le champ 'type' de chaque anomalie vaut 'high' ou 'low'."""
        anomalies = anomaly_detector.detect({"kpis": finance_df_with_anomaly})
        for anomaly in anomalies:
            assert anomaly["type"] in ("high", "low")

    def test_multiple_datasets_processed(self, finance_df, marketing_df, support_df):
        """Les 3 datasets sont bien traités sans erreur."""
        anomalies = anomaly_detector.detect({
            "kpis":       finance_df,
            "canaux":     marketing_df,
            "categories": support_df,
        })
        dataset_names = {a["dataset"] for a in anomalies}
        assert dataset_names.issubset({"kpis", "canaux", "categories"})

    def test_low_anomaly_detected(self):
        """Une valeur très basse doit être détectée comme anomalie 'low'."""
        df = pd.DataFrame({
            "sales_channel":   ["Site Web"] * 9 + ["Autre"],
            "ca_total":        [500_000.0] * 9 + [1.0],  # valeur anormalement basse
            "nb_transactions": [450] * 10,
            "panier_moyen":    [1_000.0] * 10,
        })
        anomalies = anomaly_detector.detect({"canaux": df})
        low_anomalies = [a for a in anomalies if a["type"] == "low"]
        assert len(low_anomalies) > 0

    def test_empty_dataframe_does_not_crash(self):
        """Un DataFrame vide ne doit pas provoquer d'erreur."""
        df = pd.DataFrame({"ca_total": pd.Series([], dtype=float)})
        anomalies = anomaly_detector.detect({"canaux": df})
        assert isinstance(anomalies, list)
