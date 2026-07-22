from pathlib import Path
import tomllib

from pydantic_settings import BaseSettings, SettingsConfigDict


def get_project_version() -> str:
    pyproject_path = Path("pyproject.toml")
    with pyproject_path.open("rb") as f:
        pyproject = tomllib.load(f)
    return pyproject["project"]["version"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    PROJECT_TITLE: str = "Monitoring API"
    PROJECT_DESCRIPTION: str = "Monitoring API"
    DOCS_URL: str = "/api/core/docs"
    REDOC_URL: str = "/api/core/redoc"
    OPENAPI_URL: str = "/api/core/openapi.json"
    API_PREFIX: str = "/api/core/v1"

    ENV: str = "dev"
    DATABASE_URL: str = ""
    REDIS_URL: str = ""
    SECRET_KEY: str = ""
    ALGORITHM: str = ""
    ACCESS_TOKEN_EXPIRE: int = 0
    REFRESH_TOKEN_EXPIRE: int = 10080
    MAIL_HOST: str = ""
    MAIL_PORT: int = 0
    MAIL_SECURE: bool = True
    MAIL_USER: str = ""
    MAIL_PASS: str = ""
    MAIL_FROM: str = "a@a.com"

    @property
    def cors_origins(self) -> list[str]:
        if self.ENV == "prd":
            return [
                "http://localhost:8080",
                "http://localhost:8081",
            ]

        return [
            "http://localhost:8080",
            "http://localhost:8081",
        ]


settings = Settings()
