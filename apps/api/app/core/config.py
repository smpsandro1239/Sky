import os
from urllib.parse import urlsplit


def normalize_database_url(database_url: str) -> str:
    """Normaliza URLs PostgreSQL comuns para o driver psycopg 3 do SQLAlchemy."""
    if database_url.startswith("postgres://"):
        return "postgresql+psycopg://" + database_url.removeprefix("postgres://")
    if database_url.startswith("postgresql://"):
        return "postgresql+psycopg://" + database_url.removeprefix("postgresql://")
    return database_url


class Settings:
    """Configuração da aplicação obtida através das variáveis de ambiente."""

    app_name: str = "SKY API"
    environment: str = os.getenv("SKY_ENV", "development")
    _raw_database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://sky:change-me-local-only@localhost:5432/sky",
    )
    database_url: str = normalize_database_url(_raw_database_url)
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    price_monitor_interval_seconds: int = int(os.getenv("PRICE_MONITOR_INTERVAL_SECONDS", "21600"))
    price_monitor_poll_seconds: int = int(os.getenv("PRICE_MONITOR_POLL_SECONDS", "60"))
    price_monitor_retry_seconds: int = int(os.getenv("PRICE_MONITOR_RETRY_SECONDS", "600"))
    secret_key: str = os.getenv("SKY_SECRET_KEY", "dev-only-change-this-secret-key-rotate-before-production")
    access_token_minutes: int = int(os.getenv("ACCESS_TOKEN_MINUTES", "20"))
    admin_emails: set[str] = {
        email.strip().lower()
        for email in os.getenv("SKY_ADMIN_EMAILS", "").split(",")
        if email.strip()
    }
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    cors_origins: list[str] = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
        if origin.strip()
    ]
    smtp_host: str | None = os.getenv("SMTP_HOST")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str | None = os.getenv("SMTP_USERNAME")
    smtp_password: str | None = os.getenv("SMTP_PASSWORD")
    smtp_from_email: str | None = os.getenv("SMTP_FROM_EMAIL")
    smtp_starttls: bool = os.getenv("SMTP_STARTTLS", "true").strip().lower() in {"1", "true", "yes"}
    smtp_use_ssl: bool = os.getenv("SMTP_USE_SSL", "false").strip().lower() in {"1", "true", "yes"}
    amadeus_client_id: str | None = os.getenv("AMADEUS_CLIENT_ID")
    amadeus_client_secret: str | None = os.getenv("AMADEUS_CLIENT_SECRET")
    amadeus_base_url: str = os.getenv("AMADEUS_BASE_URL", "https://test.api.amadeus.com")
    google_client_id: str | None = os.getenv("GOOGLE_CLIENT_ID")
    google_client_secret: str | None = os.getenv("GOOGLE_CLIENT_SECRET")
    google_redirect_uri: str = os.getenv(
        "GOOGLE_REDIRECT_URI", "http://localhost:8000/api/v1/auth/google/callback"
    )

    def validate_security(self) -> None:
        if self.environment == "production":
            if (
                self.secret_key.startswith("dev-only-")
                or "replace-with" in self.secret_key.lower()
                or len(self.secret_key) < 32
            ):
                raise RuntimeError("Em produção, SKY_SECRET_KEY tem de ter pelo menos 32 caracteres e ser única.")
            if not self.cors_origins:
                raise RuntimeError("Em produção, CORS_ORIGINS tem de conter pelo menos uma origem HTTPS explícita.")
            for origin in self.cors_origins:
                try:
                    parsed_origin = urlsplit(origin)
                except ValueError as exc:
                    raise RuntimeError("CORS_ORIGINS contém uma origem inválida.") from exc
                if (
                    parsed_origin.scheme != "https"
                    or not parsed_origin.netloc
                    or parsed_origin.hostname is None
                    or parsed_origin.username is not None
                    or parsed_origin.password is not None
                    or parsed_origin.path
                    or parsed_origin.query
                    or parsed_origin.fragment
                    or origin == "*"
                ):
                    raise RuntimeError(
                        "Em produção, cada origem de CORS_ORIGINS tem de ser uma origem HTTPS válida, sem caminhos."
                    )
        if self.smtp_port < 1 or self.smtp_port > 65535:
            raise RuntimeError("SMTP_PORT tem de estar entre 1 e 65535.")
        if self.smtp_starttls and self.smtp_use_ssl:
            raise RuntimeError("SMTP_STARTTLS e SMTP_USE_SSL não podem estar ativos em simultâneo.")
        if bool(self.smtp_host) != bool(self.smtp_from_email):
            raise RuntimeError("SMTP_HOST e SMTP_FROM_EMAIL têm de ser configurados em conjunto.")
        if self.smtp_host and not (self.smtp_starttls or self.smtp_use_ssl):
            raise RuntimeError("O SMTP tem de utilizar STARTTLS ou SSL para proteger as credenciais e o convite.")
        if bool(self.smtp_username) != bool(self.smtp_password):
            raise RuntimeError("SMTP_USERNAME e SMTP_PASSWORD têm de ser configurados em conjunto.")
        if self.access_token_minutes < 1:
            raise RuntimeError("ACCESS_TOKEN_MINUTES tem de ser superior a zero.")
        if self.price_monitor_interval_seconds < 60:
            raise RuntimeError("PRICE_MONITOR_INTERVAL_SECONDS tem de ser pelo menos 60.")
        if self.price_monitor_poll_seconds < 5:
            raise RuntimeError("PRICE_MONITOR_POLL_SECONDS tem de ser pelo menos 5.")
        if self.price_monitor_retry_seconds < 30:
            raise RuntimeError("PRICE_MONITOR_RETRY_SECONDS tem de ser pelo menos 30.")


settings = Settings()
