"""Tests vérifiant l'intégrité du jeu de données d'exemple."""

from pathlib import Path

import pandas as pd

SAMPLE_CSV = Path(__file__).resolve().parents[1] / "data" / "sample" / "ventes.csv"

EXPECTED_COLUMNS = ["date", "region", "produit", "quantite", "prix"]


def test_sample_csv_exists() -> None:
    """Le CSV d'exemple est présent dans data/sample/."""
    assert SAMPLE_CSV.exists()


def test_sample_csv_has_expected_columns() -> None:
    """Le CSV d'exemple contient les colonnes attendues."""
    df = pd.read_csv(SAMPLE_CSV)
    assert list(df.columns) == EXPECTED_COLUMNS


def test_sample_csv_has_rows_and_valid_types() -> None:
    """Le CSV d'exemple contient des lignes avec des types cohérents."""
    df = pd.read_csv(SAMPLE_CSV, parse_dates=["date"])
    assert len(df) > 0
    assert (df["quantite"] > 0).all()
    assert (df["prix"] > 0).all()
