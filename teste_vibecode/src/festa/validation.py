import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from festa.errors import ValidationError
from festa.models import Alimento, Insumo, Composicao, Doador, Doacao, Participante, Tarefa, Escala

UNITS = ("kg", "g", "L", "mL", "unidade")
DONOR_TYPES = ("pessoa", "organização")
LINKS = ("aluno", "responsável por aluno", "servidor", "outro")
STATUSES = ("Pendente", "Parcialmente recebida", "Recebida")


def required_text(value, label, limit=150, required=True):
    value = str(value or "").strip()
    if required and not value:
        raise ValidationError(f"{label} é obrigatório.")
    if len(value) > limit:
        raise ValidationError(f"{label} deve ter no máximo {limit} caracteres.")
    return value


def decimal_value(value, label, scale=4, positive=False):
    if isinstance(value, (float, bool)):
        raise ValidationError(f"{label}: use um valor decimal exato.")
    raw = str(value).strip().replace(",", ".")
    if not re.fullmatch(r"[+-]?[0-9]+(?:\.[0-9]+)?", raw):
        raise ValidationError(f"{label}: informe um número, sem separador de milhar.")
    try:
        number = Decimal(raw)
    except InvalidOperation:
        raise ValidationError(f"{label}: número inválido.") from None
    if not number.is_finite() or number < 0 or (positive and number == 0):
        requirement = "maior que zero" if positive else "não negativo"
        raise ValidationError(f"{label} deve ser {requirement}.")
    if number > Decimal("999999999"):
        raise ValidationError(f"{label} excede o limite de 999999999.")
    rounded = number.quantize(Decimal(1).scaleb(-scale))
    if rounded != number:
        raise ValidationError(f"{label} aceita até {scale} casas decimais.")
    return rounded


def integer_value(value, label):
    if isinstance(value, bool) or not re.fullmatch(r"[0-9]+", str(value)):
        raise ValidationError(f"{label} deve ser um número inteiro não negativo.")
    number = int(value)
    if number > 999999999:
        raise ValidationError(f"{label} excede o limite de 999999999.")
    return number


def choice(value, choices, label):
    if value not in choices:
        raise ValidationError(f"Selecione um valor válido para {label}.")
    return value


def normalize(model, data):
    d = dict(data)
    if model in (Alimento, Insumo, Doador, Participante, Tarefa):
        d["nome"] = required_text(d.get("nome"), "Nome")
    if model in (Alimento, Insumo, Tarefa):
        d["descricao"] = required_text(d.get("descricao"), "Descrição", 5000, False)
    if model in (Doador, Doacao, Participante, Escala):
        d["observacoes"] = required_text(d.get("observacoes"), "Observações", 5000, False)
    if model in (Doador, Participante):
        d["contato"] = required_text(d.get("contato"), "Contato", 200, False)
    if model is Alimento:
        d["preco"] = decimal_value(d.get("preco"), "Preço", 2)
        d["porcoes"] = integer_value(d.get("porcoes"), "Porções")
        if not isinstance(d.get("disponivel"), bool):
            raise ValidationError("Informe a situação do alimento.")
    elif model is Insumo:
        d["unidade"] = choice(d.get("unidade"), UNITS, "Unidade")
    elif model is Doador:
        d["tipo"] = choice(d.get("tipo"), DONOR_TYPES, "Tipo")
    elif model is Participante:
        d["vinculo"] = choice(d.get("vinculo"), LINKS, "Vínculo")
    elif model is Tarefa:
        d["local"] = required_text(d.get("local"), "Local ou setor", 150, False)
    elif model is Composicao:
        d["quantidade"] = decimal_value(d.get("quantidade"), "Quantidade por porção", positive=True)
    elif model is Doacao:
        d["prometida"] = decimal_value(d.get("prometida"), "Quantidade prometida")
        d["recebida"] = decimal_value(d.get("recebida"), "Quantidade recebida")
        d.setdefault("entrega", None)
        if d["entrega"] is not None and type(d["entrega"]) is not date:
            raise ValidationError("Data de entrega inválida.")
    elif model is Escala:
        if any(type(d.get(key)) is not datetime for key in ("inicio", "termino")):
            raise ValidationError("Informe data e hora de início e término.")
        if d["inicio"].tzinfo or d["termino"].tzinfo:
            raise ValidationError("Utilize o horário local de Blumenau nas escalas.")
        if d["termino"] <= d["inicio"]:
            raise ValidationError("O término deve ser posterior ao início.")
    return d
