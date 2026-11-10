from collections import Counter
from decimal import Decimal

from festa.models import donation_status


def planning_summary(data):
    zero = Decimal("0")
    foods = {item["id"]: item for item in data["alimentos"]}
    needs = {item["id"]: zero for item in data["insumos"]}
    promised = needs.copy()
    received = needs.copy()
    for composition in data["composicoes"]:
        needs[composition["insumo_id"]] += composition["quantidade"] * foods[composition["alimento_id"]]["porcoes"]
    for donation in data["doacoes"]:
        promised[donation["insumo_id"]] += donation["prometida"]
        received[donation["insumo_id"]] += donation["recebida"]
    rows = []
    for item in data["insumos"]:
        i = item["id"]
        rows.append({
            "id": i, "nome": item["nome"], "unidade": item["unidade"],
            "necessaria": needs[i], "prometida": promised[i], "recebida": received[i],
            "sem_compromisso": max(needs[i] - promised[i], zero),
            "falta_receber": max(needs[i] - received[i], zero),
            "excedente_prometido": max(promised[i] - needs[i], zero),
            "excedente_recebido": max(received[i] - needs[i], zero),
        })
    return {
        "insumos": rows,
        "alimentos": len(foods),
        "porcoes": sum(item["porcoes"] for item in foods.values()),
        "participantes": len(data["participantes"]),
        "receita": sum((item["preco"] * item["porcoes"] for item in foods.values()), zero),
        "situacoes": Counter(donation_status(d["prometida"], d["recebida"]) for d in data["doacoes"]),
    }
