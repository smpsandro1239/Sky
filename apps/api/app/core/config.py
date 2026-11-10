import os


class Settings:
    """Configuração da aplicação obtida através do ambiente."""

    app_name: str = "SKY API"
    environment: str = os.getenv("SKY_ENV", "development")
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://sky:change-me-local-only@localhost:5432/sky",
    )


settings = Settings()
