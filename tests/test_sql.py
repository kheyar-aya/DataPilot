"""Tests pour datapilot.tools.sql (outil run_sql)."""

import json

import pytest

from datapilot.tools.data_store import DataStore
from datapilot.tools.sql import MAX_ROWS, run_sql, validate_select


def test_run_sql_aggregation(store: DataStore) -> None:
    """Une agrégation renvoie colonnes, lignes et nombre total de lignes."""
    result = run_sql(store, "SELECT region, count(*) AS n FROM ventes GROUP BY region")
    assert "error" not in result
    assert result["columns"] == ["region", "n"]
    assert result["row_count"] == 5
    assert result["truncated"] is False
    assert sum(row["n"] for row in result["rows"]) == 120
    json.dumps(result)


def test_run_sql_limits_rows(store: DataStore) -> None:
    """Le résultat est limité à MAX_ROWS lignes mais row_count donne le total."""
    result = run_sql(store, "SELECT * FROM ventes;")
    assert len(result["rows"]) == MAX_ROWS
    assert result["row_count"] == 120
    assert result["truncated"] is True
    assert result["rows"][0]["date"] == "2024-01-01"
    json.dumps(result)


def test_run_sql_with_cte(store: DataStore) -> None:
    """Les requêtes WITH ... SELECT sont acceptées."""
    result = run_sql(store, "WITH t AS (SELECT sum(quantite) AS q FROM ventes) SELECT q FROM t")
    assert result["row_count"] == 1


def test_run_sql_invalid_sql(store: DataStore) -> None:
    """Un SQL invalide renvoie une erreur au lieu de lever."""
    result = run_sql(store, "SELEC * FROM ventes")
    assert "error" in result


def test_run_sql_unknown_column(store: DataStore) -> None:
    """Une colonne inexistante renvoie une erreur."""
    result = run_sql(store, "SELECT chiffre_affaires FROM ventes")
    assert "chiffre_affaires" in result["error"]


@pytest.mark.parametrize(
    "query",
    [
        "DELETE FROM ventes",
        "DROP TABLE ventes",
        "CREATE TABLE x AS SELECT 1",
        "SELECT 1; DROP TABLE ventes",
        "COPY ventes TO 'out.csv'",
    ],
)
def test_run_sql_rejects_non_select(store: DataStore, query: str) -> None:
    """Toute requête autre qu'un SELECT unique est refusée et les données intactes."""
    assert "error" in run_sql(store, query)
    assert store.tables() == ["ventes"]
    assert run_sql(store, "SELECT count(*) AS n FROM ventes")["rows"] == [{"n": 120}]


def test_validate_select_strips_semicolon() -> None:
    """validate_select renvoie la requête sans point-virgule final."""
    assert validate_select("SELECT 1 ;  ") == "SELECT 1"
