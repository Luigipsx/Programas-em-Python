# alguns imports
from sqlalchemy import create_engine, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from typing import Optional
import os
from dotenv import load_dotenv

# classe "base"
class Base(DeclarativeBase):
    pass

# classe pessoa, que herda da "base"
class Pessoa(Base):
    # nome da tabela a ser criada no banco de dados
    __tablename__ = "pessoas"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255))
    telefone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

# ler o arquivo .env
load_dotenv()

# buscando as variáveis de ambiente
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")

# definição do banco de dados
engine = create_engine(
f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
)

# configuração para criar o arquivo de banco de dados
Base.metadata.create_all(engine)

# abrir a sessão
with Session(engine) as session:

    # criar uma pessoa
    p = Pessoa(nome="João", 
               email="joao@email.com",
               telefone="11999999999")

    # adicionar a pessoa na sessão, preparando para ser gravada
    session.add(p)
        
    # confirmar a inserção no banco de dados
    session.commit()

    print("Tabela criada (se não havia) e pessoa inserida no banco de dados")
