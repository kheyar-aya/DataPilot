"""Stockage des CSV dans une base DuckDB en mémoire, en lecture seule pour les outils."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

from datapilot.tools._common import quote_ident


def table_name_from_path(path: str | Path) -> str:
    """Dérive un nom de table SQL propre (minuscules, ASCII, `_`) du nom de fichier."""
    stem = unicodedata.normalize("NFKD", Path(path).stem).encode("ascii", "ignore").decode()
    name = re.sub(r"[^0-9a-zA-Z]+", "_", stem).strip("_").lower() or "table"
    if name[0].isdigit():
        name = f"t_{name}"
    return name


class DataStore:
    """Base DuckDB en mémoire contenant une table par fichier CSV chargé.

    L'accès au système de fichiers est désactivé dans DuckDB : les requêtes ne
    peuvent lire que les tables chargées via `load_csv`.
    """

    def __init__(self, csv_paths: Iterable[str | Path] = ()) -> None:
        """Crée la base et charge les CSV fournis."""
        self._con = duckdb.connect(":memory:")
        self._con.execute("SET enable_external_access = false")
        self._reserved = {
            row[0]
            for row in self._con.execute(
                "SELECT keyword_name FROM duckdb_keywords() WHERE keyword_category = 'reserved'"
            ).fetchall()
        }
        for path in csv_paths:
            self.load_csv(path)

    def load_csv(self, path: str | Path, table_name: str | None = None) -> str:
        """Charge un CSV dans une table (remplacée si elle existe) et renvoie son nom."""
        path = Path(path)
        if not path.is_file():
            raise FileNotFoundError(f"Fichier CSV introuvable : {path}")
        name = table_name or table_name_from_path(path)
        if name in self._reserved:
            name = f"{name}_data"

        # La connexion principale n'a pas accès aux fichiers : lecture via une
        # connexion temporaire, puis restauration des types inférés par DuckDB.
        with duckdb.connect(":memory:") as tmp:
            rel = tmp.read_csv(str(path))
            types = [str(t) for t in rel.dtypes]
            df = rel.df()

        casts = ", ".join(
            f"CAST({quote_ident(col)} AS {typ}) AS {quote_ident(col)}"
            for col, typ in zip(df.columns, types, strict=True)
        )
        self._con.register("__csv_import", df)
        try:
            self._con.execute(
                f"CREATE OR REPLACE TABLE {quote_ident(name)} AS SELECT {casts} FROM __csv_import"
            )
        finally:
            self._con.unregister("__csv_import")
        return name

    def tables(self) -> list[str]:
        """Renvoie les noms des tables chargées, triés."""
        rows = self._con.execute(
            "SELECT table_name FROM duckdb_tables() WHERE NOT internal ORDER BY table_name"
        ).fetchall()
        return [r[0] for r in rows]

    def columns(self, table: str) -> list[tuple[str, str]]:
        """Renvoie les couples (colonne, type DuckDB) d'une table."""
        if table not in self.tables():
            raise KeyError(table)
        rows = self._con.execute(f"DESCRIBE {quote_ident(table)}").fetchall()
        return [(r[0], r[1]) for r in rows]

    def fetch(self, sql: str, params: list[Any] | None = None) -> tuple[list[str], list[tuple]]:
        """Exécute une requête et renvoie (noms de colonnes, lignes)."""
        cur = self._con.execute(sql, params)
        columns = [d[0] for d in cur.description] if cur.description else []
        return columns, cur.fetchall()

    def fetch_df(self, sql: str) -> pd.DataFrame:
        """Exécute une requête et renvoie le résultat sous forme de DataFrame."""
        return self._con.execute(sql).df()

    def close(self) -> None:
        """Ferme la connexion DuckDB."""
        self._con.close()

    def __enter__(self) -> DataStore:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
