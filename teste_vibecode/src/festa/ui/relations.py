from datetime import datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

import streamlit as st

from festa.models import Composicao, Doacao, Escala, donation_status
from festa.ui.common import (
    date_text, delete_controls, lookup, matches, quantity, record_picker,
    reference_picker, relation_label, revision, save, table,
)
from festa.validation import STATUSES


def filter_parent(records, data, table_name, field, title, key):
    parents = lookup(data, table_name)
    selected = st.selectbox(title, [None, *parents],
                            format_func=lambda i: "Todos" if i is None else parents[i]["nome"] + f" · #{i}",
                            key=key)
    return records if selected is None else [row for row in records if row[field] == selected]


def render_compositions(factory, data, food_id=None, namespace="composicoes"):
    if food_id is None:
        st.title("Composições")
        st.caption("Defina quanto de cada insumo é necessário para produzir uma porção.")
    if not data["alimentos"] or not data["insumos"]:
        st.info("Cadastre pelo menos um alimento e um insumo para gerenciar composições.")
        return
    records = data["composicoes"]
    if food_id is not None:
        records = [row for row in records if row["alimento_id"] == food_id]
    else:
        records = filter_parent(records, data, "alimentos", "alimento_id", "Filtrar por alimento", f"{namespace}_food_filter")
    query = st.text_input("Buscar alimento ou insumo", key=f"{namespace}_search")
    def describe(row):
        return relation_label(data, "alimentos", row["alimento_id"]) + " / " + relation_label(data, "insumos", row["insumo_id"])
    records = [row for row in records if matches({"nome": describe(row)}, query)]
    ingredients = lookup(data, "insumos")
    table([{"Código": row["id"], "Alimento": relation_label(data, "alimentos", row["alimento_id"]),
            "Insumo": relation_label(data, "insumos", row["insumo_id"]),
            "Quantidade / porção": quantity(row["quantidade"]),
            "Unidade": ingredients[row["insumo_id"]]["unidade"]} for row in records])
    current = record_picker(records, namespace, describe)
    row = current or {}
    prefix = f"{namespace}_{row.get('id', 'new')}_{revision(namespace)}"
    left, right = st.columns(2)
    with left:
        selected_food = food_id if food_id is not None else reference_picker(
            data["alimentos"], "Alimento *", f"{prefix}_food", row.get("alimento_id"))
        if food_id is not None:
            st.caption("Alimento: " + relation_label(data, "alimentos", food_id))
    with right:
        ingredient = reference_picker(data["insumos"], "Insumo *", f"{prefix}_ingredient", row.get("insumo_id"), units=True)
    unit = ingredients[ingredient]["unidade"]
    with st.form(f"{prefix}_form_{selected_food}_{ingredient}"):
        amount = st.text_input(f"Quantidade por porção ({unit}) *", value=str(row.get("quantidade", "0")),
                               help="Maior que zero, até quatro casas decimais, sem conversão de unidade.")
        submitted = st.form_submit_button("Salvar composição", type="primary")
    if submitted:
        save(factory, Composicao, {"alimento_id": selected_food, "insumo_id": ingredient, "quantidade": amount}, row.get("id"), namespace)
    delete_controls(factory, Composicao, current, namespace)


def donation_rows(data, records):
    ingredients = lookup(data, "insumos")
    return [{"Código": row["id"], "Doador": relation_label(data, "doadores", row["doador_id"]),
             "Insumo": relation_label(data, "insumos", row["insumo_id"]), "Unidade": ingredients[row["insumo_id"]]["unidade"],
             "Prometida": quantity(row["prometida"]), "Recebida": quantity(row["recebida"]),
             "Excedente da promessa": quantity(max(row["recebida"] - row["prometida"], Decimal("0"))),
             "Situação": donation_status(row["prometida"], row["recebida"]),
             "Entrega prevista": date_text(row["entrega"]), "Observações": row["observacoes"]} for row in records]


def render_donations(factory, data):
    namespace = "doacoes"
    st.title("Doações")
    st.caption("Acompanhe os compromissos, os recebimentos parciais e os excedentes.")
    if not data["doadores"] or not data["insumos"]:
        st.info("Cadastre pelo menos um doador e um insumo antes de registrar uma doação.")
        return
    left, right = st.columns([2, 1])
    query = left.text_input("Buscar doador ou insumo", key="donation_search")
    status = right.selectbox("Situação", ["Todas", *STATUSES], key="donation_status")
    records = data["doacoes"]
    with st.expander("Mais filtros"):
        records = filter_parent(records, data, "doadores", "doador_id", "Filtrar por doador", "donation_donor_filter")
        records = filter_parent(records, data, "insumos", "insumo_id", "Filtrar por insumo", "donation_ingredient_filter")
    records = [row for row, display in zip(records, donation_rows(data, records))
               if matches(display, query) and (status == "Todas" or donation_status(row["prometida"], row["recebida"]) == status)]
    table(donation_rows(data, records))
    def describe(row):
        return relation_label(data, "doadores", row["doador_id"]) + " / " + relation_label(data, "insumos", row["insumo_id"]) + f" · doação #{row['id']}"
    current = record_picker(records, namespace, describe)
    row = current or {}
    prefix = f"{namespace}_{row.get('id', 'new')}_{revision(namespace)}"
    left, right = st.columns(2)
    with left:
        donor = reference_picker(data["doadores"], "Doador *", f"{prefix}_donor", row.get("doador_id"))
    with right:
        ingredient = reference_picker(data["insumos"], "Insumo *", f"{prefix}_ingredient", row.get("insumo_id"), units=True)
    unit = lookup(data, "insumos")[ingredient]["unidade"]
    with st.form(f"{prefix}_form_{donor}_{ingredient}"):
        left, right = st.columns(2)
        promised = left.text_input(f"Quantidade prometida ({unit}) *", value=str(row.get("prometida", "0")))
        received = right.text_input(f"Quantidade recebida ({unit}) *", value=str(row.get("recebida", "0")))
        delivery = st.date_input("Data prevista para entrega (opcional)", value=row.get("entrega"), format="DD/MM/YYYY")
        notes = st.text_area("Observações", value=row.get("observacoes", ""), max_chars=5000)
        st.caption("Use até quatro casas decimais. O recebimento pode superar a promessa.")
        submitted = st.form_submit_button("Salvar doação", type="primary")
    if submitted:
        save(factory, Doacao, {"doador_id": donor, "insumo_id": ingredient, "prometida": promised,
                              "recebida": received, "entrega": delivery, "observacoes": notes}, row.get("id"), namespace)
    delete_controls(factory, Doacao, current, namespace)


def shift_rows(data, records):
    tasks = lookup(data, "tarefas")
    return [{"Código": row["id"], "Participante": relation_label(data, "participantes", row["participante_id"]),
             "Tarefa": relation_label(data, "tarefas", row["tarefa_id"]), "Local / setor": tasks[row["tarefa_id"]]["local"],
             "Início": date_text(row["inicio"]), "Término": date_text(row["termino"]), "Observações": row["observacoes"]}
            for row in sorted(records, key=lambda row: row["inicio"])]


def render_shifts(factory, data):
    namespace = "escalas"
    st.title("Escalas de trabalho")
    st.caption("Distribua pessoas e tarefas. Todos os horários são locais de Blumenau (America/Sao_Paulo).")
    if not data["participantes"] or not data["tarefas"]:
        st.info("Cadastre pelo menos um participante e uma tarefa para montar a escala.")
        return
    query = st.text_input("Buscar participante, tarefa ou local", key="shift_search")
    left, right = st.columns(2)
    with left:
        records = filter_parent(data["escalas"], data, "participantes", "participante_id", "Filtrar por participante", "shift_person_filter")
    with right:
        records = filter_parent(records, data, "tarefas", "tarefa_id", "Filtrar por tarefa", "shift_task_filter")
    day = st.date_input("Escalas que passam pelo dia (opcional)", value=None, format="DD/MM/YYYY", key="shift_day_filter")
    records = [row for row in records if matches(shift_rows(data, [row])[0], query)]
    if day:
        start_day = datetime.combine(day, time.min)
        records = [row for row in records if row["inicio"] < start_day + timedelta(days=1) and row["termino"] > start_day]
    table(shift_rows(data, records))
    def describe(row):
        return relation_label(data, "participantes", row["participante_id"]) + " / " + relation_label(data, "tarefas", row["tarefa_id"]) + " / " + date_text(row["inicio"]) + f" · escala #{row['id']}"
    current = record_picker(records, namespace, describe)
    row = current or {}
    prefix = f"{namespace}_{row.get('id', 'new')}_{revision(namespace)}"
    left, right = st.columns(2)
    with left:
        person = reference_picker(data["participantes"], "Participante *", f"{prefix}_person", row.get("participante_id"))
    with right:
        task = reference_picker(data["tarefas"], "Tarefa *", f"{prefix}_task", row.get("tarefa_id"))
    today = datetime.now(ZoneInfo("America/Sao_Paulo")).date()
    begin = row.get("inicio", datetime.combine(today, time(18)))
    end = row.get("termino", datetime.combine(today, time(20)))
    with st.form(f"{prefix}_form_{person}_{task}"):
        left, right = st.columns(2)
        start_date = left.date_input("Data de início *", value=begin.date(), format="DD/MM/YYYY")
        start_time = left.time_input("Hora de início *", value=begin.time(), step=60)
        end_date = right.date_input("Data de término *", value=end.date(), format="DD/MM/YYYY")
        end_time = right.time_input("Hora de término *", value=end.time(), step=60)
        notes = st.text_area("Observações", value=row.get("observacoes", ""), max_chars=5000)
        submitted = st.form_submit_button("Salvar escala", type="primary")
    if submitted:
        if any(value is None for value in (start_date, start_time, end_date, end_time)):
            st.error("Informe as datas e os horários de início e término.")
        else:
            save(factory, Escala, {"participante_id": person, "tarefa_id": task,
                                  "inicio": datetime.combine(start_date, start_time),
                                  "termino": datetime.combine(end_date, end_time), "observacoes": notes}, row.get("id"), namespace)
    delete_controls(factory, Escala, current, namespace)
