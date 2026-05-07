"""
Tests d'intégration — système RAG (ChromaDB + sentence-t5-base).

Couverture :
    - retriever.search() : structure des résultats, top-k, sources valides
    - Pertinence sémantique de base (vérification des sources retournées)

Prérequis : ChromaDB doit être indexée (python -m backend.rag.ingest)
Lancer    : pytest backend/tests/test_rag.py -v
"""

import pytest
from pathlib import Path

from backend.config import CHROMA_DB_PATH, RAG_TOP_K
from backend.rag import retriever


# ================================================================
# Skip global si la base ChromaDB n'est pas initialisée
# ================================================================

pytestmark = pytest.mark.skipif(
    not Path(CHROMA_DB_PATH).exists(),
    reason="ChromaDB non initialisée — lancez 'python -m backend.rag.ingest' d'abord",
)

# Sources légitimes attendues dans la base
VALID_SOURCES = {
    "guide_gestion_entreprises_tunisiennes.md",
    "guide_gestion_financiere_tunisie.md",
    "guide_interpretation_kpis_tunisie.md",
    "guide_logistique_supply_chain_tunisie.md",
    "guide_rh_droit_travail_tunisie.md",
}


# ================================================================
# Tests de structure des résultats
# ================================================================


class TestRetrieverStructure:
    """Vérifie la forme des résultats retournés par search()."""

    def test_returns_list(self):
        """search() doit toujours retourner une liste."""
        results = retriever.search("gestion financière Tunisie")
        assert isinstance(results, list)

    def test_returns_top_k_results(self):
        """search() retourne exactement RAG_TOP_K résultats par défaut."""
        results = retriever.search("TVA fiscalité PME")
        assert len(results) == RAG_TOP_K

    def test_custom_k_respected(self):
        """Le paramètre k personnalisé est bien respecté."""
        results = retriever.search("marketing digital", k=1)
        assert len(results) == 1

    def test_result_has_required_keys(self):
        """Chaque résultat doit contenir les clés attendues."""
        results = retriever.search("chiffre d'affaires")
        required_keys = {"page_content", "source", "score"}
        for result in results:
            assert required_keys.issubset(result.keys()), (
                f"Clés manquantes dans le résultat : {required_keys - result.keys()}"
            )

    def test_page_content_is_non_empty_string(self):
        """Le contenu textuel de chaque chunk doit être non vide."""
        results = retriever.search("droit du travail tunisien")
        for result in results:
            assert isinstance(result["page_content"], str)
            assert len(result["page_content"]) > 0

    def test_score_between_0_and_1(self):
        """Le score de similarité doit être compris entre 0 et 1."""
        results = retriever.search("gestion de stock logistique")
        for result in results:
            assert 0.0 <= result["score"] <= 1.0, (
                f"Score hors intervalle : {result['score']}"
            )

    def test_source_is_known_guide(self):
        """La source de chaque résultat doit être l'un des 5 guides attendus."""
        results = retriever.search("contrat de travail CDI CDD Tunisie")
        for result in results:
            assert result["source"] in VALID_SOURCES, (
                f"Source inconnue : {result['source']}"
            )


# ================================================================
# Tests de pertinence sémantique
# ================================================================


class TestRetrieverRelevance:
    """Vérifie que les résultats sont sémantiquement pertinents."""

    def test_finance_query_returns_finance_guide(self):
        """Une requête financière doit retourner le guide finance en priorité."""
        results = retriever.search("marge bénéficiaire chiffre d'affaires TND")
        sources = [r["source"] for r in results]
        assert "guide_gestion_financiere_tunisie.md" in sources, (
            f"Le guide finance n'est pas dans les résultats : {sources}"
        )

    def test_rh_query_returns_rh_guide(self):
        """Une requête RH doit retourner le guide RH en priorité."""
        results = retriever.search("congés payés contrat de travail droit du travail")
        sources = [r["source"] for r in results]
        assert "guide_rh_droit_travail_tunisie.md" in sources, (
            f"Le guide RH n'est pas dans les résultats : {sources}"
        )

    def test_logistique_query_returns_logistique_guide(self):
        """Une requête logistique doit retourner le guide supply chain."""
        results = retriever.search("gestion de stock livraison supply chain")
        sources = [r["source"] for r in results]
        assert "guide_logistique_supply_chain_tunisie.md" in sources, (
            f"Le guide logistique n'est pas dans les résultats : {sources}"
        )

    def test_results_are_ordered_by_score_desc(self):
        """Les résultats doivent être ordonnés par score décroissant."""
        results = retriever.search("TVA taux applicable PME Tunisie")
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True), (
            f"Résultats non triés par score : {scores}"
        )

    def test_different_queries_return_different_results(self):
        """Deux requêtes distinctes doivent retourner des résultats différents."""
        results_finance = retriever.search("profit marge bénéficiaire")
        results_rh = retriever.search("licenciement code du travail")
        contents_finance = {r["page_content"][:50] for r in results_finance}
        contents_rh = {r["page_content"][:50] for r in results_rh}
        assert contents_finance != contents_rh


# ================================================================
# Tests de robustesse
# ================================================================


class TestRetrieverRobustness:
    """Vérifie le comportement du retriever sur des inputs inhabituels."""

    def test_empty_query_does_not_crash(self):
        """Une requête vide ne doit pas provoquer d'exception."""
        try:
            results = retriever.search("")
            assert isinstance(results, list)
        except Exception as e:
            pytest.fail(f"Requête vide a levé une exception : {e}")

    def test_very_long_query_does_not_crash(self):
        """Une requête très longue (> 512 tokens) ne doit pas provoquer d'erreur."""
        long_query = "gestion financière " * 100  # répété pour dépasser 512 tokens
        try:
            results = retriever.search(long_query)
            assert isinstance(results, list)
        except Exception as e:
            pytest.fail(f"Requête longue a levé une exception : {e}")

    def test_arabic_query_does_not_crash(self):
        """Une requête en arabe (langue non principale) ne doit pas crasher."""
        try:
            results = retriever.search("إدارة الأعمال التونسية")
            assert isinstance(results, list)
        except Exception as e:
            pytest.fail(f"Requête en arabe a levé une exception : {e}")
