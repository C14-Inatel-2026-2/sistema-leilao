from collections.abc import Iterator

from sqlalchemy.orm import Session


def get_session() -> Iterator[Session]:
    # Import tardio: infra.db.session exige DATABASE_URL ao ser importado.
    from infra.db.session import SessionLocal  # noqa: PLC0415

    with SessionLocal() as session:
        yield session
