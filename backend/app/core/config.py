from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    DATABASE_URL: str
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_ACCESS_TOKEN: str = ""
    WHATSAPP_WEBHOOK_VERIFY_TOKEN: str = ""
    WHATSAPP_APP_SECRET: str = ""
    WHATSAPP_API_VERSION: str = "v23.0"
    WHATSAPP_GRAPH_TIMEOUT_SECONDS: float = 15.0
    WHATSAPP_CONVERSATION_TTL_MINUTES: int = 1440
    WHATSAPP_RATE_LIMIT_PER_MINUTE: int = 20
    WHATSAPP_MAX_RETRIES: int = 3
    WHATSAPP_TEMPLATE_RECEPCION: str = ""
    WHATSAPP_TEMPLATE_PROGRAMACION: str = ""
    WHATSAPP_TEMPLATE_RECOLECCION: str = ""
    WHATSAPP_TEMPLATE_CANCELACION: str = ""
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_TRANSCRIPTION_MODEL: str = "whisper-1"
    USE_EXTERNAL_SERVICES: bool = False
    MODO_PILOTO: bool = False
    DATA_RETENTION_DAYS: int = 90
    BACKEND_CORS_ORIGINS: str = "http://localhost:3000"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    AUTH_RATE_LIMIT_PER_MINUTE: int = 10

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",")]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
