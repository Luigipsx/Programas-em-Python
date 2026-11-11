import streamlit as st

PAGES = {
    "Painel": ("painel", "◈"),
    "Alimentos": ("alimentos", "◒"),
    "Insumos": ("insumos", "▤"),
    "Composições": ("composicoes", "⌘"),
    "Doadores": ("doadores", "♡"),
    "Doações": ("doacoes", "↗"),
    "Participantes": ("participantes", "♧"),
    "Tarefas": ("tarefas", "☷"),
    "Escalas de trabalho": ("escalas", "◷"),
}
SECTIONS = {slug: page for page, (slug, _) in PAGES.items()}


def navigate(page):
    st.session_state["navigation"] = page


def process_route():
    section = st.query_params.get("section")
    if section not in SECTIONS:
        return
    st.session_state["navigation"] = SECTIONS[section]
    record = st.query_params.get("record", "")
    action = st.query_params.get("action", "edit")
    if section != "painel" and str(record).isdigit() and action in ("edit", "delete"):
        st.session_state[f"{section}_requested"] = (int(record), action)
    # Consome apenas os parâmetros desta aplicação.
    for key in ("section", "record", "action"):
        if key in st.query_params:
            del st.query_params[key]