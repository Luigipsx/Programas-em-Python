from datetime import datetime
from pathlib import Path

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from festa.database import create_tables, make_engine, make_session_factory
from festa.models import Alimento, Insumo, Composicao, Doador, Doacao, Participante, Tarefa, Escala
from festa.services import save_record, snapshot


@pytest.fixture
def ui(monkeypatch, tmp_path):
    path = tmp_path / "ui.db"
    monkeypatch.setenv("DB_BACKEND", "sqlite")
    monkeypatch.setenv("SQLITE_PATH", str(path))
    st.cache_resource.clear()
    engine = make_engine("sqlite+pysqlite:///" + path.as_posix())
    create_tables(engine)
    factory = make_session_factory(engine)
    app = AppTest.from_file(str(Path(__file__).parents[1] / "app.py"), default_timeout=20)
    yield app, factory
    st.cache_resource.clear()
    engine.dispose()


def element(elements, label):
    return next(item for item in elements if item.label == label)


def navigate(app, page):
    app.sidebar.radio[0].set_value(page).run()
    assert not app.exception


def test_all_empty_pages(ui):
    app, _ = ui
    app.run()
    assert not app.exception
    assert app.metric[0].value == "0"
    for page in ("Alimentos", "Insumos", "Composições", "Doadores", "Doações",
                 "Participantes", "Tarefas", "Escalas de trabalho", "Painel"):
        navigate(app, page)


def test_food_crud_validation_and_delete_confirmation(ui):
    app, factory = ui
    app.run()
    navigate(app, "Alimentos")
    element(app.button, "Salvar cadastro").click().run()
    assert app.error and "Nome" in app.error[0].value
    element(app.text_input, "Nome *").set_value("Pastel")
    element(app.text_input, "Preço de venda por porção (R$) *").set_value("7,50")
    element(app.number_input, "Porções planejadas *").set_value(40)
    element(app.button, "Salvar cadastro").click().run()
    assert not app.exception
    assert snapshot(factory)["alimentos"][0]["porcoes"] == 40
    record_id = snapshot(factory)["alimentos"][0]["id"]
    element(app.selectbox, "Cadastrar ou editar").set_value(record_id).run()
    element(app.text_input, "Preço de venda por porção (R$) *").set_value("8,00")
    element(app.button, "Salvar cadastro").click().run()
    assert str(snapshot(factory)["alimentos"][0]["preco"]) == "8.00"
    element(app.selectbox, "Cadastrar ou editar").set_value(record_id).run()
    element(app.button, "Excluir definitivamente").click().run()
    assert app.warning
    assert len(snapshot(factory)["alimentos"]) == 1
    element(app.checkbox, "Confirmo a exclusão deste registro.").check()
    element(app.button, "Excluir definitivamente").click().run()
    assert not app.exception
    assert snapshot(factory)["alimentos"] == []


def seed(factory):
    iid = save_record(factory, Insumo, {"nome": "Farinha", "unidade": "kg"})
    fid = save_record(factory, Alimento, {"nome": "Pastel", "preco": "5", "porcoes": 20, "disponivel": True})
    did = save_record(factory, Doador, {"nome": "Ana", "tipo": "pessoa"})
    pid = save_record(factory, Participante, {"nome": "Bia", "vinculo": "aluno"})
    tid = save_record(factory, Tarefa, {"nome": "Preparo", "local": "Cozinha"})
    return iid, fid, did, pid, tid


def test_relationship_forms_planning_and_restrictions(ui):
    app, factory = ui
    iid, fid, did, pid, tid = seed(factory)
    app.run()
    navigate(app, "Composições")
    element(app.text_input, "Quantidade por porção (kg) *").set_value("0,25")
    element(app.button, "Salvar composição").click().run()
    assert not app.exception
    assert len(snapshot(factory)["composicoes"]) == 1
    navigate(app, "Doações")
    element(app.text_input, "Quantidade prometida (kg) *").set_value("6")
    element(app.text_input, "Quantidade recebida (kg) *").set_value("7")
    element(app.button, "Salvar doação").click().run()
    assert not app.exception
    assert len(snapshot(factory)["doacoes"]) == 1
    navigate(app, "Escalas de trabalho")
    element(app.button, "Salvar escala").click().run()
    assert not app.exception
    assert len(snapshot(factory)["escalas"]) == 1
    element(app.button, "Salvar escala").click().run()
    assert app.error and "sobreposição" in app.error[0].value
    navigate(app, "Insumos")
    element(app.selectbox, "Cadastrar ou editar").set_value(iid).run()
    element(app.selectbox, "Unidade de medida *").set_value("g")
    element(app.button, "Salvar cadastro").click().run()
    assert app.error and "unidade" in app.error[0].value
    element(app.checkbox, "Confirmo a exclusão deste registro.").check()
    element(app.button, "Excluir definitivamente").click().run()
    assert app.error and "vínculos" in app.error[0].value
    navigate(app, "Painel")
    assert app.metric[1].value == "20"
    assert app.metric[3].value == "R$ 100,00"
    assert not app.exception
    for page in ("Alimentos", "Doadores", "Participantes", "Tarefas"):
        navigate(app, page)
