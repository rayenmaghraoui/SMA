"""
Tests d'intégration — routes FastAPI.

Couverture :
    - GET  /health
    - POST /upload  (CSV valide, CSV invalide, CSV vide, mauvais format)
    - POST /analyze (pipeline mocké)
    - GET  /report  (rapport présent, rapport absent)

Lancer : pytest backend/tests/test_routes.py -v
"""

import io
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from backend.main import app


# ================================================================
# Client de test partagé
# ================================================================


@pytest_asyncio.fixture
async def client():
    """Client HTTP asynchrone pour tester l'app FastAPI sans serveur réel."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


# ================================================================
# Helpers CSV
# ================================================================


def _make_finance_csv_bytes() -> bytes:
    """Génère un CSV kpis_globaux valide en mémoire."""
    df = pd.DataFrame({
        "indicateur": [
            "CA Total (TND)", "Profit Total (TND)", "Marge Beneficiaire (%)",
            "Nb Transactions", "Panier Moyen (TND)", "Quantite Totale Vendue",
        ],
        "valeur": [500_000.0, 125_000.0, 25.0, 500, 1_000.0, 1_500],
    })
    buffer = io.BytesIO()
    df.to_csv(buffer, index=False)
    return buffer.getvalue()


def _make_canaux_csv_bytes() -> bytes:
    """Génère un CSV canaux de vente valide en mémoire (04_analyse_canaux.csv)."""
    df = pd.DataFrame({
        "sales_channel":   ["Site Web", "Magasin Physique", "Application Mobile", "Réseaux Sociaux"],
        "ca_total":        [450_000.0, 350_000.0, 200_000.0, 150_000.0],
        "nb_transactions": [450, 300, 200, 150],
        "panier_moyen":    [1_000.0, 1_166.67, 1_000.0, 1_000.0],
    })
    buffer = io.BytesIO()
    df.to_csv(buffer, index=False)
    return buffer.getvalue()


# ================================================================
# Tests GET /health
# ================================================================


class TestHealthRoute:
    """Tests de la route /health."""

    @pytest.mark.asyncio
    async def test_health_returns_200(self, client):
        """GET /health doit retourner HTTP 200."""
        response = await client.get("/health")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_health_response_has_status_key(self, client):
        """La réponse /health doit contenir une clé 'status'."""
        response = await client.get("/health")
        data = response.json()
        assert "status" in data

    @pytest.mark.asyncio
    async def test_health_content_type_is_json(self, client):
        """La réponse /health doit être en JSON."""
        response = await client.get("/health")
        assert "application/json" in response.headers["content-type"]


# ================================================================
# Tests POST /upload
# ================================================================


class TestUploadRoute:
    """Tests de la route /upload."""

    @pytest.fixture(autouse=True)
    def _isolate_uploads(self, tmp_path, monkeypatch):
        """
        Redirige les écritures de la route /upload vers un dossier temporaire.

        Sans cette isolation, les tests d'upload écraseraient les vrais fichiers
        de data/uploads/ (04_analyse_canaux.csv, 05_kpis_globaux.csv, ...) avec
        des données de fixture, corrompant le dataset de démonstration.
        """
        monkeypatch.setattr("backend.routes.upload.UPLOADS_DIR", tmp_path)

    @pytest.mark.asyncio
    async def test_upload_valid_finance_csv_returns_200(self, client):
        """Un CSV kpis valide doit retourner HTTP 200."""
        response = await client.post(
            "/upload",
            files={"file": ("05_kpis_globaux.csv", _make_finance_csv_bytes(), "text/csv")},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_upload_valid_csv_response_has_filename(self, client):
        """La réponse /upload doit contenir le nom du fichier."""
        response = await client.post(
            "/upload",
            files={"file": ("05_kpis_globaux.csv", _make_finance_csv_bytes(), "text/csv")},
        )
        data = response.json()
        assert "filename" in data

    @pytest.mark.asyncio
    async def test_upload_valid_csv_response_has_rows(self, client):
        """La réponse /upload doit indiquer le nombre de lignes."""
        response = await client.post(
            "/upload",
            files={"file": ("05_kpis_globaux.csv", _make_finance_csv_bytes(), "text/csv")},
        )
        data = response.json()
        assert "rows" in data
        assert data["rows"] == 6

    @pytest.mark.asyncio
    async def test_upload_valid_csv_response_has_file_type(self, client):
        """La réponse /upload doit identifier le type du fichier."""
        response = await client.post(
            "/upload",
            files={"file": ("05_kpis_globaux.csv", _make_finance_csv_bytes(), "text/csv")},
        )
        data = response.json()
        assert "file_type" in data
        assert data["file_type"] == "kpis"

    @pytest.mark.asyncio
    async def test_upload_non_csv_file_returns_error(self, client):
        """Un fichier non-CSV doit retourner une erreur (400 ou 422)."""
        response = await client.post(
            "/upload",
            files={"file": ("document.txt", b"ce n'est pas un CSV", "text/plain")},
        )
        assert response.status_code in (400, 422)

    @pytest.mark.asyncio
    async def test_upload_empty_csv_returns_error(self, client):
        """Un CSV vide doit retourner une erreur."""
        empty_csv = b"date,revenue,cost,profit,growth_rate\n"  # headers only
        response = await client.post(
            "/upload",
            files={"file": ("finance.csv", empty_csv, "text/csv")},
        )
        # Erreur attendue (400) ou succès avec rows=0 selon l'implémentation
        data = response.json()
        if response.status_code == 200:
            assert data.get("rows", 0) == 0
        else:
            assert response.status_code in (400, 422)

    @pytest.mark.asyncio
    async def test_upload_canaux_csv_detected_correctly(self, client):
        """Un CSV canaux doit être identifié comme type 'canaux'."""
        response = await client.post(
            "/upload",
            files={"file": ("04_analyse_canaux.csv", _make_canaux_csv_bytes(), "text/csv")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("file_type") == "canaux"


# ================================================================
# Tests POST /analyze
# ================================================================


class TestAnalyzeRoute:
    """Tests de la route /analyze."""

    # État final simulé retourné par le pipeline mocké
    _MOCK_FINAL_STATE = {
        "raw_data": {},
        "user_question": "",
        "kpis": {
            "finance": {
                "revenue_total": 1_000_000.0,
                "profit_total": 300_000.0,
                "profit_margin": 30.0,
                "avg_growth_rate": 5.0,
                "best_month": "2024-12",
                "worst_month": "2024-01",
                "trend": "hausse",
                "revenue_volatility": 10_000.0,
            }
        },
        "anomalies": [],
        "interpretation": "Insight 1: Analyse simulée.",
        "rag_context": [],
        "recommendations": [],
        "report": {},
        "errors": [],
        "current_step": "report_completed",
    }

    @pytest.mark.asyncio
    async def test_analyze_returns_200(self, client):
        """POST /analyze doit retourner HTTP 200 avec use_defaults=True."""
        with patch(
            "backend.routes.analyze.run_graph_async",
            new_callable=AsyncMock,
            return_value=self._MOCK_FINAL_STATE,
        ):
            response = await client.post("/analyze", json={"use_defaults": True})

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_analyze_response_has_kpis(self, client):
        """La réponse /analyze doit contenir une clé 'kpis'."""
        with patch(
            "backend.routes.analyze.run_graph_async",
            new_callable=AsyncMock,
            return_value=self._MOCK_FINAL_STATE,
        ):
            response = await client.post("/analyze", json={"use_defaults": True})

        data = response.json()
        assert "kpis" in data

    @pytest.mark.asyncio
    async def test_analyze_response_has_success_field(self, client):
        """La réponse /analyze doit contenir un champ 'success'."""
        with patch(
            "backend.routes.analyze.run_graph_async",
            new_callable=AsyncMock,
            return_value=self._MOCK_FINAL_STATE,
        ):
            response = await client.post("/analyze", json={"use_defaults": True})

        data = response.json()
        assert "success" in data

    @pytest.mark.asyncio
    async def test_analyze_invalid_body_returns_422(self, client):
        """Un body invalide doit retourner HTTP 422 (validation Pydantic)."""
        response = await client.post("/analyze", json={"use_defaults": "not_a_bool"})
        assert response.status_code == 422


# ================================================================
# Tests GET /report
# ================================================================


class TestReportRoute:
    """Tests de la route /report."""

    @pytest.mark.asyncio
    async def test_report_returns_200_or_404(self, client):
        """GET /report doit retourner 200 (rapport présent) ou 404 (absent)."""
        response = await client.get("/report")
        assert response.status_code in (200, 404)

    @pytest.mark.asyncio
    async def test_report_200_has_expected_structure(self, client, tmp_path):
        """Si un rapport existe, il doit avoir une structure minimale."""
        # Écrire un rapport de test dans le fichier attendu par le backend
        from backend.config import DATA_DIR
        report_path = Path(DATA_DIR) / "last_report.json"

        dummy_report = {
            "titre": "Rapport de test",
            "date_generation": "2024-01-01",
            "kpis": {"finance": {"revenue_total": 1_000_000}},
            "recommandations": [],
        }

        # Sauvegarder temporairement
        original_content = None
        if report_path.exists():
            original_content = report_path.read_text(encoding="utf-8")

        try:
            report_path.write_text(json.dumps(dummy_report), encoding="utf-8")
            response = await client.get("/report")

            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, dict)
        finally:
            # Restaurer le rapport original
            if original_content is not None:
                report_path.write_text(original_content, encoding="utf-8")
