import streamlit as st
from sqlalchemy.exc import SQLAlchemyError

from festa.database import create_tables, make_engine, make_session_factory
from festa.errors import StorageError, ValidationError
from festa.services import snapshot
from festa.ui.catalogs import CATALOGS, render_catalog
from festa.ui.dashboard import render_dashboard
from festa.ui.relations import render_compositions, render_donations, render_shifts

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
    with st.sidebar:
        st.markdown("## 🎉 Festa IFC")
        st.caption("CAMPUS BLUMENAU")
        page = st.radio("Navegação", ["Painel", "Alimentos", "Insumos", "Composições", "Doadores",
                                      "Doações", "Participantes", "Tarefas", "Escalas de trabalho"])
        st.divider()
        st.caption("Uma festa, muitas mãos.\n\nOrganize os preparativos em um só lugar.")
        st.button("Atualizar informações", width="stretch")
    if "_flash" in st.session_state:
        st.success(st.session_state.pop("_flash"))
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
