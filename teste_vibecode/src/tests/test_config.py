import pytest

from festa import config
from festa.errors import ValidationError


def test_sqlite_path_relative_to_project(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "ROOT", tmp_path)
    monkeypatch.setenv("DB_BACKEND", "sqlite")
    monkeypatch.setenv("SQLITE_PATH", "data/local.db")
    url = config.database_url()
    assert url.drivername == "sqlite+pysqlite"
    assert url.database == str((tmp_path / "data/local.db").resolve())


def test_mysql_credentials_special_characters_and_tls(monkeypatch):
    values = {"DB_BACKEND": "mysql", "MYSQL_HOST": "db.example.com", "MYSQL_PORT": "3306",
              "MYSQL_USER": "app", "MYSQL_PASSWORD": "a@:/# senha",
              "MYSQL_DATABASE": "festa", "MYSQL_SSL_CA": "/certs/ca.pem"}
    for key, value in values.items():
        monkeypatch.setenv(key, value)
    url = config.database_url()
    assert url.password == values["MYSQL_PASSWORD"]
    assert url.drivername == "mysql+pymysql"
    assert url.query["ssl_verify_cert"] == "true"
    assert values["MYSQL_PASSWORD"] not in str(url)


def test_environment_wins_over_dotenv(monkeypatch, tmp_path):
    (tmp_path / ".env").write_text("DB_BACKEND=mysql\n", encoding="utf-8")
    monkeypatch.setattr(config, "ROOT", tmp_path)
    monkeypatch.setenv("DB_BACKEND", "sqlite")
    monkeypatch.setenv("SQLITE_PATH", "data/test.db")
    assert config.database_url().drivername == "sqlite+pysqlite"


def test_invalid_backend(monkeypatch):
    monkeypatch.setenv("DB_BACKEND", "outro")
    with pytest.raises(ValidationError, match="DB_BACKEND"):
        config.database_url()


@pytest.mark.parametrize("password", ["", None])
def test_mysql_distinguishes_empty_and_missing_password(monkeypatch, tmp_path, password):
    monkeypatch.setattr(config, "ROOT", tmp_path)
    values = {"DB_BACKEND": "mysql", "MYSQL_HOST": "localhost",
              "MYSQL_DATABASE": "festa", "MYSQL_USER": "local",
              "MYSQL_PORT": "3306"}
    for key, value in values.items():
        monkeypatch.setenv(key, value)
    monkeypatch.delenv("MYSQL_SSL_CA", raising=False)
    monkeypatch.delenv("MYSQL_PASSWORD", raising=False)
    if password is None:
        with pytest.raises(ValidationError, match="Defina MYSQL_PASSWORD"):
            config.database_url()
    else:
        monkeypatch.setenv("MYSQL_PASSWORD", password)
        url = config.database_url()
        assert url.drivername == "mysql+pymysql"
        assert url.password == ""
