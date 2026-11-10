import streamlit as st

from festa.models import Alimento, Insumo, Doador, Participante, Tarefa
from festa.ui.common import (
    delete_controls, matches, money, record_picker, revision, save, table,
)
from festa.validation import DONOR_TYPES, LINKS, UNITS

CATALOGS = {
    "Alimentos": (Alimento, "alimentos", "Produtos, preços e porções para a festa."),
    "Insumos": (Insumo, "insumos", "Ingredientes e embalagens, sempre na unidade cadastrada."),
    "Doadores": (Doador, "doadores", "Pessoas e organizações que contribuem com os insumos."),
    "Participantes": (Participante, "participantes", "Pessoas que vão trabalhar na festa."),
    "Tarefas": (Tarefa, "tarefas", "Atividades, locais e setores da organização."),
}


def catalog_rows(model, records):
    rows = []
    for row in records:
        item = {"Código": row["id"], "Nome": row["nome"]}
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
    left, right = st.columns([2, 1])
    query = left.text_input("Buscar por nome ou descrição", key=f"{namespace}_search")
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
    st.title(page)
    st.caption(caption)
    records = catalog_filter(model, data[namespace], namespace)
    table(catalog_rows(model, records))
    st.subheader("Gerenciar cadastro")
    record = record_picker(records, namespace)
    current = record or {}
    with st.form(f"{namespace}_form_{current.get('id', 'new')}_{revision(namespace)}"):
        values = {"nome": st.text_input("Nome *", value=current.get("nome", ""), max_chars=150)}
        if model in (Alimento, Insumo, Tarefa):
            values["descricao"] = st.text_area("Descrição", value=current.get("descricao", ""), max_chars=5000)
        if model is Alimento:
            left, right = st.columns(2)
            values["preco"] = left.text_input("Preço de venda por porção (R$) *", value=str(current.get("preco", "0,00")),
                                             help="Até duas casas decimais. Exemplo: 7,50.")
            values["porcoes"] = right.number_input("Porções planejadas *", min_value=0, max_value=999999999,
                                                    value=current.get("porcoes", 0), step=1)
            values["disponivel"] = st.checkbox("Disponível para venda", value=current.get("disponivel", True))
        elif model is Insumo:
            values["unidade"] = select_value("Unidade de medida *", UNITS, current.get("unidade"))
            st.caption("A unidade não pode ser alterada depois que o insumo tiver composições ou doações.")
        elif model is Doador:
            values["tipo"] = select_value("Tipo *", DONOR_TYPES, current.get("tipo"))
        elif model is Participante:
            values["vinculo"] = select_value("Vínculo *", LINKS, current.get("vinculo"))
        elif model is Tarefa:
            values["local"] = st.text_input("Local ou setor", value=current.get("local", ""), max_chars=150)
        if model in (Doador, Participante):
            values["contato"] = st.text_input("Contato (opcional)", value=current.get("contato", ""), max_chars=200)
            values["observacoes"] = st.text_area("Observações", value=current.get("observacoes", ""), max_chars=5000)
        submitted = st.form_submit_button("Salvar cadastro", type="primary")
    if submitted:
        save(factory, model, values, current.get("id"), namespace)
    delete_controls(factory, model, record, namespace)
    if model is Alimento:
        from festa.ui.relations import render_compositions
        st.divider()
        st.subheader("Composição de cada alimento")
        if data["alimentos"]:
            from festa.ui.common import reference_picker
            food_id = reference_picker(data["alimentos"], "Consultar composição do alimento",
                                       "food_composition_choice", current.get("id"))
            render_compositions(factory, data, food_id=food_id, namespace="food_compositions")
        else:
            st.info("Cadastre um alimento e os insumos para montar sua composição.")
