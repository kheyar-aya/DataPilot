"""Tests pour datapilot.tools._common."""

from datetime import date, datetime
from decimal import Decimal

from datapilot.tools._common import quote_ident, safe_tool, to_jsonable


def test_to_jsonable() -> None:
    """Les types renvoyés par DuckDB sont convertis en types JSON."""
    assert to_jsonable(Decimal("1.5")) == 1.5
    assert to_jsonable(date(2024, 1, 2)) == "2024-01-02"
    assert to_jsonable(datetime(2024, 1, 2, 3, 4)) == "2024-01-02T03:04:00"
    assert to_jsonable(float("nan")) is None
    assert to_jsonable({"a": [Decimal("2"), None]}) == {"a": [2.0, None]}


def test_quote_ident() -> None:
    """Les guillemets dans un identifiant sont échappés."""
    assert quote_ident('a"b') == '"a""b"'


def test_safe_tool_catches_exceptions() -> None:
    """Une exception devient un résultat {"error": ...}."""

    @safe_tool
    def boom() -> dict:
        raise ValueError("oups")

    assert boom() == {"error": "oups"}
