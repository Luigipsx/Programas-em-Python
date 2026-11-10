from contextlib import contextmanager

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from festa.config import database_url
from festa.models import Base


def make_engine(url=None):
    url = url if url is not None else database_url()
    sqlite = str(url).startswith("sqlite")
    options = {"pool_pre_ping": True}
    if sqlite:
        options["connect_args"] = {"check_same_thread": False, "timeout": 30}
        if ":memory:" in str(url):
            options["poolclass"] = StaticPool
    else:
        options["pool_recycle"] = 1800
        options["connect_args"] = {"connect_timeout": 10}
    engine = create_engine(url, **options)
    if sqlite:
        @event.listens_for(engine, "connect")
        def enable_foreign_keys(connection, _):
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
    return engine


def make_session_factory(engine):
    return sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


def create_tables(engine):
    Base.metadata.create_all(engine)


@contextmanager
def transaction(factory):
    with factory() as session:
        # begin() faz commit no sucesso e rollback em QUALQUER exceção.
        with session.begin():
            if session.get_bind().dialect.name == "sqlite":
                # Serializa validar + gravar, inclusive quando há duas sessões.
                session.execute(text("BEGIN IMMEDIATE"))
            yield session
