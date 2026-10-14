from infra.config import Settings, settings


def test_settings_tem_defaults_de_desenvolvimento() -> None:
    cfg = Settings(_env_file=None)

    assert cfg.APP_ENV == "development"
    assert cfg.DATABASE_URL.startswith("postgresql://")
    assert cfg.JWT_ALGORITHM == "HS256"
    assert cfg.ACCESS_TOKEN_EXPIRE_MINUTES == 60
    assert settings.JWT_SECRET_KEY
