import streamlit as st

from festa.planning import planning_summary
from festa.ui.common import csv_data, matches, money, quantity, table
from festa.ui.navigation import navigate
from festa.ui.relations import shift_rows
from festa.ui.theme import icon, section_header
from festa.validation import STATUSES



def render_dashboard(data):
    summary = planning_summary(data)
    with st.container(key="hero"):
        st.html('<div class="festa-eyebrow" data-festa-page="Painel"><span></span>PLANEJAR JUNTOS. CELEBRAR MAIS.</div>')
        st.title("Uma boa festa começa aqui.")
        st.write("Do primeiro ingrediente à última tarefa: um lugar para organizar tudo o que a nossa festa precisa.")
        left, right = st.columns([1, 1])
        left.button("Organizar o cardápio", icon=":material/restaurant:", on_click=navigate, args=("Alimentos",))
        with right:
            st.html('<span class="festa-hero-tag">' + icon("spark", 15) + 'Feita por muitas mãos</span>')
    with st.container(key="overview-metrics"):
        cards = st.columns(4)
        for card, title, value in zip(cards, ("Alimentos cadastrados", "Porções planejadas", "Participantes", "Receita bruta potencial"),
                                       (summary["alimentos"], summary["porcoes"], summary["participantes"], money(summary["receita"]))):
            card.metric(title, value, border=True)
    st.caption("Receita estimada com a venda de todas as porções planejadas. Outras despesas não estão contempladas.")
    if not data["alimentos"] and not data["insumos"]:
        with st.container(key="panel-getting-started"):
            section_header("Sua festa começa com o primeiro passo", "Cadastre as informações e acompanhe o planejamento ganhar forma.", symbol="spark")
            st.html('<div class="festa-start-steps" data-festa-animate>'
                    '<div class="festa-start-step"><span>01 / PREPARE</span><h3>Ingredientes & cardápio</h3><p>Cadastre insumos, alimentos e suas composições.</p></div>'
                    '<div class="festa-start-step"><span>02 / CONECTE</span><h3>Doadores & contribuições</h3><p>Registre as promessas e acompanhe cada entrega.</p></div>'
                    '<div class="festa-start-step"><span>03 / ORGANIZE</span><h3>Pessoas & tarefas</h3><p>Monte a equipe e distribua os horários de trabalho.</p></div></div>')
    with st.container(key="panel-planning"):
        missing = sum(item["falta_receber"] > 0 for item in summary["insumos"])
        section_header("Cada ingrediente, no seu lugar", "Necessidades, contribuições e o que ainda precisa chegar.",
                       f"{missing} com pendência" if summary["insumos"] else "PLANEJAMENTO", "leaf")
        left, right = st.columns([2, 1], vertical_alignment="bottom")
        query = left.text_input("Buscar insumo", key="planning_search", placeholder="Encontre um ingrediente ou material…", icon=":material/search:")
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
        table(rows, "Cadastre os insumos e as composições dos alimentos para visualizar suas necessidades.", key="planning_table")
        st.caption("Inclui todos os alimentos planejados, inclusive os indisponíveis. Cada insumo mantém sua própria unidade.")
        if rows:
            st.download_button("Baixar planejamento (CSV)", csv_data(rows), "planejamento-insumos.csv", "text/csv", icon=":material/download:")
        incomplete = [food["nome"] for food in data["alimentos"] if food["porcoes"] > 0 and
                      not any(c["alimento_id"] == food["id"] for c in data["composicoes"])]
        if incomplete:
            st.warning("Alimentos com porções planejadas e sem composição: " + ", ".join(incomplete) + ". Cadastre os insumos para completar o planejamento.",
                       icon=":material/info:")
    with st.container(key="panel-donations"):
        section_header("Toda contribuição faz a diferença", "Acompanhe o caminho de cada doação até a festa.", symbol="heart")
        for card, status in zip(st.columns(3), STATUSES):
            card.metric(status, summary["situacoes"].get(status, 0), border=True)
        st.button("Acompanhar doações", icon=":material/arrow_forward:", on_click=navigate, args=("Doações",))
    with st.container(key="panel-team"):
        section_header("Quem faz acontecer", "Tarefas distribuídas, equipe alinhada.", f"{len(data['escalas'])} escalas", "clock")
        tabs = st.tabs(["Escalas de trabalho", "Todas as tarefas"])
        with tabs[0]:
            table(shift_rows(data, data["escalas"]), "As escalas aparecerão aqui depois de cadastradas.", key="dashboard_shifts")
        with tabs[1]:
            rows = [{"Tarefa": task["nome"], "Código": task["id"], "Local / setor": task["local"],
                     "Descrição": task["descricao"],
                     "Escalas": sum(shift["tarefa_id"] == task["id"] for shift in data["escalas"])}
                    for task in data["tarefas"]]
            table(rows, "Cadastre as atividades da festa na página Tarefas.", key="dashboard_tasks")
