"""Configuration applicative : chargement des variables d'environnement.

"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()


class Settings(BaseModel):
    """Paramètres de configuration de DataPilot."""

    llm_api_key: str | None = Field(
        default=None, description="Clé API du LLM utilisé par les agents."
    )
    llm_model: str = Field(
        default="claude-sonnet-5", description="Identifiant du modèle LLM à utiliser."
    )
    data_dir: Path = Field(
        default=Path("data"), description="Répertoire racine contenant les données CSV."
    )


def get_settings() -> Settings:
    """Construit les `Settings` à partir des variables d'environnement."""
    return Settings(
        llm_api_key=os.getenv("ANTHROPIC_API_KEY"),
        llm_model=os.getenv("DATAPILOT_LLM_MODEL", "claude-sonnet-5"),
        data_dir=Path(os.getenv("DATAPILOT_DATA_DIR", "data")),
    )
