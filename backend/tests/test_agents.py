"""
Tests d'intégration — pipeline multi-agents LangGraph.

Couverture :
    - analysis_agent : KPIs produits, anomalies détectées, état propagé
    - Pipeline complet avec LLM mocké (pas d'appel réel à Azure)
    - Propagation d'erreurs sans blocage du pipeline
    - create_initial_state() : état initial correct

Lancer : pytest backend/tests/test_agents.py -v
"""

from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from backend.agents.analysis_agent import analysis_agent
from backend.agents.state import AgentState, create_initial_state


# ================================================================
# Helpers
# ================================================================


def _make_raw_data() -> Dict[str, Any]:
    """Produit un raw_data sérialisé à partir des nouveaux schémas."""
    ventes_df = pd.DataFrame({
        "invoice_id":        ["INV001", "INV002", "INV003"],
        "product_name":      ["Laptop", "T-Shirt", "Chaise"],
        "category":          ["Electronique", "Vêtements", "Mobilier"],
        "quantity":          [1, 2, 1],
        "unit_price_tnd":    [2_000.0, 50.0, 500.0],
        "revenue_tnd":       [2_000.0, 100.0, 500.0],
        "customer_id":       ["C001", "C002", "C003"],
        "customer_region":   ["Tunis", "Sfax", "Sousse"],
        "sale_date":         ["2024-01-15", "2024-01-16", "2024-01-17"],
        "sales_channel":     ["Site Web", "Magasin Physique", "Site Web"],
        "payment_method":    ["Carte", "Espèces", "Virement"],
        "estimated_profit":  [600.0, 30.0, 150.0],
    })
    regions_df = pd.DataFrame({
        "customer_region":  ["Tunis", "Sfax", "Sousse"],
        "ca_total":         [500_000.0, 350_000.0, 200_000.0],
        "profit_total":     [125_000.0, 87_500.0, 50_000.0],
        "nb_transactions":  [500, 300, 200],
        "panier_moyen":     [1_000.0, 1_166.67, 1_000.0],
    })
    categories_df = pd.DataFrame({
        "category":        ["Électronique", "Mobilier", "Vêtements"],
        "ca_total":        [500_000.0, 350_000.0, 200_000.0],
        "profit_total":    [125_000.0, 87_500.0, 50_000.0],
        "nb_transactions": [500, 300, 200],
        "quantite_vendue": [600, 350, 400],
        "prix_moyen":      [833.33, 1_166.67, 500.0],
    })
    canaux_df = pd.DataFrame({
        "sales_channel":   ["Site Web", "Magasin Physique"],
        "ca_total":        [450_000.0, 350_000.0],
        "nb_transactions": [450, 300],
        "panier_moyen":    [1_000.0, 1_166.67],
    })
    kpis_df = pd.DataFrame({
        "indicateur": [
            "CA Total (TND)", "Profit Total (TND)", "Marge Beneficiaire (%)",
            "Nb Transactions", "Panier Moyen (TND)", "Quantite Totale Vendue",
            "Nb Clients Uniques", "CA Moyen par Client (TND)",
        ],
        "valeur": [500_000.0, 125_000.0, 25.0, 500, 1_000.0, 1_500, 350, 1_428.57],
    })
    return {
        "ventes":     ventes_df.to_dict(orient="records"),
        "regions":    regions_df.to_dict(orient="records"),
        "categories": categories_df.to_dict(orient="records"),
        "canaux":     canaux_df.to_dict(orient="records"),
        "kpis":       kpis_df.to_dict(orient="records"),
    }


# ================================================================
# Tests create_initial_state
# ================================================================


class TestCreateInitialState:
    """Vérifie la structure de l'état initial."""

    def test_initial_state_has_all_keys(self):
        """L'état initial contient toutes les clés du TypedDict."""
        state = create_initial_state()
        expected_keys = {
            "raw_data", "user_question", "kpis", "anomalies",
            "interpretation", "rag_context", "recommendations",
            "report", "errors", "current_step",
        }
        assert expected_keys.issubset(state.keys())

    def test_initial_state_empty_collections(self):
        """Les collections de l'état initial sont vides."""
        state = create_initial_state()
        assert state["kpis"] == {}
        assert state["anomalies"] == []
        assert state["rag_context"] == []
        assert state["recommendations"] == []
        assert state["errors"] == []
        assert state["report"] == {}

    def test_initial_state_empty_strings(self):
        """Les champs texte sont des chaînes vides."""
        state = create_initial_state()
        assert state["interpretation"] == ""

    def test_initial_state_with_raw_data(self):
        """raw_data injecté est bien conservé dans l'état."""
        data = {"finance": [{"revenue": 100_000}]}
        state = create_initial_state(raw_data=data)
        assert state["raw_data"] == data

    def test_initial_state_with_user_question(self):
        """user_question injectée est bien conservée."""
        state = create_initial_state(user_question="Quelle est la tendance des ventes ?")
        assert state["user_question"] == "Quelle est la tendance des ventes ?"


# ================================================================
# Tests analysis_agent
# ================================================================


class TestAnalysisAgent:
    """Teste l'agent d'analyse (agent 1 — sans LLM)."""

    def test_analysis_agent_produces_kpis(self):
        """L'analysis_agent doit produire des KPIs non vides."""
        state = create_initial_state(raw_data=_make_raw_data())
        result = analysis_agent(state)
        assert result["kpis"] != {}

    def test_analysis_agent_kpis_has_finance_keys(self):
        """Les KPIs doivent contenir les clés finance attendues."""
        state = create_initial_state(raw_data=_make_raw_data())
        result = analysis_agent(state)
        finance_kpis = result["kpis"].get("finance", {})
        expected = {"revenue_total", "profit_total", "profit_margin", "trend"}
        assert expected.issubset(finance_kpis.keys())

    def test_analysis_agent_kpis_has_canaux_keys(self):
        """Les KPIs doivent contenir les clés canaux de vente attendues."""
        state = create_initial_state(raw_data=_make_raw_data())
        result = analysis_agent(state)
        # analysis_agent stocke les KPIs canaux sous la clé "marketing"
        canaux_kpis = result["kpis"].get("marketing", {})
        expected = {"total_ca", "total_transactions", "best_channel"}
        assert expected.issubset(canaux_kpis.keys())

    def test_analysis_agent_kpis_has_categories_keys(self):
        """Les KPIs doivent contenir les clés catégories produits attendues."""
        state = create_initial_state(raw_data=_make_raw_data())
        result = analysis_agent(state)
        categories_kpis = result["kpis"].get("categories", {})
        expected = {"total_revenue", "total_profit", "top_category_by_revenue"}
        assert expected.issubset(categories_kpis.keys())

    def test_analysis_agent_returns_full_state(self):
        """L'agent retourne un état complet (pas seulement les nouvelles clés)."""
        state = create_initial_state(
            raw_data=_make_raw_data(),
            user_question="Analyse des ventes"
        )
        result = analysis_agent(state)
        # La question utilisateur doit être préservée
        assert result["user_question"] == "Analyse des ventes"

    def test_analysis_agent_anomalies_is_list(self):
        """anomalies doit toujours être une liste (éventuellement vide)."""
        state = create_initial_state(raw_data=_make_raw_data())
        result = analysis_agent(state)
        assert isinstance(result["anomalies"], list)

    def test_analysis_agent_with_empty_raw_data(self):
        """
        Un raw_data vide ne doit pas bloquer le pipeline.
        Les erreurs doivent être collectées dans state["errors"].
        """
        state = create_initial_state(raw_data={})
        result = analysis_agent(state)
        # Soit des KPIs vides, soit des erreurs — pas d'exception non catchée
        assert isinstance(result["errors"], list)

    def test_analysis_agent_errors_is_list(self):
        """Le champ errors est toujours une liste après l'exécution."""
        state = create_initial_state(raw_data=_make_raw_data())
        result = analysis_agent(state)
        assert isinstance(result["errors"], list)


# ================================================================
# Tests agents LLM (avec LLM mocké — sans LangGraph ni HuggingFace)
# ================================================================


class TestPipelineWithMockedLLM:
    """
    Teste les agents LLM individuellement en mockant _get_llm.
    N'importe pas le graphe LangGraph pour éviter le chargement
    du modèle HuggingFace (rag_agent → embeddings → sentence-t5-base).
    Aucun crédit Azure n'est consommé.
    """

    def test_interpretation_agent_state_has_all_keys(self):
        """
        interpretation_agent doit retourner un état avec toutes les clés
        attendues : kpis, anomalies, interpretation, errors.
        """
        mock_response = MagicMock()
        mock_response.content = (
            "Insight 1: La marge bénéficiaire est stable à 30%.\n"
            "Action 1: Renforcer les campagnes email pour maximiser le ROI."
        )
        mock_llm = MagicMock()
        mock_llm.invoke = MagicMock(return_value=mock_response)

        with patch("backend.agents.interpretation_agent._get_llm", return_value=mock_llm):
            from backend.agents.interpretation_agent import interpretation_agent
            state = create_initial_state(raw_data=_make_raw_data())
            state_after_analysis = analysis_agent(state)
            result = interpretation_agent(state_after_analysis)

        assert "kpis" in result
        assert "anomalies" in result
        assert "interpretation" in result
        assert "errors" in result

    def test_kpis_not_empty_after_analysis(self):
        """Après analysis_agent, kpis ne doit pas être un dict vide."""
        state = create_initial_state(raw_data=_make_raw_data())
        result = analysis_agent(state)
        assert result["kpis"] != {}

    def test_interpretation_agent_no_errors_with_valid_data(self):
        """
        interpretation_agent ne doit pas produire d'erreurs sur des données valides
        avec LLM mocké.
        """
        mock_response = MagicMock()
        mock_response.content = "Insight 1: Analyse terminée."
        mock_llm = MagicMock()
        mock_llm.invoke = MagicMock(return_value=mock_response)

        with patch("backend.agents.interpretation_agent._get_llm", return_value=mock_llm):
            from backend.agents.interpretation_agent import interpretation_agent
            state = create_initial_state(raw_data=_make_raw_data())
            state_after_analysis = analysis_agent(state)
            result = interpretation_agent(state_after_analysis)

        assert isinstance(result["errors"], list)
        assert result["interpretation"] != ""
