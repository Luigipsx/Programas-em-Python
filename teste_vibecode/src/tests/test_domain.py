from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from decimal import Decimal
from threading import Barrier

import pytest
from sqlalchemy import event, select, text
from sqlalchemy.dialects import mysql
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.schema import CreateTable

from festa.database import make_engine, make_session_factory, transaction
from festa.errors import StorageError, ValidationError
from festa.models import Alimento, Insumo, Composicao, Doador, Doacao, Participante, Tarefa, Escala, donation_status
from festa.planning import planning_summary
from festa.services import delete_record, save_record, snapshot

D = Decimal


def ingredient(factory, name="Farinha", unit="kg"):
    return save_record(factory, Insumo, {"nome": name, "unidade": unit})


def food(factory, name="Pastel", portions=10, price="7.50", available=True):
    return save_record(factory, Alimento, {"nome": name, "preco": price, "porcoes": portions, "disponivel": available})


def team(factory):
    person = save_record(factory, Participante, {"nome": "Ana", "vinculo": "aluno"})
    task = save_record(factory, Tarefa, {"nome": "Preparo"})
    return person, task


def shift(person, task, start=18, end=20):
    return {"participante_id": person, "tarefa_id": task,
            "inicio": datetime(2026, 12, 1, start), "termino": datetime(2026, 12, 1, end)}


def test_planning_multiple_foods_donors_and_units(factory):
    flour = ingredient(factory)
    cups = ingredient(factory, "Copos", "unidade")
    oil = ingredient(factory, "Óleo", "L")
    unused = ingredient(factory, "Sal", "g")
    a = food(factory, portions=10, price="0.10")
    b = food(factory, "Bolo", portions=20, price="0.20", available=False)
    for fid, iid, amount in ((a, flour, "0.2"), (b, flour, "0.15"), (a, cups, "1"), (a, oil, "0.1")):
        save_record(factory, Composicao, {"alimento_id": fid, "insumo_id": iid, "quantidade": amount})
    donors = [save_record(factory, Doador, {"nome": name, "tipo": "pessoa"}) for name in ("Ana", "Bia")]
    for donor, iid, promised, received in (
        (donors[0], flour, "3", "2"), (donors[1], flour, "4", "6"),
        (donors[0], cups, "4", "0"), (donors[1], oil, "1", "0.5"),
    ):
        save_record(factory, Doacao, {"doador_id": donor, "insumo_id": iid, "prometida": promised, "recebida": received})
    report = planning_summary(snapshot(factory))
    rows = {row["id"]: row for row in report["insumos"]}
    assert rows[flour]["necessaria"] == D("5")
    assert rows[flour]["prometida"] == D("7")
    assert rows[flour]["recebida"] == D("8")
    assert rows[flour]["sem_compromisso"] == rows[flour]["falta_receber"] == 0
    assert rows[flour]["excedente_prometido"] == 2
    assert rows[flour]["excedente_recebido"] == 3
    assert rows[cups]["sem_compromisso"] == 6
    assert rows[cups]["falta_receber"] == 10
    assert rows[oil]["falta_receber"] == D("0.5")
    assert rows[unused]["necessaria"] == 0
    assert report["receita"] == D("5.00")
    assert isinstance(report["receita"], D)
    assert report["porcoes"] == 30  # Inclui também os indisponíveis, como especificado.
    assert report["situacoes"] == {"Pendente": 1, "Parcialmente recebida": 2, "Recebida": 1}


@pytest.mark.parametrize("promised,received,status", [
    ("5", "0", "Pendente"), ("5", "2", "Parcialmente recebida"),
    ("5", "5", "Recebida"), ("5", "8", "Recebida"),
    ("0", "0", "Pendente"), ("0", "1", "Recebida"),
])
def test_donation_status(promised, received, status):
    assert donation_status(D(promised), D(received)) == status
    donation = Doacao(prometida=D(promised), recebida=D(received))
    assert donation.situacao == status
    assert donation.excedente == max(D(received) - D(promised), D("0"))


def test_composition_unique_edit_unit_lock_and_restrict_delete(factory):
    iid = ingredient(factory)
    fid = food(factory)
    values = {"alimento_id": fid, "insumo_id": iid, "quantidade": "0.2"}
    cid = save_record(factory, Composicao, values)
    with pytest.raises(ValidationError, match="já está"):
        save_record(factory, Composicao, values)
    save_record(factory, Composicao, dict(values, quantidade="0.3"), cid)
    assert snapshot(factory)["composicoes"][0]["quantidade"] == D("0.3")
    with pytest.raises(ValidationError, match="unidade não pode mudar"):
        save_record(factory, Insumo, {"nome": "Farinha", "unidade": "g"}, iid)
    for model, rid in ((Insumo, iid), (Alimento, fid)):
        with pytest.raises(ValidationError, match="composições"):
            delete_record(factory, model, rid)
    delete_record(factory, Composicao, cid)
    save_record(factory, Insumo, {"nome": "Farinha", "unidade": "g"}, iid)
    delete_record(factory, Alimento, fid)
    delete_record(factory, Insumo, iid)
    assert snapshot(factory)["insumos"] == []


def test_donation_links_and_independent_roles(factory):
    iid = ingredient(factory)
    did = save_record(factory, Doador, {"nome": "Ana", "tipo": "pessoa"})
    pid = save_record(factory, Participante, {"nome": "Ana", "vinculo": "aluno"})
    donation_id = save_record(factory, Doacao, {"doador_id": did, "insumo_id": iid, "prometida": "1", "recebida": "2"})
    delete_record(factory, Participante, pid)
    for model, rid in ((Doador, did), (Insumo, iid)):
        with pytest.raises(ValidationError, match="doações"):
            delete_record(factory, model, rid)
    with pytest.raises(ValidationError, match="unidade não pode mudar"):
        save_record(factory, Insumo, {"nome": "Farinha", "unidade": "g"}, iid)
    delete_record(factory, Doacao, donation_id)
    delete_record(factory, Doador, did)


@pytest.mark.parametrize("start,end", [(18, 19), (19, 21), (17, 19), (17, 21), (18, 20)])
def test_shift_overlap(factory, start, end):
    person, task = team(factory)
    save_record(factory, Escala, shift(person, task))
    with pytest.raises(ValidationError, match="sobreposição"):
        save_record(factory, Escala, shift(person, task, start, end))


def test_shift_boundaries_edit_different_people_and_deletion(factory):
    person, task = team(factory)
    sid = save_record(factory, Escala, shift(person, task))
    save_record(factory, Escala, shift(person, task), sid)  # Não conflita consigo.
    save_record(factory, Escala, shift(person, task, 20, 21))
    save_record(factory, Escala, shift(person, task, 17, 18))
    other = save_record(factory, Participante, {"nome": "Bia", "vinculo": "servidor"})
    save_record(factory, Escala, shift(other, task))
    with pytest.raises(ValidationError, match="sobreposição"):
        save_record(factory, Escala, shift(person, task, 19, 21), sid)
    with pytest.raises(ValidationError, match="escalas"):
        delete_record(factory, Participante, person)
    with pytest.raises(ValidationError, match="escalas"):
        delete_record(factory, Tarefa, task)
    for row in snapshot(factory)["escalas"]:
        delete_record(factory, Escala, row["id"])
    delete_record(factory, Tarefa, task)


@pytest.mark.parametrize("start,end", [(20, 20), (21, 20)])
def test_invalid_shift_duration(factory, start, end):
    person, task = team(factory)
    with pytest.raises(ValidationError, match="posterior"):
        save_record(factory, Escala, shift(person, task, start, end))


@pytest.mark.parametrize("model,values", [
    (Alimento, {"nome": " ", "preco": "0", "porcoes": 0, "disponivel": True}),
    (Alimento, {"nome": "A", "preco": "-1", "porcoes": 0, "disponivel": True}),
    (Alimento, {"nome": "A", "preco": "1.001", "porcoes": 0, "disponivel": True}),
    (Alimento, {"nome": "A", "preco": 0.1, "porcoes": 0, "disponivel": True}),
    (Alimento, {"nome": "A", "preco": "NaN", "porcoes": 0, "disponivel": True}),
    (Alimento, {"nome": "A", "preco": "Infinity", "porcoes": 0, "disponivel": True}),
    (Alimento, {"nome": "A", "preco": "0", "porcoes": -1, "disponivel": True}),
    (Alimento, {"nome": "A", "preco": "0", "porcoes": 1.5, "disponivel": True}),
    (Insumo, {"nome": "A", "unidade": "caixa"}),
    (Doador, {"nome": "A", "tipo": "inválido"}),
    (Participante, {"nome": "A", "vinculo": ""}),
    (Tarefa, {"nome": ""}),
    (Composicao, {"quantidade": "0"}),
    (Composicao, {"quantidade": "-1"}),
    (Doacao, {"prometida": "-1", "recebida": "0"}),
    (Doacao, {"prometida": "1", "recebida": "-1"}),
    (Doacao, {"prometida": "1", "recebida": "0.00001"}),
])
def test_invalid_values(factory, model, values):
    with pytest.raises(ValidationError):
        save_record(factory, model, values)


def test_foreign_key_enforced_and_missing_relationship_rejected(database):
    engine, factory = database
    with engine.connect() as connection:
        assert connection.scalar(text("PRAGMA foreign_keys")) == 1
    with pytest.raises(ValidationError, match="não existe"):
        save_record(factory, Composicao, {"alimento_id": 999, "insumo_id": 999, "quantidade": "1"})
    with pytest.raises(IntegrityError):
        with transaction(factory) as session:
            session.add(Composicao(alimento_id=999, insumo_id=999, quantidade=D("1")))
    assert snapshot(factory)["composicoes"] == []


def test_rollback_on_validation_or_database_failure(database):
    engine, factory = database
    with pytest.raises(RuntimeError):
        with transaction(factory) as session:
            session.add(Tarefa(nome="Não deve persistir"))
            session.flush()
            raise RuntimeError("interrupção")
    assert snapshot(factory)["tarefas"] == []
    def fail_insert(connection, cursor, statement, parameters, context, executemany):
        if statement.startswith("INSERT"):
            raise OperationalError(statement, parameters, Exception("senha-super-secreta"))
    event.listen(engine, "before_cursor_execute", fail_insert)
    try:
        with pytest.raises(StorageError) as failure:
            ingredient(factory)
        assert "senha-super-secreta" not in str(failure.value)
    finally:
        event.remove(engine, "before_cursor_execute", fail_insert)
    assert snapshot(factory)["insumos"] == []
    ingredient(factory)  # Próxima transação continua utilizável.


def test_persistence_and_exact_money(database):
    engine, factory = database
    food(factory, price="123456789,12")
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT preco FROM alimentos")) == 12345678912
    second_engine = make_engine(engine.url)
    try:
        stored = snapshot(make_session_factory(second_engine))["alimentos"][0]["preco"]
        assert stored == D("123456789.12")
    finally:
        second_engine.dispose()


def test_simultaneous_shift_creation_is_serialized(factory):
    person, task = team(factory)
    barrier = Barrier(2)
    def create():
        barrier.wait(timeout=10)
        try:
            save_record(factory, Escala, shift(person, task))
            return "saved"
        except ValidationError:
            return "conflict"
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: create(), range(2)))
    assert sorted(results) == ["conflict", "saved"]
    assert len(snapshot(factory)["escalas"]) == 1


def test_mysql_schema_uses_decimal_and_innodb():
    statement = str(CreateTable(Alimento.__table__).compile(dialect=mysql.dialect()))
    assert "NUMERIC(16, 2)" in statement
    assert "ENGINE=InnoDB" in statement
    assert "FOREIGN KEY" in str(CreateTable(Escala.__table__).compile(dialect=mysql.dialect()))


def test_snapshot_is_consistent_during_concurrent_write(database):
    engine, factory = database
    iid = ingredient(factory)
    with engine.connect() as connection:
        connection.exec_driver_sql("PRAGMA journal_mode=WAL")
    other_engine = make_engine(engine.url)
    other_factory = make_session_factory(other_engine)
    inserted = False

    def insert_between_reads(connection, cursor, statement, parameters, context, executemany):
        nonlocal inserted
        if "FROM alimentos" in statement and not inserted:
            inserted = True
            with transaction(other_factory) as session:
                new_food = Alimento(nome="Novo", preco=D("1.00"), porcoes=10, disponivel=True)
                session.add(new_food)
                session.flush()
                session.add(Composicao(alimento_id=new_food.id, insumo_id=iid, quantidade=D("1")))

    event.listen(engine, "after_cursor_execute", insert_between_reads)
    try:
        data = snapshot(factory)
        assert data["alimentos"] == []
        assert data["composicoes"] == []
        assert planning_summary(data)["porcoes"] == 0
    finally:
        event.remove(engine, "after_cursor_execute", insert_between_reads)
        other_engine.dispose()
    assert len(snapshot(factory)["composicoes"]) == 1