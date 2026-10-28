"""Fixtures partagées : DataStore chargé avec le CSV d'exemple."""

from collections.abc import Iterator
from pathlib import Path

import pytest

from datapilot.tools.data_store import DataStore

SAMPLE_CSV = Path(__file__).resolve().parents[1] / "data" / "sample" / "ventes.csv"


@pytest.fixture
def store() -> Iterator[DataStore]:
    """DataStore contenant la table `ventes` issue de data/sample/ventes.csv."""
    with DataStore([SAMPLE_CSV]) as s:
        yield s
