"""Outils d'exploration : `get_schema` (structure des tables) et `describe_column` (stats)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from datapilot.tools._common import ToolResult, quote_ident, safe_tool, to_jsonable
from datapilot.tools.data_store import DataStore

SAMPLE_ROWS = 3
TOP_VALUES = 10

NUMERIC_TYPES = {
    "TINYINT", "SMALLINT", "INTEGER", "BIGINT", "HUGEINT",
    "UTINYINT", "USMALLINT", "UINTEGER", "UBIGINT", "UHUGEINT",
    "FLOAT", "DOUBLE",
}  # fmt: skip
TEMPORAL_PREFIXES = ("DATE", "TIME", "TIMESTAMP", "INTERVAL")


class GetSchemaArgs(BaseModel):
    """Arguments de `get_schema` (aucun)."""


class DescribeColumnArgs(BaseModel):
    """Arguments de `describe_column`."""

    table: str = Field(description="Nom de la table, tel que renvoyé par get_schema.")
    column: str = Field(description="Nom de la colonne à décrire.")


def column_kind(duckdb_type: str) -> str:
    """Classe un type DuckDB en `numeric`, `temporal` ou `categorical`."""
    upper = duckdb_type.upper()
    if upper in NUMERIC_TYPES or upper.startswith("DECIMAL"):
        return "numeric"
    if upper.startswith(TEMPORAL_PREFIXES):
        return "temporal"
    return "categorical"


@safe_tool
def get_schema(store: DataStore) -> ToolResult:
    """Liste les tables disponibles avec leurs colonnes, types, nombre de lignes
    et 3 lignes d'exemple. À appeler en premier pour connaître les données.
    """
    tables = []
    for table in store.tables():
        ident = quote_ident(table)
        _, count = store.fetch(f"SELECT count(*) FROM {ident}")
        columns, sample = store.fetch(f"SELECT * FROM {ident} LIMIT {SAMPLE_ROWS}")
        tables.append(
            {
                "name": table,
                "row_count": count[0][0],
                "columns": [{"name": c, "type": t} for c, t in store.columns(table)],
                "sample_rows": [
                    dict(zip(columns, to_jsonable(list(r)), strict=True)) for r in sample
                ],
            }
        )
    return {"tables": tables}


@safe_tool
def describe_column(store: DataStore, table: str, column: str) -> ToolResult:
    """Calcule des statistiques descriptives sur une colonne : min, max, moyenne,
    écart-type et quantiles pour une colonne numérique ; nombre de valeurs uniques
    et valeurs les plus fréquentes pour une colonne catégorielle.
    """
    tables = store.tables()
    if table not in tables:
        return {"error": f"Table inconnue : '{table}'. Tables disponibles : {tables}."}
    types = dict(store.columns(table))
    if column not in types:
        return {
            "error": f"Colonne inconnue : '{column}' dans '{table}'. "
            f"Colonnes disponibles : {list(types)}."
        }

    t, c = quote_ident(table), quote_ident(column)
    kind = column_kind(types[column])
    _, base = store.fetch(f"SELECT count(*), count({c}), count(DISTINCT {c}) FROM {t}")
    total, non_null, n_unique = base[0]
    result: dict[str, Any] = {
        "table": table,
        "column": column,
        "type": types[column],
        "kind": kind,
        "count": total,
        "null_count": total - non_null,
        "n_unique": n_unique,
    }

    if kind == "numeric":
        _, rows = store.fetch(
            f"SELECT min({c}), max({c}), avg({c}), stddev_samp({c}), "
            f"quantile_cont({c}, [0.25, 0.5, 0.75]) FROM {t}"
        )
        mn, mx, mean, std, quantiles = rows[0]
        q25, q50, q75 = quantiles or (None, None, None)
        result |= {"min": mn, "max": mx, "mean": mean, "std": std,
                   "q25": q25, "median": q50, "q75": q75}  # fmt: skip
    elif kind == "temporal":
        _, rows = store.fetch(f"SELECT min({c}), max({c}) FROM {t}")
        result |= {"min": rows[0][0], "max": rows[0][1]}
    else:
        _, rows = store.fetch(
            f"SELECT {c} AS value, count(*) AS n FROM {t} WHERE {c} IS NOT NULL "
            f"GROUP BY {c} ORDER BY n DESC, value LIMIT {TOP_VALUES}"
        )
        result["top_values"] = [{"value": v, "count": n} for v, n in rows]

    return to_jsonable(result)
