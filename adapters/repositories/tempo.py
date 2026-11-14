from datetime import datetime, timezone


def com_fuso(momento: datetime) -> datetime:
    # SQLite devolve datetime sem fuso; o PostgreSQL ja devolve em UTC.
    if momento.tzinfo is None:
        return momento.replace(tzinfo=timezone.utc)
    return momento
