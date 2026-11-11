from app.core.config import Settings


def test_development_settings_accept_development_secret() -> None:
    settings = Settings()
    settings.environment = "development"
    settings.secret_key = "dev-only-change-this-secret-key"
    settings.access_token_minutes = 20
    settings.validate_security()


def test_production_rejects_default_secret() -> None:
    settings = Settings()
    settings.environment = "production"
    settings.secret_key = "dev-only-change-this-secret-key"

    try:
        settings.validate_security()
    except RuntimeError as exc:
        assert "SKY_SECRET_KEY" in str(exc)
    else:
        raise AssertionError("A chave de desenvolvimento não pode ser aceite em produção.")


def test_production_rejects_short_secret() -> None:
    settings = Settings()
    settings.environment = "production"
    settings.secret_key = "short-secret"

    try:
        settings.validate_security()
    except RuntimeError as exc:
        assert "32 caracteres" in str(exc)
    else:
        raise AssertionError("Uma chave curta não pode ser aceite em produção.")


def test_non_positive_token_lifetime_is_rejected() -> None:
    settings = Settings()
    settings.environment = "development"
    settings.access_token_minutes = 0

    try:
        settings.validate_security()
    except RuntimeError as exc:
        assert "ACCESS_TOKEN_MINUTES" in str(exc)
    else:
        raise AssertionError("A duração do token tem de ser positiva.")


def test_invalid_smtp_port_is_rejected() -> None:
    settings = Settings()
    settings.environment = "development"
    settings.smtp_port = 70000
    try:
        settings.validate_security()
    except RuntimeError as exc:
        assert "SMTP_PORT" in str(exc)
    else:
        raise AssertionError("Uma porta SMTP inválida não pode ser aceite.")


def test_conflicting_smtp_tls_modes_are_rejected() -> None:
    settings = Settings()
    settings.environment = "development"
    settings.smtp_starttls = True
    settings.smtp_use_ssl = True
    try:
        settings.validate_security()
    except RuntimeError as exc:
        assert "SMTP_STARTTLS" in str(exc)
    else:
        raise AssertionError("STARTTLS e SSL não podem estar ativos em simultâneo.")
