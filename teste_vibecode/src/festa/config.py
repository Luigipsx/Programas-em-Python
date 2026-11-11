import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import URL

from festa.errors import ValidationError

ROOT = Path(__file__).resolve().parents[2]


def database_url() -> URL:
    load_dotenv(ROOT / ".env", override=False)
    backend = os.getenv("DB_BACKEND", "sqlite").strip().lower()
    if backend == "sqlite":
        path = Path(os.getenv("SQLITE_PATH", "data/festa.db")).expanduser()
        if not path.is_absolute():
            path = ROOT / path
        path.parent.mkdir(parents=True, exist_ok=True)
        return URL.create("sqlite+pysqlite", database=str(path.resolve()))
    if backend != "mysql":
        raise ValidationError("DB_BACKEND deve ser sqlite ou mysql.")
    names = ("MYSQL_HOST", "MYSQL_DATABASE", "MYSQL_USER")
    if any(not os.getenv(name, "").strip() for name in names):
        raise ValidationError("Configure host, banco e usuário do MySQL nas variáveis de ambiente.")
    if "MYSQL_PASSWORD" not in os.environ:
        raise ValidationError(
            "Defina MYSQL_PASSWORD no .env ou nas variáveis de ambiente. "
            "Para um servidor local sem senha, use MYSQL_PASSWORD=."
        )
    try:
        port = int(os.getenv("MYSQL_PORT", "3306"))
        if not 1 <= port <= 65535:
            raise ValueError
    except ValueError:
        raise ValidationError("MYSQL_PORT deve ser uma porta válida.") from None
    query = {"charset": "utf8mb4"}
    if os.getenv("MYSQL_SSL_CA"):
        query.update(ssl_ca=os.environ["MYSQL_SSL_CA"],
                     ssl_check_hostname="true", ssl_verify_cert="true")
    return URL.create(
        "mysql+pymysql", username=os.environ["MYSQL_USER"],
        password=os.environ["MYSQL_PASSWORD"], host=os.environ["MYSQL_HOST"],
        port=port, database=os.environ["MYSQL_DATABASE"], query=query,
    )
