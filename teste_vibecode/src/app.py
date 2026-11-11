import streamlit as st
from sqlalchemy.exc import SQLAlchemyError

from festa.database import create_tables, make_engine, make_session_factory
from festa.errors import StorageError, ValidationError
from festa.services import snapshot
from festa.ui.catalogs import CATALOGS, render_catalog
from festa.ui.dashboard import render_dashboard
from festa.ui.navigation import PAGES, process_route
from festa.ui.relations import render_compositions, render_donations, render_shifts
from festa.ui.theme import apply_theme, sidebar_brand, sidebar_footer

st.set_page_config(page_title="Festa IFC · Planejamento", page_icon="🎉", layout="wide")


@st.cache_resource
def resources():
    engine = make_engine()
    try:
        create_tables(engine)
    except Exception:
        engine.dispose()
        raise
    return make_session_factory(engine)


def main():
    apply_theme()
    process_route()
    with st.sidebar:
        sidebar_brand()
        page = st.radio(
            "Navegação", list(PAGES), key="navigation", width="stretch",
            format_func=lambda name: f"{PAGES[name][1]}  {name}",
        )
        sidebar_footer()
        st.button("Atualizar informações", icon=":material/refresh:", width="stretch")
    st.html('<div class="festa-topline"><strong>IFC Campus Blumenau</strong>'
            '<span>Planejamento colaborativo · uma festa, muitas mãos</span></div>')
    if "_flash" in st.session_state:
        st.success(st.session_state.pop("_flash"), icon=":material/check_circle:")
    try:
        factory = resources()
        data = snapshot(factory)
    except (ValidationError, StorageError) as error:
        st.error(str(error))
        st.stop()
    except (SQLAlchemyError, OSError, ValueError):
        st.error("Não foi possível iniciar o banco. Verifique as configurações com o responsável pelo sistema.")
        st.stop()
    if page == "Painel":
        render_dashboard(data)
    elif page in CATALOGS:
        render_catalog(page, factory, data)
    elif page == "Composições":
        render_compositions(factory, data)
    elif page == "Doações":
        render_donations(factory, data)
    else:
        render_shifts(factory, data)


if __name__ == "__main__":
    main()
