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


def test_production_rejects_documentation_placeholder_secret() -> None:
    settings = Settings()
    settings.environment = "production"
    settings.secret_key = "replace-with-a-random-secret-of-at-least-32-characters"
    try:
        settings.validate_security()
    except RuntimeError as exc:
        assert "SKY_SECRET_KEY" in str(exc)
    else:
        raise AssertionError("A chave de exemplo não pode ser aceite em produção.")


def test_smtp_requires_sender_when_host_is_configured() -> None:
    settings = Settings()
    settings.environment = "development"
    settings.smtp_host = "smtp.example.com"
    settings.smtp_from_email = None
    try:
        settings.validate_security()
    except RuntimeError as exc:
        assert "SMTP_HOST" in str(exc)
    else:
        raise AssertionError("SMTP_HOST sem SMTP_FROM_EMAIL deve ser rejeitado.")


def test_smtp_rejects_unencrypted_transport() -> None:
    settings = Settings()
    settings.environment = "development"
    settings.smtp_host = "smtp.example.com"
    settings.smtp_from_email = "sky@example.com"
    settings.smtp_starttls = False
    settings.smtp_use_ssl = False
    try:
        settings.validate_security()
    except RuntimeError as exc:
        assert "STARTTLS ou SSL" in str(exc)
    else:
        raise AssertionError("SMTP sem encriptação deve ser rejeitado.")


def test_smtp_credentials_must_be_configured_as_a_pair() -> None:
    settings = Settings()
    settings.environment = "development"
    settings.smtp_username = "sky-user"
    settings.smtp_password = None
    try:
        settings.validate_security()
    except RuntimeError as exc:
        assert "SMTP_USERNAME" in str(exc)
    else:
        raise AssertionError("Credenciais SMTP incompletas devem ser rejeitadas.")


def test_neon_postgres_url_is_normalized_for_psycopg() -> None:
    from app.core.config import normalize_database_url

    source = "postgresql://sky-user:secret@ep-example.eu-central-1.aws.neon.tech/sky?sslmode=require"
    assert normalize_database_url(source) == (
        "postgresql+psycopg://sky-user:secret@ep-example.eu-central-1.aws.neon.tech/sky?sslmode=require"
    )


def test_legacy_postgres_url_is_normalized_for_psycopg() -> None:
    from app.core.config import normalize_database_url

    source = "postgres://sky-user:secret@host.example/sky"
    assert normalize_database_url(source) == "postgresql+psycopg://sky-user:secret@host.example/sky"


def test_explicit_sqlalchemy_driver_is_preserved() -> None:
    from app.core.config import normalize_database_url

    source = "postgresql+psycopg://sky-user:secret@host.example/sky"
    assert normalize_database_url(source) == source


def test_non_postgres_database_url_is_preserved() -> None:
    from app.core.config import normalize_database_url

    source = "sqlite+pysqlite:///./migration-test.db"
    assert normalize_database_url(source) == source
