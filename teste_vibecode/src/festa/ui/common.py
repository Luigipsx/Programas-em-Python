from datetime import date, datetime
from decimal import Decimal
import unicodedata

import streamlit as st

from festa.errors import StorageError, ValidationError
from festa.services import delete_record, save_record


def number(value):
    return format(Decimal(value), "f").rstrip("0").rstrip(",").rstrip(".") if Decimal(value) % 1 else str(int(value))


def quantity(value):
    return number(value).replace(".", ",")


def money(value):
    return "R$ " + format(value, ",.2f").replace(",", "_").replace(".", ",").replace("_", ".")


def table(rows, empty="Nenhum registro encontrado."):
    if not rows:
        st.info(empty)
        return
    st.dataframe(rows, hide_index=True, width="stretch")


def fold(text):
    return "".join(c for c in unicodedata.normalize("NFKD", str(text).casefold()) if not unicodedata.combining(c))


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
    st.session_state["_flash"] = message
    st.rerun()


def save(factory, model, values, record_id, namespace):
    try:
        save_record(factory, model, values, record_id)
    except (ValidationError, StorageError) as error:
        st.error(str(error))
    else:
        saved(namespace, "Registro salvo com sucesso.")


def record_picker(rows, namespace, formatter=label):
    records = {row["id"]: row for row in rows}
    selected = st.selectbox(
        "Cadastrar ou editar", [None, *records],
        format_func=lambda value: "＋ Novo registro" if value is None else formatter(records[value]),
        key=f"{namespace}_pick_{revision(namespace)}",
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
    with st.expander("Excluir este registro"):
        st.caption("A exclusão só será permitida se o registro não tiver vínculos em outros cadastros.")
        with st.form(f"{namespace}_delete_{record['id']}_{revision(namespace)}"):
            confirmed = st.checkbox("Confirmo a exclusão deste registro.")
            submitted = st.form_submit_button("Excluir definitivamente")
        if submitted:
            if not confirmed:
                st.warning("Marque a confirmação antes de excluir.")
            else:
                try:
                    delete_record(factory, model, record["id"])
                except (ValidationError, StorageError) as error:
                    st.error(str(error))
                else:
                    saved(namespace, "Registro excluído com sucesso.")


def date_text(value):
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y %H:%M")
    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")
    return "—"
