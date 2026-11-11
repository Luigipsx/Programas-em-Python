import streamlit as st

from festa.models import Alimento, Insumo, Doador, Participante, Tarefa
from festa.ui.common import (
    delete_controls, matches, money, record_picker, revision, save, table,
)
from festa.ui.theme import editor_header, page_header, section_header
from festa.validation import DONOR_TYPES, LINKS, UNITS

CATALOGS = {
    "Alimentos": (Alimento, "alimentos", "O cardápio começa aqui. Defina produtos, preços e porções."),
    "Insumos": (Insumo, "insumos", "Cada ingrediente conta. Organize materiais e suas unidades de medida."),
    "Doadores": (Doador, "doadores", "Conheça quem contribui para fazer a festa acontecer."),
    "Participantes": (Participante, "participantes", "Uma equipe, muitas habilidades. Organize as pessoas da festa."),
    "Tarefas": (Tarefa, "tarefas", "Do primeiro preparo à última arrumação, cada atividade tem seu lugar."),
}
NOUNS = {Alimento: "alimento", Insumo: "insumo", Doador: "doador", Participante: "participante", Tarefa: "tarefa"}


def catalog_rows(model, records):
    rows = []
    for row in records:
        item = {"Nome": row["nome"], "Código": row["id"]}
        if model is Alimento:
            item.update({"Preço / porção": money(row["preco"]), "Porções": row["porcoes"],
                         "Situação": "Disponível" if row["disponivel"] else "Indisponível",
                         "Descrição": row["descricao"]})
        elif model is Insumo:
            item.update({"Unidade": row["unidade"], "Descrição": row["descricao"]})
        elif model is Doador:
            item.update({"Tipo": row["tipo"], "Contato": row["contato"], "Observações": row["observacoes"]})
        elif model is Participante:
            item.update({"Vínculo": row["vinculo"], "Contato": row["contato"], "Observações": row["observacoes"]})
        else:
            item.update({"Local / setor": row["local"], "Descrição": row["descricao"]})
        rows.append(item)
    return rows


def catalog_filter(model, records, namespace):
    left, right = st.columns([2, 1], vertical_alignment="bottom")
    query = left.text_input("Buscar por nome ou descrição", key=f"{namespace}_search",
                            placeholder="Digite para encontrar um registro…", icon=":material/search:")
    records = [row for row in records if matches(row, query)]
    field, options = None, []
    if model is Alimento:
        selected = right.selectbox("Situação", ["Todas", "Disponível", "Indisponível"], key=f"{namespace}_filter")
        if selected != "Todas":
            records = [row for row in records if row["disponivel"] == (selected == "Disponível")]
    else:
        if model is Insumo:
            field, options = "unidade", list(UNITS)
        elif model is Doador:
            field, options = "tipo", list(DONOR_TYPES)
        elif model is Participante:
            field, options = "vinculo", list(LINKS)
        elif model is Tarefa:
            field, options = "local", sorted({r["local"] for r in records if r["local"]})
        selected = right.selectbox("Filtrar por " + {"unidade": "unidade", "tipo": "tipo", "vinculo": "vínculo", "local": "local"}[field],
                                   ["Todos", *options], key=f"{namespace}_filter")
        if selected != "Todos":
            records = [row for row in records if row[field] == selected]
    return records


def select_value(title, options, value):
    return st.selectbox(title, options, index=options.index(value) if value in options else 0)


def render_catalog(page, factory, data):
    model, namespace, caption = CATALOGS[page]
    page_header(page, caption, "CADASTROS · ORGANIZAÇÃO")
    with st.container(key=f"panel-{namespace}"):
        section_header("Seus registros", "Busque, consulte e gerencie os cadastros.", f"{len(data[namespace])} registros")
        records = catalog_filter(model, data[namespace], namespace)
        table(catalog_rows(model, records), key=f"{namespace}_table", namespace=namespace)
    with st.container(key=f"editor-{namespace}"):
        record = record_picker(records, namespace)
        current = record or {}
        editor_header(record, namespace, NOUNS[model])
        with st.form(f"{namespace}_form_{current.get('id', 'new')}_{revision(namespace)}", border=False):
            values = {}
            if model in (Doador, Participante, Insumo):
                left, right = st.columns([2, 1])
                values["nome"] = left.text_input("Nome *", value=current.get("nome", ""), max_chars=150,
                                                placeholder="Como você quer identificar este cadastro?")
                with right:
                    if model is Insumo:
                        values["unidade"] = select_value("Unidade de medida *", UNITS, current.get("unidade"))
                    elif model is Doador:
                        values["tipo"] = select_value("Tipo *", DONOR_TYPES, current.get("tipo"))
                    else:
                        values["vinculo"] = select_value("Vínculo *", LINKS, current.get("vinculo"))
            else:
                values["nome"] = st.text_input("Nome *", value=current.get("nome", ""), max_chars=150,
                                               placeholder="Como você quer identificar este cadastro?")
            if model is Alimento:
                left, right = st.columns(2)
                values["preco"] = left.text_input("Preço de venda por porção (R$) *", value=str(current.get("preco", "0,00")),
                                                 help="Até duas casas decimais. Exemplo: 7,50.")
                values["porcoes"] = right.number_input("Porções planejadas *", min_value=0, max_value=999999999,
                                                        value=current.get("porcoes", 0), step=1)
                values["disponivel"] = st.checkbox("Disponível para venda", value=current.get("disponivel", True))
            if model in (Alimento, Insumo, Tarefa):
                values["descricao"] = st.text_area("Descrição", value=current.get("descricao", ""), max_chars=5000,
                                                    placeholder="Detalhes que ajudam a equipe a se organizar (opcional).")
            if model is Insumo:
                st.caption("A unidade fica bloqueada enquanto houver composições ou doações vinculadas.")
            elif model is Tarefa:
                values["local"] = st.text_input("Local ou setor", value=current.get("local", ""), max_chars=150,
                                                placeholder="Ex.: cozinha, pátio ou atendimento")
            if model in (Doador, Participante):
                values["contato"] = st.text_input("Contato (opcional)", value=current.get("contato", ""), max_chars=200,
                                                   placeholder="Telefone, e-mail ou outra forma de contato")
                values["observacoes"] = st.text_area("Observações", value=current.get("observacoes", ""), max_chars=5000,
                                                      placeholder="Informações úteis para a organização (opcional).")
            submitted = st.form_submit_button("Salvar cadastro", type="primary", icon=":material/check:", width="stretch")
        if submitted:
            save(factory, model, values, current.get("id"), namespace)
        delete_controls(factory, model, record, namespace)
    if model is Alimento:
        from festa.ui.relations import render_compositions
        with st.container(key="panel-food-composition"):
            section_header("Composição de cada alimento", "Monte a receita e calcule o que será necessário.", symbol="leaf")
            if data["alimentos"]:
                from festa.ui.common import reference_picker
                food_id = reference_picker(data["alimentos"], "Consultar composição do alimento",
                                           "food_composition_choice", current.get("id"))
                render_compositions(factory, data, food_id=food_id, namespace="food_compositions")
            else:
                st.info("Cadastre um alimento e os insumos para montar sua composição.")
