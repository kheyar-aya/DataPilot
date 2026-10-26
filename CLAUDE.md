# CLAUDE.md

Ce fichier donne le contexte du projet pour Claude Code 

## Projet

**DataPilot** est un analyste de données IA multi-agents : il répond à des
questions en langage naturel sur un fichier CSV. L'orchestration des agents
utilise **LangGraph**, et les agents interrogent les données via
**function calling** (outils typés) plutôt que par génération de code libre.

Pile technique :
- **LangGraph** + **langchain-core** : orchestration des agents et function
  calling.
- **DuckDB** / **pandas** : chargement et requêtage des CSV.
- **Plotly** : génération de graphiques.
- **Streamlit** : interface utilisateur.
- **pydantic** : validation des schémas d'outils et de la configuration.
- **python-dotenv** : chargement des variables d'environnement (`.env`).

> État actuel : squelette de projet. Aucune logique d'agent, de graphe ni
> d'outil n'est encore implémentée — seule l'arborescence et la
> configuration de base existent.

## Arborescence

```
src/datapilot/
  config.py       # Settings (clé API LLM, modèle, chemin des données)
  tools/          # Outils exposés aux agents via function calling
  agents/         # Agents LangGraph (planification, analyse, réponse)
  graph/          # Graphe LangGraph orchestrant les agents
  guardrails/     # Garde-fous : validation des requêtes, limites sur les données
app/              # Interface Streamlit (app.py)
eval/             # Jeux de questions/réponses et scripts d'évaluation
tests/            # Tests pytest (un module de test par module source)
data/sample/      # Données d'exemple versionnées (ventes.csv)
```

## Conventions de code

- **Type hints** obligatoires sur toutes les fonctions/méthodes publiques
  (`from __future__ import annotations` en tête de fichier).
- **Docstrings courtes** (une à trois lignes, style impératif) sur chaque
  module, classe et fonction publique — pas de docstrings verbeuses.
- **Lint/format** : [ruff](https://docs.astral.sh/ruff/) (`uv run ruff check .`
  et `uv run ruff format .`). La configuration est dans `pyproject.toml`.
- **Tests** : chaque outil (`src/datapilot/tools/`) et chaque module de
  logique doit avoir un module de test correspondant dans `tests/`
  (`tests/test_<module>.py`), exécuté avec `uv run pytest`.
- **Gestion des dépendances** : [uv](https://docs.astral.sh/uv/) exclusivement
  (`uv add <paquet>`, `uv sync`) — ne pas utiliser pip/poetry directement.
- **Secrets** : jamais de clé API en dur ; toujours via `.env` (voir
  `.env.example`) et `datapilot.config.get_settings()`.
- **Données** : ne jamais committer de données personnelles/réelles ; seules
  les données d'exemple fictives de `data/sample/` sont versionnées (voir
  `.gitignore`).

## Commandes utiles

```bash
uv sync                      # installer les dépendances
uv run pytest                # lancer les tests
uv run ruff check .          # lint
uv run ruff format .         # formatage
uv run streamlit run app/app.py  # lancer l'interface
```
