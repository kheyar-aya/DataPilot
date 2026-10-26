# DataPilot

Analyste de données IA multi-agents (LangGraph + function calling) qui répond
à des questions en langage naturel sur un fichier CSV.

## Objectif

Permettre à un utilisateur de poser une question en français ou en anglais
sur un CSV tabulaire (ex. des ventes) et d'obtenir une réponse générée par
des agents orchestrés avec LangGraph, qui interrogent les données via
function calling (DuckDB/pandas) et peuvent produire des visualisations
(Plotly) présentées dans une interface Streamlit.


## Installation

```bash
uv sync
cp .env.example .env   
```

## Lancer les tests

```bash
uv run pytest
```

## Lancer l'application (squelette Streamlit)

```bash
uv run streamlit run app/app.py
```
