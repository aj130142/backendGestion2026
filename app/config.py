from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ─── Seguridad (#3, #4) ──────────────────────────────────────────────
    # Entorno: "development" o "production"
    ENVIRONMENT: str = "development"
    # Orígenes CORS permitidos (separados por comas en .env)
    ALLOWED_ORIGINS_STR: str = "http://localhost:5000,http://localhost:8080,http://localhost:3000"

    @property
    def ALLOWED_ORIGINS(self) -> list[str]:
        """Convierte la cadena de orígenes separados por comas en una lista."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS_STR.split(",") if origin.strip()]

    class Config:
        env_file = ".env"


settings = Settings()
