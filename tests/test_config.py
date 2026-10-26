"""Tests pour datapilot.config."""

from pathlib import Path

from datapilot.config import Settings, get_settings


def test_get_settings_returns_settings_instance() -> None:
    """get_settings() renvoie bien une instance de Settings."""
    settings = get_settings()
    assert isinstance(settings, Settings)


def test_get_settings_default_model(monkeypatch) -> None:
    """Le modèle LLM par défaut est utilisé quand la variable d'env est absente."""
    monkeypatch.delenv("DATAPILOT_LLM_MODEL", raising=False)
    settings = get_settings()
    assert settings.llm_model == "claude-sonnet-5"


def test_get_settings_reads_env(monkeypatch) -> None:
    """Les variables d'environnement surchargent les valeurs par défaut."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-123")
    monkeypatch.setenv("DATAPILOT_LLM_MODEL", "modele-test")
    monkeypatch.setenv("DATAPILOT_DATA_DIR", "data")
    settings = get_settings()
    assert settings.llm_api_key == "sk-test-123"
    assert settings.llm_model == "modele-test"
    assert settings.data_dir == Path("data")
