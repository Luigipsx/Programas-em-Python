from sqlalchemy.exc import SQLAlchemyError

from festa.database import create_tables, make_engine
from festa.errors import ValidationError


def main():
    engine = None
    try:
        engine = make_engine()
        create_tables(engine)
    except (ValidationError, SQLAlchemyError, OSError):
        raise SystemExit("Não foi possível criar as tabelas. Verifique a configuração e o acesso ao banco.") from None
    finally:
        if engine is not None:
            engine.dispose()
    print("Tabelas criadas ou verificadas com sucesso.")


if __name__ == "__main__":
    main()
