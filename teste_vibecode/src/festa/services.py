from sqlalchemy import inspect, select, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from festa.database import transaction
from festa.errors import StorageError, ValidationError
from festa.models import MODELS, Alimento, Insumo, Composicao, Doador, Doacao, Participante, Tarefa, Escala
from festa.validation import normalize

REFERENCES = {
    Composicao: (("alimento_id", Alimento, "alimento"), ("insumo_id", Insumo, "insumo")),
    Doacao: (("doador_id", Doador, "doador"), ("insumo_id", Insumo, "insumo")),
    Escala: (("participante_id", Participante, "participante"), ("tarefa_id", Tarefa, "tarefa")),
}
DEPENDENCIES = {
    Alimento: ((Composicao, "alimento_id", "composições de alimentos"),),
    Insumo: ((Composicao, "insumo_id", "composições de alimentos"), (Doacao, "insumo_id", "doações")),
    Doador: ((Doacao, "doador_id", "doações"),),
    Participante: ((Escala, "participante_id", "escalas de trabalho"),),
    Tarefa: ((Escala, "tarefa_id", "escalas de trabalho"),),
}


def linked_records(session, model, record_id):
    links = []
    for child, field, label in DEPENDENCIES.get(model, ()):
        found = session.scalars(select(child.id).where(getattr(child, field) == record_id).with_for_update()).first()
        if found is not None:
            links.append(label)
    return links


def save_record(factory, model, values, record_id=None):
    if model not in MODELS:
        raise ValidationError("Cadastro desconhecido.")
    allowed = set(inspect(model).columns.keys()) - {"id"}
    if set(values) - allowed:
        raise ValidationError("Campos de cadastro inválidos.")
    data = normalize(model, values)
    try:
        with transaction(factory) as session:
            record = None
            if record_id is not None:
                record = session.scalar(select(model).where(model.id == record_id).with_for_update())
                if record is None:
                    raise ValidationError("Registro não encontrado. Atualize a página.")
            for field, parent, label in REFERENCES.get(model, ()):
                parent_id = data.get(field)
                if type(parent_id) is not int or parent_id <= 0:
                    raise ValidationError(f"Selecione um {label}.")
                # Bloqueia o pai até o commit. Serializa escalas do mesmo participante
                # e alterações de unidade com a criação de novos vínculos em MySQL.
                if session.scalar(select(parent).where(parent.id == parent_id).with_for_update()) is None:
                    raise ValidationError(f"O {label} selecionado não existe mais.")
            if model is Insumo and record and data["unidade"] != record.unidade:
                if linked_records(session, model, record.id):
                    raise ValidationError("A unidade não pode mudar: o insumo possui composições ou doações. Remova esses vínculos primeiro.")
            if model is Composicao:
                duplicate = select(Composicao.id).where(
                    Composicao.alimento_id == data["alimento_id"],
                    Composicao.insumo_id == data["insumo_id"],
                    Composicao.id != (record_id or 0),
                ).with_for_update()
                if session.scalar(duplicate) is not None:
                    raise ValidationError("Este insumo já está na composição. Edite a associação existente.")
            if model is Escala:
                conflict = select(Escala.id).where(
                    Escala.participante_id == data["participante_id"],
                    Escala.inicio < data["termino"],
                    Escala.termino > data["inicio"],
                    Escala.id != (record_id or 0),
                ).with_for_update()
                if session.scalar(conflict) is not None:
                    raise ValidationError("O participante já possui uma escala com sobreposição de horários.")
            if record is None:
                record = model(**data)
                session.add(record)
            else:
                for key, value in data.items():
                    setattr(record, key, value)
            session.flush()
            saved_id = record.id
        return saved_id
    except IntegrityError:
        raise ValidationError("Não foi possível salvar: há um vínculo inválido ou uma composição duplicada. Atualize os cadastros.") from None
    except SQLAlchemyError:
        raise StorageError("Não foi possível salvar os dados. Tente novamente ou consulte o responsável pelo sistema.") from None


def delete_record(factory, model, record_id):
    if model not in MODELS:
        raise ValidationError("Cadastro desconhecido.")
    try:
        with transaction(factory) as session:
            record = session.scalar(select(model).where(model.id == record_id).with_for_update())
            if record is None:
                raise ValidationError("Registro não encontrado. Atualize a página.")
            links = linked_records(session, model, record_id)
            if links:
                raise ValidationError("Exclusão bloqueada. Remova primeiro os vínculos em: " + ", ".join(links) + ".")
            session.delete(record)
            session.flush()
    except IntegrityError:
        raise ValidationError("Exclusão bloqueada: o registro está em uso em outro cadastro. Atualize a página para consultar os vínculos.") from None
    except SQLAlchemyError:
        raise StorageError("Não foi possível excluir os dados. Tente novamente.") from None


def snapshot(factory):
    """Retorna somente valores; sessões e objetos ORM não vão para o estado da UI."""
    try:
        with factory() as session, session.begin():
            if session.get_bind().dialect.name == "sqlite":
                # Uma leitura consistente entre todas as tabelas, mesmo com outros usuários.
                session.execute(text("BEGIN"))
            result = {}
            for model in MODELS:
                records = session.scalars(select(model).order_by(model.id)).all()
                result[model.__tablename__] = [
                    {column.key: getattr(row, column.key) for column in inspect(model).columns}
                    for row in records
                ]
            return result
    except SQLAlchemyError:
        raise StorageError("Não foi possível consultar os dados. Verifique a conexão com o banco.") from None
