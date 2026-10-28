"""Tests pour datapilot.tools.chart (outil make_chart)."""

import json

import plotly.io as pio
import pytest

from datapilot.tools.chart import make_chart
from datapilot.tools.data_store import DataStore

AGG_QUERY = "SELECT region, sum(quantite) AS total FROM ventes GROUP BY region ORDER BY region"


@pytest.mark.parametrize(
    ("chart_type", "query", "x", "y", "trace_type"),
    [
        ("bar", AGG_QUERY, "region", "total", "bar"),
        ("line", "SELECT date, prix FROM ventes ORDER BY date", "date", "prix", "scatter"),
        ("scatter", "SELECT quantite, prix FROM ventes", "quantite", "prix", "scatter"),
        ("histogram", "SELECT prix FROM ventes", "prix", None, "histogram"),
        ("pie", AGG_QUERY, "region", "total", "pie"),
    ],
)
def test_make_chart_types(
    store: DataStore, chart_type: str, query: str, x: str, y: str | None, trace_type: str
) -> None:
    """Chaque type de graphique produit une figure Plotly JSON relisible."""
    result = make_chart(store, query, chart_type, x, y)
    assert "error" not in result, result
    assert result["chart_type"] == chart_type
    fig = pio.from_json(json.dumps(result["figure"]))
    assert fig.data[0].type == trace_type


def test_make_chart_row_count(store: DataStore) -> None:
    """Le résultat indique le nombre de lignes tracées."""
    result = make_chart(store, AGG_QUERY, "bar", "region", "total")
    assert result["row_count"] == 5
    assert result["truncated"] is False


def test_make_chart_unknown_column(store: DataStore) -> None:
    """Une colonne absente du résultat renvoie une erreur."""
    result = make_chart(store, AGG_QUERY, "bar", "region", "inexistante")
    assert "inexistante" in result["error"]


def test_make_chart_invalid_sql(store: DataStore) -> None:
    """Un SQL invalide renvoie une erreur."""
    assert "error" in make_chart(store, "SELECT FROM WHERE", "bar", "a", "b")


def test_make_chart_rejects_non_select(store: DataStore) -> None:
    """Une requête autre que SELECT est refusée."""
    assert "error" in make_chart(store, "DROP TABLE ventes", "bar", "a", "b")
    assert store.tables() == ["ventes"]


def test_make_chart_unknown_type(store: DataStore) -> None:
    """Un type de graphique non supporté renvoie une erreur."""
    assert "error" in make_chart(store, AGG_QUERY, "radar", "region", "total")


def test_make_chart_missing_y(store: DataStore) -> None:
    """y est obligatoire hors histogramme."""
    assert "'y'" in make_chart(store, AGG_QUERY, "bar", "region")["error"]
