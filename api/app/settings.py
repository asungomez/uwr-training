from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def normalize_db_url(url: str) -> str:
    """Render (and most providers) hand out a `postgresql://` URL, but the async
    engine needs the asyncpg driver. Normalize the scheme so one URL works
    everywhere."""
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Postgres connection. Scheme is normalized to the asyncpg driver.
    database_url: str = "postgresql+asyncpg://uwr:uwr@localhost:5432/uwr"

    # Signs session-cookie JWTs. MUST be overridden in any non-local environment.
    secret_key: str = "dev-secret-change-me"

    # Mark the session cookie Secure (HTTPS only). Set false for local plain-HTTP.
    cookie_secure: bool = True

    # Comma-separated allowed front-end origins (used by CORS for direct calls).
    cors_origins: str = "http://localhost:5173"

    @field_validator("database_url")
    @classmethod
    def _normalize_database_url(cls, value: str) -> str:
        return normalize_db_url(value)

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
