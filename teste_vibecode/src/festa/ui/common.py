import csv
from io import StringIO
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from html import escape
from math import ceil
import re
import unicodedata
from urllib.parse import urlencode

import streamlit as st

from festa.errors import StorageError, ValidationError
from festa.services import delete_record, save_record
from festa.ui.theme import empty_state, icon

NUMERIC_COLUMNS = {
    "Código", "Preço / porção", "Porções", "Quantidade / porção", "Prometida",
    "Recebida", "Excedente da promessa", "Necessária", "Sem compromisso",
    "Falta receber", "Excedente prometido", "Excedente recebido", "Escalas",
}
STATUS_CLASSES = {
    "Disponível": "good", "Recebida": "good",
    "Pendente": "waiting", "Parcialmente recebida": "partial",
    "Indisponível": "neutral",
}


def number(value):
    return format(Decimal(value), "f").rstrip("0").rstrip(",").rstrip(".") if Decimal(value) % 1 else str(int(value))


def quantity(value):
    return number(value).replace(".", ",")


def money(value):
    return "R$ " + format(value, ",.2f").replace(",", "_").replace(".", ",").replace("_", ".")


def fold(text):
    return "".join(c for c in unicodedata.normalize("NFKD", str(text).casefold()) if not unicodedata.combining(c))


def numeric_sort(value):
    if isinstance(value, (int, Decimal)):
        return Decimal(value)
    raw = str(value).replace("R$", "").replace(" ", "").strip()
    if "," in raw:
        raw = raw.replace(".", "").replace(",", ".")
    try:
        return Decimal(raw)
    except InvalidOperation:
        return Decimal("0")


def sorted_rows(rows, column, reverse=False):
    if column in NUMERIC_COLUMNS:
        key = lambda row: numeric_sort(row[column])
    elif column in ("Início", "Término", "Entrega prevista"):
        def key(row):
            for pattern in ("%d/%m/%Y %H:%M", "%d/%m/%Y"):
                try:
                    return datetime.strptime(str(row[column]), pattern)
                except ValueError:
                    pass
            return datetime.min
    else:
        key = lambda row: fold(row[column])
    return sorted(rows, key=key, reverse=reverse)


def cell_html(column, value):
    text = escape(str(value)) if value not in (None, "") else "—"
    if column == "Situação" and value in STATUS_CLASSES:
        return f'<span class="festa-status festa-status-{STATUS_CLASSES[value]}">{text}</span>'
    return text


def table_html(rows, columns, namespace=None, start=1, total=None):
    """HTML sem conteúdo executável proveniente dos registros."""
    total = len(rows) if total is None else total
    output = ['<div class="festa-table-shell" data-festa-animate><div class="festa-table-scroll" '
              'role="region" aria-label="Tabela de registros" tabindex="0"><table class="festa-table">'
              '<caption class="festa-sr-only">Registros cadastrados. Em telas menores, cada linha aparece como um cartão.</caption><thead><tr>']
    for column in columns:
        cls = ' class="festa-number"' if column in NUMERIC_COLUMNS else ""
        output.append(f'<th scope="col"{cls}>{escape(column)}</th>')
    if namespace:
        output.append('<th scope="col">Ações</th>')
    output.append("</tr></thead><tbody>")
    for row in rows:
        output.append("<tr>")
        for column in columns:
            classes = []
            if column in NUMERIC_COLUMNS:
                classes.append("festa-number")
            if column in ("Descrição", "Observações"):
                classes.append("festa-note")
            if column in ("Falta receber", "Sem compromisso") and numeric_sort(row[column]) > 0:
                classes.append("festa-shortage")
            output.append(f'<td data-label="{escape(column)}" class="{" ".join(classes)}">{cell_html(column, row[column])}</td>')
        if namespace:
            output.append('<td class="festa-actions-cell" data-label="Ações"><div class="festa-row-actions">')
            for action, title, symbol in (("edit", "Editar registro", "edit"), ("delete", "Excluir registro", "trash")):
                route_namespace = "composicoes" if namespace == "food_compositions" else namespace
                params = urlencode({"section": route_namespace, "record": row["Código"], "action": action})
                anchor = "delete" if action == "delete" else "editor"
                url = escape("?" + params + f"#{anchor}-{route_namespace}", quote=True)
                extra = " festa-row-delete" if action == "delete" else ""
                output.append(f'<a class="festa-row-action{extra}" href="{url}" target="_self" '
                              f'aria-label="{title} {row["Código"]}" title="{title}">'
                              f'{icon(symbol, 15)}<span class="festa-sr-only">{title}</span></a>')
            output.append("</div></td>")
        output.append("</tr>")
    finish = start + len(rows) - 1
    action_hint = "Editar abre o formulário. Excluir pede confirmação." if namespace else "Quantidades e informações por registro."
    output.append('</tbody></table></div><div class="festa-table-meta">'
                  f'<span>Exibindo <strong>{start}–{finish}</strong> de <strong>{total}</strong></span>'
                  f'<span>{action_hint}</span></div></div>')
    return "".join(output)



def csv_data(rows):
    output = StringIO()
    if rows:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]), delimiter=";")
        writer.writeheader()
        for row in rows:
            writer.writerow({
                key: "'" + value if isinstance(value, str) and value.startswith(("=", "+", "-", "@")) else value
                for key, value in row.items()
            })
    return output.getvalue().encode("utf-8-sig")


def table(rows, empty="Nenhum registro encontrado.", *, key, namespace=None):
    if not rows:
        empty_state("Um espaço para começar", empty)
        return
    columns = list(rows[0])
    toolbar = st.columns([1, 1])
    with toolbar[0].popover("Ordenar e organizar", icon=":material/sort:"):
        order = st.selectbox("Ordenar por", columns, key=f"{key}_sort")
        descending = st.checkbox("Ordem decrescente", key=f"{key}_descending")
        page_size = st.selectbox("Registros por página", [10, 20, 50], key=f"{key}_size")
    ordered = sorted_rows(rows, order, descending)
    with toolbar[1].popover("Exportar dados", icon=":material/download:"):
        st.caption("Baixe todos os registros encontrados, incluindo outras páginas.")
        st.download_button("Baixar tabela (CSV)", csv_data(ordered), f"{key}.csv",
                           "text/csv", key=f"{key}_download", icon=":material/download:")
    pages = max(ceil(len(ordered) / page_size), 1)
    page_key = f"{key}_page"
    current = st.session_state.get(page_key, 1)
    if current > pages:

        st.session_state[page_key] = 1
    page = 1
    if pages > 1:
        left, right = st.columns([1, 3])
        page = left.number_input("Página", min_value=1, max_value=pages, value=1, step=1, key=page_key)
        right.caption(f"{pages} páginas · escolha a quantidade de registros em “Ordenar e organizar”.")
    offset = (page - 1) * page_size
    st.html(table_html(ordered[offset:offset + page_size], columns, namespace, offset + 1, len(ordered)))


def matches(row, query):
    return fold(query.strip()) in fold(" ".join(str(value) for value in row.values()))


def label(row):
    return f"{row['nome']} · #{row['id']}"


def lookup(data, table_name):
    return {row["id"]: row for row in data[table_name]}


def relation_label(data, table_name, record_id):
    row = lookup(data, table_name)[record_id]
    return label(row)


def revision(namespace):
    return st.session_state.get(f"{namespace}_revision", 0)


def saved(namespace, message):
    st.session_state[f"{namespace}_revision"] = revision(namespace) + 1
    st.session_state.pop(f"{namespace}_action", None)
    st.session_state["_flash"] = message
    st.rerun()


def save(factory, model, values, record_id, namespace):
    try:
        with st.spinner("Salvando informações..."):
            save_record(factory, model, values, record_id)
    except (ValidationError, StorageError) as error:
        st.error(str(error), icon=":material/error:")
    else:
        saved(namespace, "Registro salvo com sucesso.")


def record_picker(rows, namespace, formatter=label):
    records = {row["id"]: row for row in rows}
    key = f"{namespace}_pick_{revision(namespace)}"
    requested = st.session_state.pop(f"{namespace}_requested", None)
    if requested and requested[0] in records:
        st.session_state[key] = requested[0]
        st.session_state[f"{namespace}_action"] = requested[1]
    selected = st.selectbox(
        "Cadastrar ou editar", [None, *records],
        format_func=lambda value: "＋ Novo registro" if value is None else formatter(records[value]),
        key=key, help="Escolha um registro para editar ou use as ações na tabela.",
    )
    return records.get(selected)


def reference_picker(rows, title, key, current=None, units=False):
    records = {row["id"]: row for row in rows}
    options = list(records)
    def display(record_id):
        row = records[record_id]
        return label(row) + (f" ({row['unidade']})" if units else "")
    return st.selectbox(title, options, index=options.index(current) if current in options else 0,
                        format_func=display, key=key)


def delete_controls(factory, model, record, namespace):
    if record is None:
        return
    opened = st.session_state.get(f"{namespace}_action") == "delete"
    with st.expander("Excluir este registro", expanded=opened, icon=":material/delete_outline:"):
        focus = ' data-festa-focus="true"' if opened else ""
        st.html(f'<div id="delete-{escape(namespace)}" class="festa-danger-marker"{focus}></div>')
        st.caption("A exclusão só será permitida se o registro não tiver vínculos em outros cadastros.")
        with st.form(f"{namespace}_delete_{record['id']}_{revision(namespace)}", border=False):
            confirmed = st.checkbox("Confirmo a exclusão deste registro.")
            submitted = st.form_submit_button("Excluir definitivamente", icon=":material/delete_outline:")
        if submitted:
            if not confirmed:
                st.warning("Marque a confirmação antes de excluir.", icon=":material/info:")
            else:
                try:
                    with st.spinner("Excluindo registro..."):
                        delete_record(factory, model, record["id"])
                except (ValidationError, StorageError) as error:
                    st.error(str(error), icon=":material/error:")
                else:
                    saved(namespace, "Registro excluído com sucesso.")


def date_text(value):
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y %H:%M")
    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")
    return "—"
