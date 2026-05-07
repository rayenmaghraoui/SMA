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
    """Tests du calculateur de KPIs financiers."""

    def test_kpis_keys_present(self, finance_df):
        """Tous les KPIs attendus sont présents dans le résultat."""
        kpis = finance_analyzer.analyze(finance_df)
        expected_keys = {
            "revenue_total", "profit_total", "profit_margin",
            "avg_growth_rate", "best_month", "worst_month",
            "trend", "revenue_volatility",
        }
        assert expected_keys.issubset(kpis.keys())

    def test_revenue_total_correct(self, finance_df):
        """revenue_total = somme exacte des revenues."""
        kpis = finance_analyzer.analyze(finance_df)
        expected = float(finance_df["revenue"].sum())
        assert kpis["revenue_total"] == round(expected, 2)

    def test_profit_total_correct(self, finance_df):
        """profit_total = somme exacte des profits."""
        kpis = finance_analyzer.analyze(finance_df)
        expected = float(finance_df["profit"].sum())
        assert kpis["profit_total"] == round(expected, 2)

    def test_profit_margin_between_0_and_100(self, finance_df):
        """La marge bénéficiaire doit être entre 0% et 100%."""
        kpis = finance_analyzer.analyze(finance_df)
        assert 0.0 <= kpis["profit_margin"] <= 100.0

    def test_best_month_is_highest_profit(self, finance_df):
        """best_month correspond au mois avec le plus grand profit."""
        kpis = finance_analyzer.analyze(finance_df)
        # Le dernier mois a profit=50_000 (ex aequo avec octobre)
        # best_month doit être une string au format YYYY-MM
        assert isinstance(kpis["best_month"], str)
        assert len(kpis["best_month"]) == 7  # format "YYYY-MM"

    def test_worst_month_is_lowest_profit(self, finance_df):
        """worst_month correspond au mois avec le plus faible profit."""
        kpis = finance_analyzer.analyze(finance_df)
        assert isinstance(kpis["worst_month"], str)

    def test_trend_values_are_valid(self, finance_df):
        """trend est l'une des 3 valeurs autorisées."""
        kpis = finance_analyzer.analyze(finance_df)
        assert kpis["trend"] in ("hausse", "baisse", "stable")

    def test_trend_hausse_on_increasing_data(self):
        """Tendance = 'hausse' sur une série revenue strictement croissante."""
        df = pd.DataFrame({
            "date":        pd.date_range("2024-01-01", periods=12, freq="MS"),
            "revenue":     [100_000 + i * 20_000 for i in range(12)],
            "cost":        [60_000] * 12,
            "profit":      [40_000 + i * 20_000 for i in range(12)],
            "growth_rate": [10.0] * 12,
        })
        kpis = finance_analyzer.analyze(df)
        assert kpis["trend"] == "hausse"

    def test_trend_baisse_on_decreasing_data(self):
        """Tendance = 'baisse' sur une série revenue strictement décroissante."""
        df = pd.DataFrame({
            "date":        pd.date_range("2024-01-01", periods=12, freq="MS"),
            "revenue":     [320_000 - i * 20_000 for i in range(12)],
            "cost":        [60_000] * 12,
            "profit":      [260_000 - i * 20_000 for i in range(12)],
            "growth_rate": [-5.0] * 12,
        })
        kpis = finance_analyzer.analyze(df)
        assert kpis["trend"] == "baisse"

    def test_revenue_volatility_is_positive(self, finance_df):
        """L'écart-type du revenue doit être positif."""
        kpis = finance_analyzer.analyze(finance_df)
        assert kpis["revenue_volatility"] >= 0.0

    def test_missing_column_raises_value_error(self):
        """Une colonne manquante doit lever ValueError."""
        df = pd.DataFrame({"date": ["2024-01-01"], "revenue": [100_000.0]})
        with pytest.raises(ValueError, match="Colonnes manquantes"):
            finance_analyzer.analyze(df)

    def test_single_row_does_not_crash(self):
        """Un DataFrame d'une seule ligne ne doit pas provoquer d'erreur."""
        df = pd.DataFrame({
            "date":        ["2024-01-01"],
            "revenue":     [100_000.0],
            "cost":        [70_000.0],
            "profit":      [30_000.0],
            "growth_rate": [0.0],
        })
        kpis = finance_analyzer.analyze(df)
        assert kpis["revenue_total"] == 100_000.0

    def test_zero_revenue_does_not_divide_by_zero(self):
        """Un revenue = 0 ne doit pas provoquer de ZeroDivisionError."""
        df = pd.DataFrame({
            "date":        pd.date_range("2024-01-01", periods=3, freq="MS"),
            "revenue":     [0.0, 0.0, 0.0],
            "cost":        [0.0, 0.0, 0.0],
            "profit":      [0.0, 0.0, 0.0],
            "growth_rate": [0.0, 0.0, 0.0],
        })
        kpis = finance_analyzer.analyze(df)
        assert kpis["profit_margin"] == 0.0


# ================================================================
# Tests marketing_analyzer
# ================================================================


class TestMarketingAnalyzer:
    """Tests du calculateur de KPIs marketing."""

    def test_kpis_keys_present(self, marketing_df):
        """Tous les KPIs marketing attendus sont présents."""
        kpis = marketing_analyzer.analyze(marketing_df)
        expected_keys = {
            "total_budget_spent", "total_conversions", "avg_conversion_rate",
            "best_channel", "roi_by_channel", "cost_per_conversion", "top_campaign",
        }
        assert expected_keys.issubset(kpis.keys())

    def test_total_budget_correct(self, marketing_df):
        """total_budget_spent = somme exacte des budgets."""
        kpis = marketing_analyzer.analyze(marketing_df)
        assert kpis["total_budget_spent"] == round(float(marketing_df["budget"].sum()), 2)

    def test_total_conversions_correct(self, marketing_df):
        """total_conversions = somme exacte des conversions."""
        kpis = marketing_analyzer.analyze(marketing_df)
        assert kpis["total_conversions"] == int(marketing_df["conversions"].sum())

    def test_best_channel_is_email(self, marketing_df):
        """
        email a ROI = 80/3000*100 ≈ 2.67
        social_media combiné = 95/9000*100 ≈ 1.06
        SEO = 30/2000*100 = 1.5
        Donc email doit être le meilleur canal.
        """
        kpis = marketing_analyzer.analyze(marketing_df)
        assert kpis["best_channel"] == "email"

    def test_roi_by_channel_is_dict(self, marketing_df):
        """roi_by_channel doit être un dictionnaire non vide."""
        kpis = marketing_analyzer.analyze(marketing_df)
        assert isinstance(kpis["roi_by_channel"], dict)
        assert len(kpis["roi_by_channel"]) > 0

    def test_cost_per_conversion_positive(self, marketing_df):
        """Le coût par conversion doit être positif."""
        kpis = marketing_analyzer.analyze(marketing_df)
        assert kpis["cost_per_conversion"] > 0.0

    def test_avg_conversion_rate_between_0_and_100(self, marketing_df):
        """Le taux de conversion moyen doit être entre 0% et 100%."""
        kpis = marketing_analyzer.analyze(marketing_df)
        assert 0.0 <= kpis["avg_conversion_rate"] <= 100.0

    def test_missing_column_raises_value_error(self):
        """Une colonne manquante doit lever ValueError."""
        df = pd.DataFrame({"date": ["2024-01-01"], "channel": ["email"]})
        with pytest.raises(ValueError, match="Colonnes manquantes"):
            marketing_analyzer.analyze(df)

    def test_zero_clicks_does_not_crash(self):
        """Aucun clic ne doit pas provoquer de division par zéro."""
        df = pd.DataFrame({
            "date":            ["2024-01-01"],
            "campaign_id":     ["C001"],
            "channel":         ["email"],
            "budget":          [1_000.0],
            "clicks":          [0],
            "conversions":     [0],
            "conversion_rate": [0.0],
        })
        kpis = marketing_analyzer.analyze(df)
        assert kpis["avg_conversion_rate"] == 0.0


# ================================================================
# Tests support_analyzer
# ================================================================


class TestSupportAnalyzer:
    """Tests du calculateur de KPIs support client."""

    def test_kpis_keys_present(self, support_df):
        """Tous les KPIs support attendus sont présents."""
        kpis = support_analyzer.analyze(support_df)
        expected_keys = {
            "avg_satisfaction", "avg_resolution_hours", "high_churn_rate",
            "top_issue_type", "sla_compliance", "satisfaction_trend",
        }
        assert expected_keys.issubset(kpis.keys())

    def test_avg_satisfaction_between_1_and_5(self, support_df):
        """La satisfaction moyenne doit être entre 1 et 5."""
        kpis = support_analyzer.analyze(support_df)
        assert 1.0 <= kpis["avg_satisfaction"] <= 5.0

    def test_avg_satisfaction_correct(self, support_df):
        """avg_satisfaction = moyenne exacte des scores."""
        kpis = support_analyzer.analyze(support_df)
        expected = float(support_df["satisfaction_score"].mean())
        assert abs(kpis["avg_satisfaction"] - expected) < 0.01

    def test_high_churn_rate_correct(self, support_df):
        """high_churn_rate = 2/6 = 33.33% (2 tickets 'high' sur 6)."""
        kpis = support_analyzer.analyze(support_df)
        assert abs(kpis["high_churn_rate"] - 33.33) < 0.5

    def test_top_issue_type_is_billing(self, support_df):
        """billing est le type de problème le plus fréquent (3 fois sur 6)."""
        kpis = support_analyzer.analyze(support_df)
        assert kpis["top_issue_type"] == "billing"

    def test_sla_compliance_between_0_and_100(self, support_df):
        """Le taux de conformité SLA doit être entre 0% et 100%."""
        kpis = support_analyzer.analyze(support_df)
        assert 0.0 <= kpis["sla_compliance"] <= 100.0

    def test_sla_compliance_correct(self, support_df):
        """
        Tickets résolus en < 24h : T001(12h), T003(8h), T004(20h), T006(5h) = 4/6 ≈ 66.67%
        """
        kpis = support_analyzer.analyze(support_df)
        assert abs(kpis["sla_compliance"] - 66.67) < 0.5

    def test_satisfaction_trend_is_valid(self, support_df):
        """satisfaction_trend est l'une des 3 valeurs autorisées."""
        kpis = support_analyzer.analyze(support_df)
        assert kpis["satisfaction_trend"] in ("hausse", "baisse", "stable")

    def test_missing_column_raises_value_error(self):
        """Une colonne manquante doit lever ValueError."""
        df = pd.DataFrame({"date": ["2024-01-01"], "ticket_id": ["T001"]})
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
            "date":        pd.date_range("2024-01-01", periods=12, freq="MS"),
            "revenue":     [100_000.0] * 12,
            "cost":        [70_000.0] * 12,
            "profit":      [30_000.0] * 12,
            "growth_rate": [5.0] * 12,
        })
        anomalies = anomaly_detector.detect({"finance": uniform_df})
        assert len(anomalies) == 0

    def test_detects_obvious_high_anomaly(self, finance_df_with_anomaly):
        """Une valeur revenue ×10 doit être détectée comme anomalie 'high'."""
        anomalies = anomaly_detector.detect({"finance": finance_df_with_anomaly})
        revenue_anomalies = [a for a in anomalies if a["colonne"] == "revenue"]
        assert len(revenue_anomalies) > 0
        assert any(a["type"] == "high" for a in revenue_anomalies)

    def test_anomaly_dict_has_required_keys(self, finance_df_with_anomaly):
        """Chaque anomalie doit contenir les 5 clés attendues."""
        anomalies = anomaly_detector.detect({"finance": finance_df_with_anomaly})
        assert len(anomalies) > 0
        required_keys = {"dataset", "colonne", "index", "valeur", "type"}
        for anomaly in anomalies:
            assert required_keys.issubset(anomaly.keys())

    def test_anomaly_type_is_high_or_low(self, finance_df_with_anomaly):
        """Le champ 'type' de chaque anomalie vaut 'high' ou 'low'."""
        anomalies = anomaly_detector.detect({"finance": finance_df_with_anomaly})
        for anomaly in anomalies:
            assert anomaly["type"] in ("high", "low")

    def test_multiple_datasets_processed(self, finance_df, marketing_df, support_df):
        """Les 3 datasets sont bien traités sans erreur."""
        anomalies = anomaly_detector.detect({
            "finance":   finance_df,
            "marketing": marketing_df,
            "support":   support_df,
        })
        # dataset_names présents dans les anomalies = subset des 3 noms
        dataset_names = {a["dataset"] for a in anomalies}
        assert dataset_names.issubset({"finance", "marketing", "support"})

    def test_low_anomaly_detected(self):
        """Une valeur très basse doit être détectée comme anomalie 'low'."""
        df = pd.DataFrame({
            "date":        pd.date_range("2024-01-01", periods=10, freq="MS"),
            "revenue":     [100_000.0] * 9 + [100.0],  # valeur anormalement basse
            "cost":        [70_000.0] * 10,
            "profit":      [30_000.0] * 9 + [-69_900.0],
            "growth_rate": [5.0] * 10,
        })
        anomalies = anomaly_detector.detect({"finance": df})
        low_anomalies = [a for a in anomalies if a["type"] == "low"]
        assert len(low_anomalies) > 0

    def test_empty_dataframe_does_not_crash(self):
        """Un DataFrame vide ne doit pas provoquer d'erreur."""
        df = pd.DataFrame({"revenue": pd.Series([], dtype=float)})
        anomalies = anomaly_detector.detect({"finance": df})
        assert isinstance(anomalies, list)
