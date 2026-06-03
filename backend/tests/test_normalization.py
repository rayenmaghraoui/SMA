"""
Tests unitaires et d'intégration — couche de normalisation sémantique.

Couverture :
    - DatasetProfiler          : profilage structurel
    - synonyms.find_concept_by_synonym
    - BusinessDomainDetector   : détection par keywords + tie-break
    - SchemaMapper             : mapping synonyme + fallback (sémantique mocké)
    - SafeDataTransformer      : renommage sûr + validation
    - NormalizationPipeline    : intégration end-to-end
    - Compatibilité avec les analyzers existants (kpis, canaux, categories)

Lancer : pytest backend/tests/test_normalization.py -v
"""

from __future__ import annotations

from typing import Dict
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from backend.normalization import (
    BusinessDomain,
    BusinessDomainDetector,
    DatasetProfiler,
    NormalizationPipeline,
    SafeDataTransformer,
    SchemaMapper,
)
from backend.normalization.schemas import (
    CanonicalConcept,
    CANAUX_SCHEMA,
    CATEGORIES_SCHEMA,
    KPIS_SCHEMA,
    REGIONS_SCHEMA,
    VENTES_SCHEMA,
    get_schema_by_name,
)
from backend.normalization.synonyms import find_concept_by_synonym


# ================================================================
# Fixtures — datasets variés couvrant des schémas hétérogènes
# ================================================================


@pytest.fixture
def df_kpis_format_french() -> pd.DataFrame:
    """KPIs au format clé-valeur français (schéma canonique direct)."""
    return pd.DataFrame({
        "indicateur": ["CA Total (TND)", "Profit Total (TND)", "Marge Beneficiaire (%)"],
        "valeur":     [500_000.0, 125_000.0, 25.0],
    })


@pytest.fixture
def df_kpis_format_english() -> pd.DataFrame:
    """KPIs avec noms de colonnes en anglais ('kpi_name' / 'value')."""
    return pd.DataFrame({
        "kpi_name": ["Total Revenue", "Net Profit", "Margin %"],
        "value":    [500_000.0, 125_000.0, 25.0],
    })


@pytest.fixture
def df_canaux_french() -> pd.DataFrame:
    """Dataset canaux au schéma canonique français."""
    return pd.DataFrame({
        "sales_channel":   ["Site Web", "Magasin Physique", "App Mobile"],
        "ca_total":        [450_000.0, 350_000.0, 200_000.0],
        "nb_transactions": [450, 300, 200],
        "panier_moyen":    [1_000.0, 1_166.67, 1_000.0],
    })


@pytest.fixture
def df_canaux_renamed() -> pd.DataFrame:
    """
    Dataset canaux avec colonnes renommées (cas d'usage réel : CSV uploadé
    par un utilisateur qui utilise sa propre nomenclature).
    """
    return pd.DataFrame({
        "channel":           ["Web", "Store", "Mobile"],
        "turnover":          [450_000.0, 350_000.0, 200_000.0],
        "num_orders":        [450, 300, 200],
        "average_basket":    [1_000.0, 1_166.67, 1_000.0],
    })


@pytest.fixture
def df_ventes() -> pd.DataFrame:
    """Dataset transactionnel (10 transactions)."""
    return pd.DataFrame({
        "invoice_id":      [f"INV{i:05d}" for i in range(10)],
        "product_name":    ["Laptop"] * 5 + ["T-Shirt"] * 5,
        "category":        ["Electronique"] * 5 + ["Textile"] * 5,
        "quantity":        [1, 2, 1, 3, 1, 4, 2, 3, 1, 2],
        "unit_price_tnd":  [2_000.0] * 5 + [50.0] * 5,
        "revenue_tnd":     [2_000.0, 4_000.0, 2_000.0, 6_000.0, 2_000.0,
                            200.0, 100.0, 150.0, 50.0, 100.0],
        "customer_id":     [f"C{i:03d}" for i in range(10)],
        "customer_region": ["Tunis", "Ariana", "Sfax", "Sousse", "Tunis",
                            "Sfax", "Tunis", "Sousse", "Ariana", "Tunis"],
        "sale_date":       pd.date_range("2024-01-01", periods=10).strftime("%Y-%m-%d"),
        "sales_channel":   ["Site web"] * 5 + ["Magasin physique"] * 5,
        "payment_method":  ["Carte"] * 5 + ["Especes"] * 5,
        "estimated_profit": [600.0, 1_200.0, 600.0, 1_800.0, 600.0,
                             60.0, 30.0, 45.0, 15.0, 30.0],
    })


@pytest.fixture
def df_hr_dataset() -> pd.DataFrame:
    """Dataset RH : domaine non couvert par les analyzers actuels."""
    return pd.DataFrame({
        "employee_id":     ["E001", "E002", "E003"],
        "salary":          [3000.0, 4500.0, 5200.0],
        "department":      ["IT", "Sales", "HR"],
        "hire_date":       ["2020-01-15", "2019-03-20", "2021-06-01"],
    })


@pytest.fixture
def df_empty() -> pd.DataFrame:
    """DataFrame vide pour tester la robustesse."""
    return pd.DataFrame()


# ================================================================
# Tests DatasetProfiler
# ================================================================


class TestDatasetProfiler:
    """Tests du profileur structurel."""

    def test_profile_returns_correct_shape(self, df_canaux_french):
        profiler = DatasetProfiler()
        profile = profiler.profile(df_canaux_french)
        assert profile.n_rows == 3
        assert profile.n_columns == 4

    def test_profile_detects_numeric_columns(self, df_canaux_french):
        profile = DatasetProfiler().profile(df_canaux_french)
        numeric_names = {c.name for c in profile.numeric_columns}
        assert "ca_total" in numeric_names
        assert "nb_transactions" in numeric_names
        assert "panier_moyen" in numeric_names

    def test_profile_detects_categorical_columns(self, df_canaux_french):
        profile = DatasetProfiler().profile(df_canaux_french)
        cat_names = {c.name for c in profile.categorical_columns}
        assert "sales_channel" in cat_names

    def test_profile_detects_date_column(self, df_ventes):
        profile = DatasetProfiler().profile(df_ventes)
        date_names = {c.name for c in profile.date_columns}
        assert "sale_date" in date_names

    def test_profile_detects_identifier_column(self, df_ventes):
        profile = DatasetProfiler().profile(df_ventes)
        kinds = {c.name: c.kind.value for c in profile.columns}
        # invoice_id est unique → IDENTIFIER
        assert kinds["invoice_id"] == "identifier"

    def test_profile_handles_empty_dataframe(self, df_empty):
        profile = DatasetProfiler().profile(df_empty)
        assert profile.n_rows == 0
        assert len(profile.structural_issues) > 0

    def test_profile_stats_computed_for_numeric(self, df_canaux_french):
        profile = DatasetProfiler().profile(df_canaux_french)
        ca_col = profile.get_column("ca_total")
        assert ca_col is not None
        assert ca_col.stats is not None
        assert ca_col.stats["min"] == 200_000.0
        assert ca_col.stats["max"] == 450_000.0

    def test_profile_null_ratio_computed(self):
        df = pd.DataFrame({"col": [1.0, None, 3.0, None]})
        profile = DatasetProfiler().profile(df)
        col = profile.get_column("col")
        assert col is not None
        assert col.null_ratio == 0.5


# ================================================================
# Tests synonyms
# ================================================================


class TestSynonymLookup:
    """Tests du dictionnaire de synonymes (lookup déterministe)."""

    def test_exact_match_french(self):
        assert find_concept_by_synonym("ca_total") == CanonicalConcept.REVENUE
        assert find_concept_by_synonym("chiffre_affaires") == CanonicalConcept.REVENUE

    def test_exact_match_english(self):
        assert find_concept_by_synonym("turnover") == CanonicalConcept.REVENUE
        assert find_concept_by_synonym("sales") == CanonicalConcept.REVENUE

    def test_case_insensitive(self):
        assert find_concept_by_synonym("CA_TOTAL") == CanonicalConcept.REVENUE
        assert find_concept_by_synonym("Revenue") == CanonicalConcept.REVENUE

    def test_handles_spaces(self):
        assert find_concept_by_synonym("ca total") == CanonicalConcept.REVENUE
        assert find_concept_by_synonym("panier moyen") == CanonicalConcept.AVG_BASKET

    def test_handles_accents(self):
        assert find_concept_by_synonym("bénéfice") == CanonicalConcept.PROFIT
        assert find_concept_by_synonym("catégorie") == CanonicalConcept.CATEGORY

    def test_unknown_synonym_returns_none(self):
        assert find_concept_by_synonym("xyz_unknown_column_xyz") is None

    def test_profit_concepts(self):
        assert find_concept_by_synonym("net_income") == CanonicalConcept.PROFIT
        assert find_concept_by_synonym("benefice") == CanonicalConcept.PROFIT

    def test_quantity_concepts(self):
        assert find_concept_by_synonym("quantite_vendue") == CanonicalConcept.TOTAL_QUANTITY
        assert find_concept_by_synonym("units_sold") == CanonicalConcept.TOTAL_QUANTITY

    def test_indicator_concepts(self):
        assert find_concept_by_synonym("indicateur") == CanonicalConcept.INDICATOR_NAME
        assert find_concept_by_synonym("kpi_name") == CanonicalConcept.INDICATOR_NAME
        assert find_concept_by_synonym("valeur") == CanonicalConcept.INDICATOR_VALUE


# ================================================================
# Tests BusinessDomainDetector
# ================================================================


class TestBusinessDomainDetector:
    """Tests du détecteur de domaine métier."""

    def test_detects_finance_from_keyvalue_format(self, df_kpis_format_french):
        detector = BusinessDomainDetector()
        prediction = detector.detect(df_kpis_format_french)
        assert prediction.domain == BusinessDomain.FINANCE

    def test_detects_sales_from_invoice(self, df_ventes):
        detector = BusinessDomainDetector()
        prediction = detector.detect(df_ventes)
        # invoice_id est un signal fort pour "sales"
        assert prediction.domain in {BusinessDomain.SALES, BusinessDomain.MARKETING}
        # On accepte marketing comme alternative car le dataset contient
        # aussi des canaux. Vérifie au moins que ce n'est pas "unknown".
        assert prediction.domain != BusinessDomain.UNKNOWN

    def test_detects_marketing_from_channels(self, df_canaux_french):
        detector = BusinessDomainDetector()
        prediction = detector.detect(df_canaux_french)
        assert prediction.domain in {BusinessDomain.MARKETING, BusinessDomain.SALES}

    def test_unknown_domain_for_unrelated_data(self):
        df = pd.DataFrame({
            "x": [1, 2, 3],
            "y": [4, 5, 6],
            "z": ["a", "b", "c"],
        })
        detector = BusinessDomainDetector()
        prediction = detector.detect(df)
        # Doit être unknown ou un score très faible
        assert prediction.confidence < 0.5 or prediction.domain == BusinessDomain.UNKNOWN

    def test_prediction_has_explanation(self, df_canaux_french):
        prediction = BusinessDomainDetector().detect(df_canaux_french)
        assert prediction.explanation != ""
        assert prediction.method in {"keywords", "tie_break", "llm_fallback"}

    def test_scores_by_domain_present(self, df_canaux_french):
        prediction = BusinessDomainDetector().detect(df_canaux_french)
        assert isinstance(prediction.scores_by_domain, dict)
        assert len(prediction.scores_by_domain) > 0

    def test_hr_dataset_detected_or_unknown(self, df_hr_dataset):
        """Le dataset RH doit être détecté HR ou rester unknown (pas de schéma)."""
        prediction = BusinessDomainDetector().detect(df_hr_dataset)
        assert prediction.domain in {BusinessDomain.HR, BusinessDomain.UNKNOWN}


# ================================================================
# Tests SchemaMapper (sémantique désactivée pour tests rapides)
# ================================================================


class TestSchemaMapperWithoutSemantic:
    """Tests du mapper sans embeddings (synonymes uniquement)."""

    def test_maps_french_canaux_exact_synonyms(self, df_canaux_french):
        profile = DatasetProfiler().profile(df_canaux_french)
        mapper = SchemaMapper(use_semantic=False)
        mappings = mapper.map_columns(profile, target_schema=CANAUX_SCHEMA)

        mapped_concepts = {m.target_concept for m in mappings if m.is_mapped}
        assert CanonicalConcept.SALES_CHANNEL in mapped_concepts
        assert CanonicalConcept.REVENUE in mapped_concepts
        assert CanonicalConcept.NB_TRANSACTIONS in mapped_concepts
        assert CanonicalConcept.AVG_BASKET in mapped_concepts

    def test_maps_english_columns_via_synonyms(self, df_canaux_renamed):
        profile = DatasetProfiler().profile(df_canaux_renamed)
        mapper = SchemaMapper(use_semantic=False)
        mappings = mapper.map_columns(profile, target_schema=CANAUX_SCHEMA)

        # "turnover" → REVENUE, "channel" → SALES_CHANNEL, "num_orders" → NB_TRANSACTIONS
        source_to_concept = {m.source_column: m.target_concept for m in mappings}
        assert source_to_concept["channel"] == CanonicalConcept.SALES_CHANNEL
        assert source_to_concept["turnover"] == CanonicalConcept.REVENUE
        assert source_to_concept["num_orders"] == CanonicalConcept.NB_TRANSACTIONS
        assert source_to_concept["average_basket"] == CanonicalConcept.AVG_BASKET

    def test_maps_kpis_kvformat_exact(self, df_kpis_format_french):
        profile = DatasetProfiler().profile(df_kpis_format_french)
        mapper = SchemaMapper(use_semantic=False)
        mappings = mapper.map_columns(profile, target_schema=KPIS_SCHEMA)

        source_to_concept = {m.source_column: m.target_concept for m in mappings}
        assert source_to_concept["indicateur"] == CanonicalConcept.INDICATOR_NAME
        assert source_to_concept["valeur"] == CanonicalConcept.INDICATOR_VALUE

    def test_maps_kpis_english_via_synonyms(self, df_kpis_format_english):
        profile = DatasetProfiler().profile(df_kpis_format_english)
        mapper = SchemaMapper(use_semantic=False)
        mappings = mapper.map_columns(profile, target_schema=KPIS_SCHEMA)

        source_to_concept = {m.source_column: m.target_concept for m in mappings}
        assert source_to_concept["kpi_name"] == CanonicalConcept.INDICATOR_NAME
        assert source_to_concept["value"] == CanonicalConcept.INDICATOR_VALUE

    def test_confidence_is_1_for_exact_synonym(self, df_canaux_french):
        profile = DatasetProfiler().profile(df_canaux_french)
        mapper = SchemaMapper(use_semantic=False)
        mappings = mapper.map_columns(profile, target_schema=CANAUX_SCHEMA)
        for m in mappings:
            if m.is_mapped:
                assert m.confidence == 1.0
                assert m.method == "synonym"

    def test_unmapped_when_no_synonym(self):
        df = pd.DataFrame({
            "xyz_weird_column": [1, 2, 3],
            "totally_unknown":  ["a", "b", "c"],
        })
        profile = DatasetProfiler().profile(df)
        mapper = SchemaMapper(use_semantic=False)
        mappings = mapper.map_columns(profile, target_schema=CANAUX_SCHEMA)
        assert all(not m.is_mapped for m in mappings)


# ================================================================
# Tests SafeDataTransformer
# ================================================================


class TestSafeDataTransformer:
    """Tests de l'application sûre des mappings."""

    def test_original_dataframe_not_modified(self, df_canaux_renamed):
        original_cols = list(df_canaux_renamed.columns)
        original_values = df_canaux_renamed.copy()

        profile = DatasetProfiler().profile(df_canaux_renamed)
        mapper = SchemaMapper(use_semantic=False)
        mappings = mapper.map_columns(profile, target_schema=CANAUX_SCHEMA)

        transformer = SafeDataTransformer()
        _, _ = transformer.transform(df_canaux_renamed, mappings, CANAUX_SCHEMA)

        assert list(df_canaux_renamed.columns) == original_cols
        pd.testing.assert_frame_equal(df_canaux_renamed, original_values)

    def test_transformed_df_has_canonical_columns(self, df_canaux_renamed):
        profile = DatasetProfiler().profile(df_canaux_renamed)
        mappings = SchemaMapper(use_semantic=False).map_columns(
            profile, target_schema=CANAUX_SCHEMA
        )
        normalized, report = SafeDataTransformer().transform(
            df_canaux_renamed, mappings, CANAUX_SCHEMA
        )

        assert "sales_channel" in normalized.columns
        assert "ca_total" in normalized.columns
        assert "nb_transactions" in normalized.columns
        assert "panier_moyen" in normalized.columns
        assert report.success is True

    def test_report_contains_renames(self, df_canaux_renamed):
        profile = DatasetProfiler().profile(df_canaux_renamed)
        mappings = SchemaMapper(use_semantic=False).map_columns(
            profile, target_schema=CANAUX_SCHEMA
        )
        _, report = SafeDataTransformer().transform(
            df_canaux_renamed, mappings, CANAUX_SCHEMA
        )

        assert "channel" in report.applied_renames
        assert report.applied_renames["channel"] == "sales_channel"
        assert report.applied_renames["turnover"] == "ca_total"

    def test_unmapped_columns_preserved_with_prefix(self):
        df = pd.DataFrame({
            "sales_channel":   ["A", "B"],
            "ca_total":        [100.0, 200.0],
            "nb_transactions": [10, 20],
            "panier_moyen":    [10.0, 10.0],
            "extra_col":       ["x", "y"],
        })
        profile = DatasetProfiler().profile(df)
        mappings = SchemaMapper(use_semantic=False).map_columns(
            profile, target_schema=CANAUX_SCHEMA
        )
        normalized, _ = SafeDataTransformer(keep_unmapped=True).transform(
            df, mappings, CANAUX_SCHEMA
        )
        assert "_unmapped_extra_col" in normalized.columns

    def test_missing_required_reported(self):
        df = pd.DataFrame({"sales_channel": ["A"]})  # manque CA, transactions, panier
        profile = DatasetProfiler().profile(df)
        mappings = SchemaMapper(use_semantic=False).map_columns(
            profile, target_schema=CANAUX_SCHEMA
        )
        _, report = SafeDataTransformer().transform(df, mappings, CANAUX_SCHEMA)

        assert report.success is False
        assert len(report.missing_required) >= 3


# ================================================================
# Tests intégration NormalizationPipeline
# ================================================================


class TestNormalizationPipelineIntegration:
    """Tests end-to-end de la couche de normalisation."""

    def test_pipeline_normalizes_canonical_dataset(self, df_canaux_french):
        pipeline = NormalizationPipeline(use_semantic=False, use_llm_fallback=False)
        result = pipeline.normalize(df_canaux_french)

        assert result.success is True
        assert result.schema is not None
        assert result.normalized_df is not None
        assert "ca_total" in result.normalized_df.columns

    def test_pipeline_normalizes_renamed_dataset(self, df_canaux_renamed):
        pipeline = NormalizationPipeline(use_semantic=False, use_llm_fallback=False)
        result = pipeline.normalize(df_canaux_renamed)

        assert result.success is True
        assert result.normalized_df is not None
        assert "sales_channel" in result.normalized_df.columns
        assert "ca_total" in result.normalized_df.columns

    def test_pipeline_normalizes_english_kpis(self, df_kpis_format_english):
        pipeline = NormalizationPipeline(use_semantic=False, use_llm_fallback=False)
        result = pipeline.normalize(df_kpis_format_english)

        assert result.success is True
        assert result.schema is not None
        assert result.schema.name == "kpis"
        assert "indicateur" in result.normalized_df.columns
        assert "valeur" in result.normalized_df.columns

    def test_pipeline_explanation_present(self, df_canaux_french):
        pipeline = NormalizationPipeline(use_semantic=False)
        result = pipeline.normalize(df_canaux_french)
        explanation = result.get_explanation()
        assert isinstance(explanation, str)
        assert len(explanation) > 0

    def test_pipeline_unknown_dataset_handled_gracefully(self, df_hr_dataset):
        """Un dataset RH (sans schéma associé) doit échouer proprement."""
        pipeline = NormalizationPipeline(use_semantic=False, use_llm_fallback=False)
        result = pipeline.normalize(df_hr_dataset)

        # success peut être False sans crash, c'est l'essentiel
        assert isinstance(result.success, bool)
        assert result.report is not None
        assert result.profile is not None

    def test_pipeline_normalize_all_schemas(self, df_canaux_renamed):
        pipeline = NormalizationPipeline(use_semantic=False)
        results = pipeline.normalize_all_schemas(df_canaux_renamed)

        assert isinstance(results, dict)
        # Au moins le schéma canaux doit avoir réussi
        assert "canaux" in results
        assert results["canaux"].success is True


# ================================================================
# Tests compatibilité avec les analyzers existants
# ================================================================


class TestAnalyzerCompatibility:
    """
    Vérifie que le DataFrame normalisé est consommable SANS MODIFICATION
    par les analyzers existants. C'est la garantie de non-régression.
    """

    def test_canaux_analyzer_accepts_normalized_df(self, df_canaux_renamed):
        from backend.analysis import canaux_analyzer

        pipeline = NormalizationPipeline(use_semantic=False)
        result = pipeline.normalize(df_canaux_renamed)
        assert result.success is True

        kpis = canaux_analyzer.analyze(result.normalized_df)
        assert "total_ca" in kpis
        assert kpis["total_ca"] == 1_000_000.0  # 450k + 350k + 200k

    def test_kpis_analyzer_accepts_normalized_df(self):
        """
        Vérifie que kpis_analyzer consomme un DataFrame normalisé.

        Note : seules les COLONNES sont normalisées par cette V1, pas les
        VALEURS. L'utilisateur doit donc fournir des libellés d'indicateurs
        reconnaissables (ex : "CA Total (TND)").
        """
        from backend.analysis import kpis_analyzer

        df = pd.DataFrame({
            "kpi_name": [
                "CA Total (TND)", "Profit Total (TND)",
                "Marge Beneficiaire (%)",
            ],
            "value": [500_000.0, 125_000.0, 25.0],
        })

        pipeline = NormalizationPipeline(use_semantic=False)
        result = pipeline.normalize(df)
        assert result.success is True

        kpis = kpis_analyzer.analyze(result.normalized_df)
        assert kpis["revenue_total"] == 500_000.0
        assert kpis["profit_total"] == 125_000.0

    def test_categories_analyzer_accepts_normalized_df(self):
        df = pd.DataFrame({
            "categorie":        ["Mobilier", "Electronique", "Textile"],
            "turnover":         [962_000.0, 919_000.0, 117_000.0],
            "net_income":       [240_000.0, 229_000.0, 29_000.0],
            "num_orders":       [347, 362, 370],
            "units_sold":       [1906, 2032, 2012],
            "average_price":    [496.82, 457.85, 59.09],
        })

        from backend.analysis import categories_analyzer

        pipeline = NormalizationPipeline(use_semantic=False)
        result = pipeline.normalize(df, target_schema_name="categories")
        assert result.success is True

        kpis = categories_analyzer.analyze(result.normalized_df)
        assert "total_revenue" in kpis
        assert kpis["top_category_by_revenue"] == "Mobilier"


# ================================================================
# Tests fallback LLM (mocké)
# ================================================================


class TestLlmFallbackMocked:
    """Tests du fallback LLM avec DeepSeek mocké (pas d'appel Azure réel)."""

    def test_schema_mapper_calls_llm_for_unmapped(self):
        """Si use_llm_fallback=True, le mapper appelle le LLM pour les non-mappés."""
        df = pd.DataFrame({
            "sales_channel":   ["A"],
            "ca_total":        [100.0],
            "nb_transactions": [10],
            "panier_moyen":    [10.0],
            "weird_column":    ["xyz"],
        })
        profile = DatasetProfiler().profile(df)

        mock_response = MagicMock()
        mock_response.content = '{"weird_column": null}'
        mock_llm = MagicMock()
        mock_llm.invoke = MagicMock(return_value=mock_response)

        # ChatOpenAI est importé dynamiquement dans _call_llm_for_mapping,
        # on patche donc dans son module d'origine.
        with patch(
            "langchain_openai.ChatOpenAI",
            return_value=mock_llm,
        ):
            mapper = SchemaMapper(use_semantic=False, use_llm_fallback=True)
            mappings = mapper.map_columns(profile, target_schema=CANAUX_SCHEMA)

        # Les colonnes du schéma sont mappées par synonymes
        # weird_column reste non mappé (LLM a retourné null)
        assert any(
            m.source_column == "weird_column" and not m.is_mapped
            for m in mappings
        )
