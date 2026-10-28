"""Tests pour datapilot.tools.schema (outils get_schema et describe_column)."""

import json

import pytest

from datapilot.tools.data_store import DataStore
from datapilot.tools.schema import column_kind, describe_column, get_schema


def test_get_schema(store: DataStore) -> None:
    """get_schema décrit la table, ses colonnes, son nombre de lignes et 3 exemples."""
    result = get_schema(store)
    json.dumps(result)
    [table] = result["tables"]
    assert table["name"] == "ventes"
    assert table["row_count"] == 120
    assert [c["name"] for c in table["columns"]] == [
        "date", "region", "produit", "quantite", "prix",
    ]  # fmt: skip
    assert len(table["sample_rows"]) == 3
    assert table["sample_rows"][0]["region"] == "Centre"


def test_get_schema_empty_store() -> None:
    """Sans CSV chargé, get_schema renvoie une liste de tables vide."""
    with DataStore() as empty:
        assert get_schema(empty) == {"tables": []}


def test_describe_numeric_column(store: DataStore) -> None:
    """Une colonne numérique donne min/max/moyenne/quantiles cohérents."""
    result = describe_column(store, "ventes", "quantite")
    json.dumps(result)
    assert result["kind"] == "numeric"
    assert result["count"] == 120
    assert result["null_count"] == 0
    assert result["min"] <= result["q25"] <= result["median"] <= result["q75"] <= result["max"]
    assert result["min"] <= result["mean"] <= result["max"]


def test_describe_categorical_column(store: DataStore) -> None:
    """Une colonne catégorielle donne le nb de valeurs uniques et les plus fréquentes."""
    result = describe_column(store, "ventes", "region")
    json.dumps(result)
    assert result["kind"] == "categorical"
    assert result["n_unique"] == 5
    counts = [v["count"] for v in result["top_values"]]
    assert sum(counts) == 120
    assert counts == sorted(counts, reverse=True)


def test_describe_temporal_column(store: DataStore) -> None:
    """Une colonne date donne min et max au format ISO."""
    result = describe_column(store, "ventes", "date")
    assert result["kind"] == "temporal"
    assert result["min"] == "2024-01-01"


def test_describe_unknown_column(store: DataStore) -> None:
    """Une colonne inexistante renvoie une erreur listant les colonnes."""
    result = describe_column(store, "ventes", "inexistante")
    assert "inexistante" in result["error"]
    assert "region" in result["error"]


def test_describe_unknown_table(store: DataStore) -> None:
    """Une table inexistante renvoie une erreur listant les tables."""
    result = describe_column(store, "clients", "region")
    assert "clients" in result["error"]
    assert "ventes" in result["error"]


@pytest.mark.parametrize(
    ("duckdb_type", "kind"),
    [
        ("BIGINT", "numeric"),
        ("DECIMAL(10,2)", "numeric"),
        ("DOUBLE", "numeric"),
        ("DATE", "temporal"),
        ("TIMESTAMP WITH TIME ZONE", "temporal"),
        ("VARCHAR", "categorical"),
        ("BOOLEAN", "categorical"),
    ],
)
def test_column_kind(duckdb_type: str, kind: str) -> None:
    """Les types DuckDB sont correctement classés."""
    assert column_kind(duckdb_type) == kind
