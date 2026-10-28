"""Tests pour datapilot.tools.data_store."""

import shutil
from pathlib import Path

import pytest

from datapilot.tools.data_store import DataStore, table_name_from_path
from tests.conftest import SAMPLE_CSV


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("data/ventes.csv", "ventes"),
        ("Ventes 2024 (Q1).csv", "ventes_2024_q1"),
        ("données-élèves.csv", "donnees_eleves"),
        ("2024_ventes.csv", "t_2024_ventes"),
        ("###.csv", "table"),
    ],
)
def test_table_name_from_path(path: str, expected: str) -> None:
    """Le nom de table est dérivé proprement du nom de fichier."""
    assert table_name_from_path(path) == expected


def test_load_sample_csv(store: DataStore) -> None:
    """Le CSV d'exemple est chargé dans la table `ventes` avec les bons types."""
    assert store.tables() == ["ventes"]
    assert store.columns("ventes") == [
        ("date", "DATE"),
        ("region", "VARCHAR"),
        ("produit", "VARCHAR"),
        ("quantite", "BIGINT"),
        ("prix", "DOUBLE"),
    ]
    _, rows = store.fetch("SELECT count(*) FROM ventes")
    assert rows[0][0] == 120


def test_load_multiple_csv_and_reserved_name(tmp_path: Path) -> None:
    """Plusieurs CSV donnent plusieurs tables ; un mot réservé SQL est suffixé."""
    order_csv = tmp_path / "order.csv"
    shutil.copy(SAMPLE_CSV, order_csv)
    with DataStore([SAMPLE_CSV, order_csv]) as store:
        assert store.tables() == ["order_data", "ventes"]


def test_load_csv_custom_name(store: DataStore) -> None:
    """Un nom de table explicite est respecté."""
    assert store.load_csv(SAMPLE_CSV, table_name="sales") == "sales"
    assert "sales" in store.tables()


def test_load_missing_file_raises(store: DataStore) -> None:
    """Charger un fichier inexistant lève FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        store.load_csv("introuvable.csv")


def test_columns_unknown_table_raises(store: DataStore) -> None:
    """Demander les colonnes d'une table inconnue lève KeyError."""
    with pytest.raises(KeyError):
        store.columns("inconnue")


def test_filesystem_access_disabled(store: DataStore) -> None:
    """Les requêtes ne peuvent pas lire de fichiers arbitraires."""
    with pytest.raises(Exception, match="disabled"):
        store.fetch(f"SELECT * FROM read_csv('{SAMPLE_CSV}')")
