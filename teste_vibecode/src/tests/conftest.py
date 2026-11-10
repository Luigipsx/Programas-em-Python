import pytest

from festa.database import create_tables, make_engine, make_session_factory


@pytest.fixture
def database(tmp_path):
    engine = make_engine("sqlite+pysqlite:///" + (tmp_path / "test.db").as_posix())
    create_tables(engine)
    factory = make_session_factory(engine)
    yield engine, factory
    engine.dispose()


@pytest.fixture
def factory(database):
    return database[1]
