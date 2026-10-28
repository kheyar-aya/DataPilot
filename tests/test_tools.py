"""Tests pour le registre datapilot.tools (schémas JSON et appel des outils)."""

import json

from datapilot.tools import TOOLS, call_tool, get_tool_schemas
from datapilot.tools.data_store import DataStore


def test_registry_lists_all_tools() -> None:
    """Le registre expose les quatre outils."""
    assert [t.name for t in TOOLS] == ["get_schema", "run_sql", "describe_column", "make_chart"]


def test_tool_schemas_are_valid() -> None:
    """Chaque schéma a un nom, une description et des paramètres JSON Schema."""
    schemas = get_tool_schemas()
    json.dumps(schemas)
    for schema in schemas:
        assert schema["description"]
        assert schema["parameters"]["type"] == "object"
    by_name = {s["name"]: s for s in schemas}
    assert by_name["run_sql"]["parameters"]["required"] == ["query"]
    assert set(by_name["describe_column"]["parameters"]["required"]) == {"table", "column"}
    chart_type = by_name["make_chart"]["parameters"]["properties"]["chart_type"]
    assert chart_type["enum"] == ["bar", "line", "scatter", "histogram", "pie"]
    assert "store" not in json.dumps(schemas)


def test_call_tool_with_dict_and_json(store: DataStore) -> None:
    """call_tool accepte des arguments en dict ou en chaîne JSON."""
    assert call_tool(store, "get_schema", None)["tables"][0]["name"] == "ventes"
    result = call_tool(store, "run_sql", '{"query": "SELECT 1 AS x"}')
    assert result["rows"] == [{"x": 1}]
    result = call_tool(store, "describe_column", {"table": "ventes", "column": "prix"})
    assert result["kind"] == "numeric"


def test_call_tool_unknown_tool(store: DataStore) -> None:
    """Un outil inconnu renvoie une erreur."""
    assert "error" in call_tool(store, "drop_everything", {})


def test_call_tool_invalid_arguments(store: DataStore) -> None:
    """Des arguments invalides renvoient une erreur de validation."""
    assert "error" in call_tool(store, "run_sql", {})
    result = call_tool(store, "make_chart", {"query": "SELECT 1", "chart_type": "radar", "x": "a"})
    assert "chart_type" in result["error"]
    assert "error" in call_tool(store, "run_sql", "{pas du json")
