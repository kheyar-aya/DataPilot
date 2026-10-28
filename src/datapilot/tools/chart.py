"""Outil `make_chart` : génération de graphiques Plotly à partir d'une requête SQL."""

from __future__ import annotations

import json
from typing import Literal

import plotly.express as px
from pydantic import BaseModel, Field

from datapilot.tools._common import ToolResult, safe_tool
from datapilot.tools.data_store import DataStore
from datapilot.tools.sql import validate_select

ChartType = Literal["bar", "line", "scatter", "histogram", "pie"]
CHART_TYPES: tuple[str, ...] = ("bar", "line", "scatter", "histogram", "pie")
MAX_CHART_ROWS = 5000


class MakeChartArgs(BaseModel):
    """Arguments de `make_chart`."""

    query: str = Field(description="Requête SELECT (DuckDB) produisant les données à tracer.")
    chart_type: ChartType = Field(description="Type de graphique.")
    x: str = Field(
        description="Colonne du résultat pour l'axe X (catégories du camembert pour 'pie')."
    )
    y: str | None = Field(
        default=None,
        description="Colonne du résultat pour l'axe Y (valeurs pour 'pie'). "
        "Facultative uniquement pour 'histogram'.",
    )


@safe_tool
def make_chart(
    store: DataStore, query: str, chart_type: str, x: str, y: str | None = None
) -> ToolResult:
    """Exécute une requête SELECT et trace son résultat avec Plotly.

    Types : bar, line, scatter, histogram, pie. Renvoie la figure au format JSON Plotly.
    """
    if chart_type not in CHART_TYPES:
        return {"error": f"Type de graphique inconnu : '{chart_type}'. Types : {CHART_TYPES}."}
    if y is None and chart_type != "histogram":
        return {"error": f"Le paramètre 'y' est obligatoire pour un graphique '{chart_type}'."}

    sql = validate_select(query)
    df = store.fetch_df(f"SELECT * FROM ({sql}) AS q LIMIT {MAX_CHART_ROWS + 1}")
    truncated = len(df) > MAX_CHART_ROWS
    df = df.head(MAX_CHART_ROWS)

    missing = [col for col in (x, y) if col is not None and col not in df.columns]
    if missing:
        return {
            "error": f"Colonne(s) absente(s) du résultat : {missing}. "
            f"Colonnes disponibles : {list(df.columns)}."
        }

    if chart_type == "pie":
        fig = px.pie(df, names=x, values=y)
    else:
        plot = {"bar": px.bar, "line": px.line, "scatter": px.scatter, "histogram": px.histogram}
        fig = plot[chart_type](df, x=x, y=y)

    return {
        "chart_type": chart_type,
        "row_count": len(df),
        "truncated": truncated,
        "figure": json.loads(fig.to_json()),
    }
