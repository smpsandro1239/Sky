import os


class Settings:
    """Configuração da aplicação obtida através das variáveis de ambiente."""

    app_name: str = "SKY API"
    environment: str = os.getenv("SKY_ENV", "development")
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://sky:change-me-local-only@localhost:5432/sky",
    )
    secret_key: str = os.getenv("SKY_SECRET_KEY", "dev-only-change-this-secret-key-rotate-before-production")
    access_token_minutes: int = int(os.getenv("ACCESS_TOKEN_MINUTES", "20"))
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
    google_client_id: str | None = os.getenv("GOOGLE_CLIENT_ID")
    google_client_secret: str | None = os.getenv("GOOGLE_CLIENT_SECRET")
    google_redirect_uri: str = os.getenv(
        "GOOGLE_REDIRECT_URI", "http://localhost:8000/api/v1/auth/google/callback"
    )

    def validate_security(self) -> None:
        if self.environment == "production":
            if (\n                self.secret_key.startswith("dev-only-")\n                or "replace-with" in self.secret_key.lower()\n                or len(self.secret_key) < 32\n            ):
                raise RuntimeError("Em produção, SKY_SECRET_KEY tem de ter pelo menos 32 caracteres e ser única.")
        if self.smtp_port < 1 or self.smtp_port > 65535:
            raise RuntimeError("SMTP_PORT tem de estar entre 1 e 65535.")
        if self.smtp_starttls and self.smtp_use_ssl:
            raise RuntimeError("SMTP_STARTTLS e SMTP_USE_SSL não podem estar ativos em simultâneo.")
        if self.access_token_minutes < 1:
            raise RuntimeError("ACCESS_TOKEN_MINUTES tem de ser superior a zero.")


settings = Settings()
