"""Utilitaires partagés par les outils : sérialisation JSON et gestion des erreurs."""

from __future__ import annotations

import functools
import math
from collections.abc import Callable
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Any, ParamSpec

P = ParamSpec("P")

ToolResult = dict[str, Any]


def to_jsonable(value: Any) -> Any:
    """Convertit une valeur renvoyée par DuckDB en valeur sérialisable en JSON."""
    if value is None or isinstance(value, bool | int | str):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, datetime | date | time):
        return value.isoformat()
    if isinstance(value, timedelta):
        return str(value)
    if isinstance(value, list | tuple):
        return [to_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    return str(value)


def quote_ident(name: str) -> str:
    """Échappe un identifiant SQL (table ou colonne) entre guillemets doubles."""
    return '"' + name.replace('"', '""') + '"'


def safe_tool(func: Callable[P, ToolResult]) -> Callable[P, ToolResult]:
    """Transforme toute exception levée par un outil en résultat `{"error": ...}`."""

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> ToolResult:
        try:
            return func(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001 - un outil ne doit jamais lever
            return {"error": str(exc) or type(exc).__name__}

    return wrapper
