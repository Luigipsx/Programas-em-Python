"""Prévia visual com dados fictícios em SQLite temporário.

Execute: uv run python src/tests/preview_demo.py
Nunca usa o banco configurado no .env.
"""
import os
import sys
import tempfile
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from festa.database import create_tables, make_engine, make_session_factory
from festa.models import Alimento, Composicao, Doacao, Doador, Escala, Insumo, Participante, Tarefa
from festa.services import save_record


def main():
    folder = Path(tempfile.mkdtemp(prefix="festa-ifc-preview-"))
    os.environ["DB_BACKEND"] = "sqlite"
    os.environ["SQLITE_PATH"] = str(folder / "preview.db")
    engine = make_engine()
    create_tables(engine)
    factory = make_session_factory(engine)
    ingredients = [
        ("Farinha de trigo", "kg"), ("Queijo muçarela", "kg"), ("Óleo de cozinha", "L"),
        ("Embalagem de papel", "unidade"), ("Chocolate em pó", "kg"), ("Leite integral", "L"),
    ]
    ids = [save_record(factory, Insumo, {"nome": name, "unidade": unit,
            "descricao": "Contribuição para o preparo dos alimentos."}) for name, unit in ingredients]
    foods = [
        ("Pastel de queijo", "8.50", 180, True), ("Bolo de chocolate", "6", 100, True),
        ("Cachorro-quente", "10", 150, True), ("Chocolate quente", "5", 80, False),
    ]
    food_ids = [save_record(factory, Alimento, {"nome": name, "preco": price,
                "porcoes": portions, "disponivel": available}) for name, price, portions, available in foods]
    for food, ingredient, quantity in [
        (0, 0, "0.08"), (0, 1, "0.05"), (0, 2, "0.025"), (0, 3, "1"),
        (1, 4, "0.02"), (1, 5, "0.05"),
    ]:
        save_record(factory, Composicao, {"alimento_id": food_ids[food],
                    "insumo_id": ids[ingredient], "quantidade": quantity})
    donors = [save_record(factory, Doador, {"nome": name, "tipo": kind})
              for name, kind in [("Comunidade IFC", "organização"),
                                  ("Mariana Costa", "pessoa"), ("Padaria do Bairro", "organização")]]
    for donor, ingredient, promised, received in [
        (0, 0, "10", "10"), (1, 1, "6", "3"), (2, 0, "5", "0"),
        (0, 3, "200", "200"), (1, 2, "5", "2"), (2, 5, "10", "12"),
    ]:
        save_record(factory, Doacao, {"doador_id": donors[donor], "insumo_id": ids[ingredient],
                    "prometida": promised, "recebida": received, "entrega": date(2026, 12, 5)})
    for name, task, place, hour in [
        ("Ana Souza", "Preparo dos alimentos", "Cozinha", 16),
        ("Pedro Martins", "Atendimento ao público", "Pátio", 18),
        ("Juliana Lima", "Montagem do espaço", "Área de convivência", 14),
    ]:
        person = save_record(factory, Participante, {"nome": name, "vinculo": "aluno"})
        job = save_record(factory, Tarefa, {"nome": task, "local": place})
        save_record(factory, Escala, {"participante_id": person, "tarefa_id": job,
                    "inicio": datetime(2026, 12, 5, hour), "termino": datetime(2026, 12, 5, hour + 2)})
    engine.dispose()
    print("Prévia com banco temporário e dados fictícios: http://127.0.0.1:8511")
    from streamlit.web import cli
    sys.argv = ["streamlit", "run", str(Path(__file__).resolve().parents[1] / "app.py"),
                "--server.headless=true", "--server.address=127.0.0.1", "--server.port=8511"]
    return cli.main()


if __name__ == "__main__":
    raise SystemExit(main())
