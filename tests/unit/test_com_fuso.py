from datetime import datetime, timedelta, timezone

from adapters.repositories.tempo import com_fuso


def test_datetime_sem_fuso_ganha_utc():
    momento = datetime(2026, 11, 14, 12, 0)

    assert com_fuso(momento) == momento.replace(tzinfo=timezone.utc)


def test_datetime_com_fuso_permanece():
    fuso = timezone(timedelta(hours=-3))
    momento = datetime(2026, 11, 14, 9, 0, tzinfo=fuso)

    assert com_fuso(momento) is momento
