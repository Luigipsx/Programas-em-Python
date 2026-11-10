import csv
from io import StringIO

import streamlit as st

from festa.planning import planning_summary
from festa.ui.common import matches, money, quantity, table
from festa.ui.relations import shift_rows
from festa.validation import STATUSES


def csv_data(rows):
    output = StringIO()
    if rows:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]), delimiter=";")
        writer.writeheader()
        for row in rows:
            # Neutraliza fórmulas ao abrir conteúdo digitado por usuários em planilhas.
            writer.writerow({key: "'" + value if isinstance(value, str) and value.startswith(("=", "+", "-", "@")) else value
                             for key, value in row.items()})
    return output.getvalue().encode("utf-8-sig")


def render_dashboard(data):
    summary = planning_summary(data)
    st.caption("IFC CAMPUS BLUMENAU  /  ORGANIZAÇÃO DA FESTA")
    st.title("Tudo pronto para a festa?")
    st.write("Planeje o cardápio, acompanhe as doações e organize quem faz acontecer.")
    cards = st.columns(4)
    for card, title, value in zip(cards, ("Alimentos cadastrados", "Porções planejadas", "Participantes", "Receita bruta potencial"),
                                   (summary["alimentos"], summary["porcoes"], summary["participantes"], money(summary["receita"]))):
        card.metric(title, value, border=True)
    st.caption("Receita estimada com a venda de todas as porções planejadas. Outras despesas não estão contempladas.")
    if not data["alimentos"] and not data["insumos"]:
        with st.container(border=True):
            st.subheader("Comece a organizar")
            st.write("1. Cadastre os insumos e suas unidades.\n2. Defina alimentos, porções e composições.\n3. Registre doações, participantes e escalas.")
    st.subheader("Planejamento dos insumos")
    st.caption("Inclui todos os alimentos, inclusive os indisponíveis para venda. Cada quantidade usa a unidade do próprio insumo.")
    left, right = st.columns([2, 1])
    query = left.text_input("Buscar insumo", key="planning_search")
    only_missing = right.checkbox("Somente com recebimento incompleto")
    rows = []
    for item in summary["insumos"]:
        if not matches({"nome": item["nome"]}, query) or (only_missing and item["falta_receber"] == 0):
            continue
        rows.append({"Insumo": item["nome"], "Código": item["id"], "Unidade": item["unidade"],
                     "Necessária": quantity(item["necessaria"]), "Prometida": quantity(item["prometida"]),
                     "Recebida": quantity(item["recebida"]), "Sem compromisso": quantity(item["sem_compromisso"]),
                     "Falta receber": quantity(item["falta_receber"]), "Excedente prometido": quantity(item["excedente_prometido"]),
                     "Excedente recebido": quantity(item["excedente_recebido"])})
    table(rows, "Nenhum insumo para exibir com estes filtros.")
    if rows:
        st.download_button("Baixar planejamento (CSV)", csv_data(rows), "planejamento-insumos.csv", "text/csv")
    incomplete = [food["nome"] for food in data["alimentos"] if food["porcoes"] > 0 and
                  not any(c["alimento_id"] == food["id"] for c in data["composicoes"])]
    if incomplete:
        st.warning("Alimentos com porções planejadas e sem composição: " + ", ".join(incomplete) + ". Cadastre os insumos para completar o planejamento.")
    st.subheader("Andamento das doações")
    for card, status in zip(st.columns(3), STATUSES):
        card.metric(status, summary["situacoes"].get(status, 0), border=True)
    st.subheader("Tarefas e equipe")
    tabs = st.tabs(["Escalas de trabalho", "Todas as tarefas"])
    with tabs[0]:
        table(shift_rows(data, data["escalas"]), "As escalas aparecerão aqui depois de cadastradas.")
    with tabs[1]:
        rows = [{"Código": task["id"], "Tarefa": task["nome"], "Local / setor": task["local"],
                 "Descrição": task["descricao"],
                 "Escalas": sum(shift["tarefa_id"] == task["id"] for shift in data["escalas"])}
                for task in data["tarefas"]]
        table(rows, "Cadastre as atividades da festa na página Tarefas.")
