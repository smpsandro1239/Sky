import os


class Settings:
    """Configuração da aplicação obtida através das variáveis de ambiente."""

    app_name: str = "SKY API"
    environment: str = os.getenv("SKY_ENV", "development")
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://sky:change-me-local-only@localhost:5432/sky",
    )
    secret_key: str = os.getenv("SKY_SECRET_KEY", "dev-only-change-this-secret-key")
    access_token_minutes: int = int(os.getenv("ACCESS_TOKEN_MINUTES", "20"))
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    cors_origins: list[str] = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
        if origin.strip()
    ]
    google_client_id: str | None = os.getenv("GOOGLE_CLIENT_ID")
    google_client_secret: str | None = os.getenv("GOOGLE_CLIENT_SECRET")
    google_redirect_uri: str = os.getenv(
        "GOOGLE_REDIRECT_URI", "http://localhost:8000/api/v1/auth/google/callback"
    )

    def validate_security(self) -> None:
        if self.environment == "production":
            if self.secret_key == "dev-only-change-this-secret-key" or len(self.secret_key) < 32:
                raise RuntimeError("Em produção, SKY_SECRET_KEY tem de ter pelo menos 32 caracteres e ser única.")
        if self.access_token_minutes < 1:
            raise RuntimeError("ACCESS_TOKEN_MINUTES tem de ser superior a zero.")


settings = Settings()
