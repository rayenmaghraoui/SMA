"""
Tests unitaires et d'intégration — SQL Agent.

Couverture :
    - validator.py : validate_sql(), enforce_limit()
    - intent_router.py : classify_intent()
    - db.py : get_schema()
    - executor.py : execute_sql() (avec DuckDB en mémoire)
    - route POST /sql/query (mock LLM)

Lancer : pytest backend/tests/test_sql_agent.py -v
"""

from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from backend.main import app
from backend.sql_agent.intent_router import classify_intent
from backend.sql_agent.validator import enforce_limit, validate_sql


# ================================================================
# Tests validate_sql
# ================================================================


class TestValidateSql:
    """Tests du validateur de sécurité SQL."""

    def test_valid_select(self):
        """Une requête SELECT simple est valide."""
        ok, err = validate_sql("SELECT * FROM finance LIMIT 10")
        assert ok is True
        assert err == ""

    def test_rejects_empty(self):
        """Une requête vide est rejetée."""
        ok, err = validate_sql("   ")
        assert ok is False
        assert err != ""

    def test_rejects_drop(self):
        """DROP TABLE est refusé."""
        ok, err = validate_sql("DROP TABLE finance")
        assert ok is False
        assert err != ""

    def test_rejects_delete(self):
        """DELETE est refusé."""
        ok, err = validate_sql("DELETE FROM finance WHERE revenue < 0")
        assert ok is False

    def test_rejects_update(self):
        """UPDATE est refusé."""
        ok, err = validate_sql("UPDATE finance SET revenue = 0")
        assert ok is False

    def test_rejects_insert(self):
        """INSERT est refusé."""
        ok, err = validate_sql("INSERT INTO finance VALUES (1, 2, 3)")
        assert ok is False

    def test_rejects_alter(self):
        """ALTER TABLE est refusé."""
        ok, err = validate_sql("ALTER TABLE finance ADD COLUMN test INT")
        assert ok is False

    def test_rejects_comment_double_dash(self):
        """Les commentaires -- sont refusés."""
        ok, err = validate_sql("SELECT * FROM finance -- DROP TABLE finance")
        assert ok is False

    def test_rejects_comment_block(self):
        """Les commentaires /* sont refusés."""
        ok, err = validate_sql("SELECT * FROM finance /* DROP TABLE */")
        assert ok is False

    def test_rejects_multiple_semicolons(self):
        """Plusieurs points-virgules sont refusés."""
        ok, err = validate_sql("SELECT 1; DROP TABLE finance")
        assert ok is False

    def test_case_insensitive_detection(self):
        """La détection des mots-clés est insensible à la casse."""
        ok, err = validate_sql("drop table finance")
        assert ok is False

    def test_complex_select_is_valid(self):
        """Un SELECT avec JOIN, GROUP BY, ORDER BY est valide."""
        sql = """
        SELECT channel, SUM(conversions) as total_conversions
        FROM marketing
        GROUP BY channel
        ORDER BY total_conversions DESC
        LIMIT 10
        """
        ok, err = validate_sql(sql)
        assert ok is True


# ================================================================
# Tests enforce_limit
# ================================================================


class TestEnforceLimit:
    """Tests de l'imposition du LIMIT."""

    def test_adds_limit_if_absent(self):
        """Ajoute LIMIT 500 si absent."""
        sql = enforce_limit("SELECT * FROM finance")
        assert "LIMIT 500" in sql.upper()

    def test_respects_smaller_existing_limit(self):
        """Conserve un LIMIT existant inférieur à 500."""
        sql = enforce_limit("SELECT * FROM finance LIMIT 10")
        assert "LIMIT 10" in sql.upper()
        assert "LIMIT 500" not in sql.upper()

    def test_reduces_large_limit(self):
        """Réduit un LIMIT trop élevé à MAX_ROWS."""
        sql = enforce_limit("SELECT * FROM finance LIMIT 10000")
        assert "LIMIT 500" in sql.upper()
        assert "LIMIT 10000" not in sql.upper()

    def test_custom_max_rows(self):
        """Respecte le max_rows personnalisé."""
        sql = enforce_limit("SELECT * FROM finance", max_rows=50)
        assert "LIMIT 50" in sql.upper()

    def test_strips_trailing_semicolon(self):
        """Supprime le point-virgule final."""
        sql = enforce_limit("SELECT * FROM finance;")
        assert sql.endswith(";") is False


# ================================================================
# Tests classify_intent
# ================================================================


class TestClassifyIntent:
    """Tests du routeur d'intention."""

    def test_sql_intent_show(self):
        """'Montre-moi' déclenche l'intention SQL."""
        assert classify_intent("Montre-moi les 10 meilleures campagnes") == "sql"

    def test_sql_intent_top(self):
        """'Top 5' déclenche l'intention SQL."""
        assert classify_intent("Top 5 des canaux par budget") == "sql"

    def test_sql_intent_total_par(self):
        """'Total par canal' déclenche l'intention SQL."""
        assert classify_intent("Donne-moi le total des conversions par canal") == "sql"

    def test_sql_intent_combien(self):
        """'Combien' déclenche l'intention SQL."""
        assert classify_intent("Combien de tickets ont un churn_risk élevé ?") == "sql"

    def test_strategic_intent_recommend(self):
        """'Recommandations' déclenche l'intention stratégique."""
        assert classify_intent("Donne-moi des recommandations pour améliorer la marge") == "strategic"

    def test_strategic_intent_analyze(self):
        """'Analysez' déclenche l'intention stratégique."""
        assert classify_intent("Analysez les performances financières globales") == "strategic"

    def test_strategic_intent_why(self):
        """'Pourquoi' déclenche l'intention stratégique."""
        assert classify_intent("Pourquoi le chiffre d'affaires baisse-t-il ?") == "strategic"

    def test_strategic_wins_on_tie(self):
        """En cas d'égalité, l'intention stratégique gagne."""
        # Question neutre sans pattern fort des deux côtés
        result = classify_intent("Comment va l'entreprise ?")
        assert result == "strategic"


# ================================================================
# Tests execute_sql (DuckDB en mémoire avec données mock)
# ================================================================


class TestExecuteSql:
    """Tests d'exécution SQL avec DuckDB."""

    @pytest.fixture(autouse=True)
    def mock_duckdb(self):
        """Injecte une connexion DuckDB de test avec données factices."""
        import duckdb

        conn = duckdb.connect(":memory:")
        finance_df = pd.DataFrame({
            "date": ["2024-01-01", "2024-02-01"],
            "revenue": [100_000.0, 110_000.0],
            "cost": [70_000.0, 75_000.0],
            "profit": [30_000.0, 35_000.0],
            "growth_rate": [0.0, 10.0],
        })
        conn.register("finance", finance_df)

        with patch("backend.sql_agent.executor.get_connection", return_value=conn):
            yield

    @pytest.mark.asyncio
    async def test_valid_query_returns_rows(self):
        """Une requête SELECT valide retourne des lignes."""
        from backend.sql_agent.executor import execute_sql
        rows, errors = await execute_sql("SELECT * FROM finance")
        assert errors == []
        assert len(rows) == 2
        assert "revenue" in rows[0]

    @pytest.mark.asyncio
    async def test_invalid_sql_returns_error(self):
        """Une requête invalide retourne une erreur sans crash."""
        from backend.sql_agent.executor import execute_sql
        rows, errors = await execute_sql("DROP TABLE finance")
        assert rows == []
        assert len(errors) > 0

    @pytest.mark.asyncio
    async def test_limit_enforced(self):
        """Le LIMIT est bien imposé (max 500)."""
        from backend.sql_agent.executor import execute_sql
        rows, errors = await execute_sql("SELECT * FROM finance LIMIT 1")
        assert errors == []
        assert len(rows) == 1

    @pytest.mark.asyncio
    async def test_result_is_list_of_dicts(self):
        """Le résultat est une liste de dictionnaires."""
        from backend.sql_agent.executor import execute_sql
        rows, _ = await execute_sql("SELECT revenue FROM finance LIMIT 1")
        assert isinstance(rows, list)
        assert isinstance(rows[0], dict)


# ================================================================
# Tests route POST /sql/query
# ================================================================


@pytest_asyncio.fixture
async def client():
    """Client HTTP asynchrone de test."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


class TestSqlQueryRoute:
    """Tests de la route POST /sql/query."""

    @pytest.mark.asyncio
    async def test_sql_query_success(self, client):
        """Un appel réussi retourne 200 avec les champs attendus."""
        import duckdb

        conn = duckdb.connect(":memory:")
        ventes_df = pd.DataFrame({
            "invoice_id":       ["INV001"],
            "product_name":     ["Laptop"],
            "category":         ["Electronique"],
            "quantity":         [1],
            "unit_price_tnd":   [2_000.0],
            "revenue_tnd":      [2_000.0],
            "customer_id":      ["C001"],
            "customer_region":  ["Tunis"],
            "sale_date":        ["2024-01-15"],
            "sales_channel":    ["Site Web"],
            "payment_method":   ["Carte"],
            "estimated_profit": [600.0],
        })
        conn.register("ventes", ventes_df)

        with (
            patch("backend.routes.sql.generate_sql", new_callable=AsyncMock) as mock_gen,
            patch("backend.sql_agent.executor.get_connection", return_value=conn),
        ):
            mock_gen.return_value = ("SELECT * FROM ventes LIMIT 10", "table")

            response = await client.post("/sql/query", json={"question": "Montre les ventes"})

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "sql" in data
        assert "rows_preview" in data
        assert "total_rows" in data
        assert "errors" in data

    @pytest.mark.asyncio
    async def test_sql_query_llm_error(self, client):
        """Si le LLM échoue, retourne success=False avec message d'erreur."""
        with patch(
            "backend.routes.sql.generate_sql",
            new_callable=AsyncMock,
            side_effect=Exception("LLM indisponible"),
        ):
            response = await client.post("/sql/query", json={"question": "Test"})

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert len(data["errors"]) > 0

    @pytest.mark.asyncio
    async def test_sql_query_missing_body(self, client):
        """Un body vide retourne 422."""
        response = await client.post("/sql/query", json={})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_sql_query_too_short_question(self, client):
        """Une question trop courte retourne 422."""
        response = await client.post("/sql/query", json={"question": "ab"})
        assert response.status_code == 422
