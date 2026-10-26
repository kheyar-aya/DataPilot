"""Point d'entrée Streamlit de DataPilot.

connectée. Lancement : `uv run streamlit run app/app.py`.
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="DataPilot", page_icon="📊")
st.title("📊 DataPilot")
st.caption("Analyste de données IA multi-agents — posez une question sur votre CSV.")
st.info("Logique d'agent non encore implémentée.")
