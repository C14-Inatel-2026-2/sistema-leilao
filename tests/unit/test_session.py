from unittest.mock import MagicMock, patch

from infra.api.dependencies import get_db
from infra.db import session as session_mod


def test_get_db_abre_e_fecha_sessao() -> None:
    fake_db = MagicMock()

    with patch.object(session_mod, "SessionLocal", return_value=fake_db):
        gen = get_db()
        db = next(gen)
        assert db is fake_db
        gen.close()

    fake_db.close.assert_called_once()
