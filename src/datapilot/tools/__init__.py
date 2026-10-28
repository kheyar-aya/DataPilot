"""Outils (function calling) exposés aux agents : chargement CSV, requêtes DuckDB, graphiques.

Le registre `TOOLS` associe chaque outil à son modèle d'arguments Pydantic ;
`get_tool_schemas()` fournit les schémas JSON et `call_tool()` exécute un appel.
"""

from __future__ import annotations

import inspect
import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ValidationError

from datapilot.tools._common import ToolResult
from datapilot.tools.chart import MakeChartArgs, make_chart
from datapilot.tools.data_store import DataStore
from datapilot.tools.schema import DescribeColumnArgs, GetSchemaArgs, describe_column, get_schema
from datapilot.tools.sql import RunSqlArgs, run_sql


@dataclass(frozen=True)
class Tool:
    """Outil appelable par un agent : fonction, modèle d'arguments et description."""

    name: str
    func: Callable[..., ToolResult]
    args_model: type[BaseModel]

    @property
    def description(self) -> str:
        """Renvoie la docstring de la fonction, utilisée comme description pour le LLM."""
        return " ".join(inspect.getdoc(self.func).split())

    def json_schema(self) -> dict[str, Any]:
        """Renvoie le schéma de l'outil au format function calling (name/description/parameters)."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.args_model.model_json_schema(),
        }


TOOLS: list[Tool] = [
    Tool("get_schema", get_schema, GetSchemaArgs),
    Tool("run_sql", run_sql, RunSqlArgs),
    Tool("describe_column", describe_column, DescribeColumnArgs),
    Tool("make_chart", make_chart, MakeChartArgs),
]
TOOLS_BY_NAME: dict[str, Tool] = {tool.name: tool for tool in TOOLS}


def get_tool_schemas() -> list[dict[str, Any]]:
    """Renvoie les schémas JSON de tous les outils enregistrés."""
    return [tool.json_schema() for tool in TOOLS]


def call_tool(store: DataStore, name: str, arguments: dict[str, Any] | str | None) -> ToolResult:
    """Valide les arguments puis exécute l'outil `name` ; renvoie `{"error": ...}` si échec."""
    tool = TOOLS_BY_NAME.get(name)
    if tool is None:
        return {"error": f"Outil inconnu : '{name}'. Outils disponibles : {list(TOOLS_BY_NAME)}."}
    try:
        if isinstance(arguments, str):
            args = tool.args_model.model_validate_json(arguments or "{}")
        else:
            args = tool.args_model.model_validate(arguments or {})
    except ValidationError as exc:
        details = json.dumps(exc.errors(include_url=False, include_context=False), default=str)
        return {"error": f"Arguments invalides pour '{name}' : {details}"}
    return tool.func(store, **args.model_dump())


__all__ = [
    "TOOLS",
    "TOOLS_BY_NAME",
    "DataStore",
    "Tool",
    "call_tool",
    "describe_column",
    "get_schema",
    "get_tool_schemas",
    "make_chart",
    "run_sql",
]
