"""Outil `run_sql` : exécution de requêtes SELECT en lecture seule."""

from __future__ import annotations

import duckdb
from pydantic import BaseModel, Field

from datapilot.tools._common import ToolResult, safe_tool, to_jsonable
from datapilot.tools.data_store import DataStore

MAX_ROWS = 100


class RunSqlArgs(BaseModel):
    """Arguments de `run_sql`."""

    query: str = Field(
        description="Requête SQL (dialecte DuckDB) de type SELECT ou WITH ... SELECT."
    )


def validate_select(query: str) -> str:
    """Vérifie que `query` est une unique requête SELECT et renvoie son texte nettoyé."""
    statements = duckdb.extract_statements(query)
    if len(statements) != 1:
        raise ValueError(f"Une seule requête attendue, {len(statements)} reçue(s).")
    if statements[0].type != duckdb.StatementType.SELECT:
        raise ValueError("Seules les requêtes SELECT sont autorisées.")
    return statements[0].query.strip().rstrip(";").rstrip()


@safe_tool
def run_sql(store: DataStore, query: str) -> ToolResult:
    """Exécute une requête SQL SELECT (dialecte DuckDB) sur les tables chargées.

    Renvoie au plus 100 lignes ainsi que le nombre total de lignes du résultat.
    """
    sql = validate_select(query)
    _, count_rows = store.fetch(f"SELECT count(*) FROM ({sql}) AS q")
    columns, rows = store.fetch(f"SELECT * FROM ({sql}) AS q LIMIT {MAX_ROWS}")
    total = count_rows[0][0]
    return {
        "columns": columns,
        "rows": [dict(zip(columns, to_jsonable(list(r)), strict=True)) for r in rows],
        "row_count": total,
        "truncated": total > len(rows),
    }
