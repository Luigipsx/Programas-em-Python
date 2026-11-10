from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger, Boolean, CheckConstraint, Date, DateTime, ForeignKey,
    Index, Integer, Numeric, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator


class ExactDecimal(TypeDecorator):
    """Decimal em MySQL; inteiro de escala fixa em SQLite, sem passagem por float."""
    impl = Numeric
    cache_ok = True

    def __init__(self, scale=4):
        self.scale = scale
        super().__init__()

    def load_dialect_impl(self, dialect):
        if dialect.name == "sqlite":
            return dialect.type_descriptor(BigInteger())
        return dialect.type_descriptor(Numeric(16, self.scale, asdecimal=True))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, float):
            raise ValueError("Use Decimal, nunca float.")
        number = Decimal(value)
        factor = Decimal(10) ** self.scale
        if not number.is_finite() or number * factor != (number * factor).to_integral_value():
            raise ValueError("Precisão decimal inválida.")
        return int(number * factor) if dialect.name == "sqlite" else number

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        number = Decimal(value)
        if dialect.name == "sqlite":
            number /= Decimal(10) ** self.scale
        return number.quantize(Decimal(1).scaleb(-self.scale))


class Base(DeclarativeBase):
    pass


class Alimento(Base):
    __tablename__ = "alimentos"
    __table_args__ = (
        CheckConstraint("preco >= 0", name="ck_alimento_preco"),
        CheckConstraint("porcoes >= 0", name="ck_alimento_porcoes"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(150))
    descricao: Mapped[str] = mapped_column(Text, default="")
    preco: Mapped[Decimal] = mapped_column(ExactDecimal(2), default=Decimal("0"))
    porcoes: Mapped[int] = mapped_column(Integer, default=0)
    disponivel: Mapped[bool] = mapped_column(Boolean, default=True)
    composicoes: Mapped[list["Composicao"]] = relationship(back_populates="alimento", passive_deletes="all")


class Insumo(Base):
    __tablename__ = "insumos"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(150))
    descricao: Mapped[str] = mapped_column(Text, default="")
    unidade: Mapped[str] = mapped_column(String(20))
    composicoes: Mapped[list["Composicao"]] = relationship(back_populates="insumo", passive_deletes="all")
    doacoes: Mapped[list["Doacao"]] = relationship(back_populates="insumo", passive_deletes="all")


class Composicao(Base):
    __tablename__ = "composicoes"
    __table_args__ = (
        UniqueConstraint("alimento_id", "insumo_id", name="uq_composicao_alimento_insumo"),
        CheckConstraint("quantidade > 0", name="ck_composicao_quantidade"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    alimento_id: Mapped[int] = mapped_column(ForeignKey("alimentos.id", ondelete="RESTRICT"), index=True)
    insumo_id: Mapped[int] = mapped_column(ForeignKey("insumos.id", ondelete="RESTRICT"), index=True)
    quantidade: Mapped[Decimal] = mapped_column(ExactDecimal(4))
    alimento: Mapped[Alimento] = relationship(back_populates="composicoes")
    insumo: Mapped[Insumo] = relationship(back_populates="composicoes")


class Doador(Base):
    __tablename__ = "doadores"
    __table_args__ = (
        CheckConstraint("tipo IN ('pessoa', 'organização')", name="ck_doador_tipo"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(150))
    tipo: Mapped[str] = mapped_column(String(20))
    contato: Mapped[str] = mapped_column(String(200), default="")
    observacoes: Mapped[str] = mapped_column(Text, default="")
    doacoes: Mapped[list["Doacao"]] = relationship(back_populates="doador", passive_deletes="all")


class Doacao(Base):
    __tablename__ = "doacoes"
    __table_args__ = (
        CheckConstraint("prometida >= 0 AND recebida >= 0", name="ck_doacao_quantidades"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    doador_id: Mapped[int] = mapped_column(ForeignKey("doadores.id", ondelete="RESTRICT"), index=True)
    insumo_id: Mapped[int] = mapped_column(ForeignKey("insumos.id", ondelete="RESTRICT"), index=True)
    prometida: Mapped[Decimal] = mapped_column(ExactDecimal(4), default=Decimal("0"))
    recebida: Mapped[Decimal] = mapped_column(ExactDecimal(4), default=Decimal("0"))
    entrega: Mapped[date | None] = mapped_column(Date, nullable=True)
    observacoes: Mapped[str] = mapped_column(Text, default="")
    doador: Mapped[Doador] = relationship(back_populates="doacoes")
    insumo: Mapped[Insumo] = relationship(back_populates="doacoes")

    @property
    def situacao(self):
        return donation_status(self.prometida, self.recebida)

    @property
    def excedente(self):
        return max(self.recebida - self.prometida, Decimal("0"))


def donation_status(prometida: Decimal, recebida: Decimal) -> str:
    # Uma promessa de zero ainda sem recebimento permanece pendente.
    if recebida == 0:
        return "Pendente"
    return "Recebida" if recebida >= prometida else "Parcialmente recebida"


class Participante(Base):
    __tablename__ = "participantes"
    __table_args__ = (
        CheckConstraint("vinculo IN ('aluno', 'responsável por aluno', 'servidor', 'outro')", name="ck_participante_vinculo"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(150))
    vinculo: Mapped[str] = mapped_column(String(30))
    contato: Mapped[str] = mapped_column(String(200), default="")
    observacoes: Mapped[str] = mapped_column(Text, default="")
    escalas: Mapped[list["Escala"]] = relationship(back_populates="participante", passive_deletes="all")


class Tarefa(Base):
    __tablename__ = "tarefas"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(150))
    descricao: Mapped[str] = mapped_column(Text, default="")
    local: Mapped[str] = mapped_column(String(150), default="")
    escalas: Mapped[list["Escala"]] = relationship(back_populates="tarefa", passive_deletes="all")


class Escala(Base):
    __tablename__ = "escalas"
    __table_args__ = (
        CheckConstraint("termino > inicio", name="ck_escala_periodo"),
        Index("ix_escala_participante_periodo", "participante_id", "inicio", "termino"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    participante_id: Mapped[int] = mapped_column(ForeignKey("participantes.id", ondelete="RESTRICT"))
    tarefa_id: Mapped[int] = mapped_column(ForeignKey("tarefas.id", ondelete="RESTRICT"), index=True)
    inicio: Mapped[datetime] = mapped_column(DateTime)
    termino: Mapped[datetime] = mapped_column(DateTime)
    observacoes: Mapped[str] = mapped_column(Text, default="")
    participante: Mapped[Participante] = relationship(back_populates="escalas")
    tarefa: Mapped[Tarefa] = relationship(back_populates="escalas")


MODELS = (Alimento, Insumo, Composicao, Doador, Doacao, Participante, Tarefa, Escala)
