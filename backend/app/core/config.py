from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List


class Settings(BaseSettings):
    # App
    APP_NAME: str = "AI Interview Trainer"
    APP_ENV: str = "development"
    DEBUG: bool = False
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    PUBLIC_API_BASE_URL: str = ""
    PUBLIC_WEB_BASE_URL: str = ""
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # AI
    GROQ_API_KEY: str = ""
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
    GROQ_LLM_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_STT_MODEL: str = "whisper-large-v3"
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_MODEL: str = ""
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = ""
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_BASE_URL: str = ""
    ANTHROPIC_MODEL: str = ""
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = ""
    DEEPSEEK_MODEL: str = ""
    RESEND_API_KEY: str = ""
    AI_MODEL: str = "llama-3.3-70b-versatile"
    DEFAULT_PROVIDER: str = "groq"
    ENABLED_PROVIDERS: str = "groq"
    AI_REQUEST_TIMEOUT_SECONDS: int = 60
    AI_MAX_RETRIES: int = 2

    # Code execution
    CODE_RUNNER_PROVIDER: str = "judge0"
    JUDGE0_BASE_URL: str = ""
    JUDGE0_API_KEY: str = ""
    JUDGE0_HOST: str = ""

    # Email
    EMAIL_PROVIDER: str = "resend"
    EMAIL_FROM_NAME: str = "ProctoAI"
    EMAIL_FROM_ADDRESS: str = ""

    # TTS (future use)
    ELEVENLABS_API_KEY: str = ""
    TTS_PROVIDER: str = "edge"
    TTS_VOICE: str = ""

    # STT
    STT_PROVIDER: str = "groq"
    STT_BASE_URL: str = "https://api.groq.com/openai/v1"

    # Storage (future use)
    STORAGE_PROVIDER: str = "local"
    RECORDINGS_DIR: str = "recordings"
    S3_ENDPOINT_URL: str = ""
    S3_BUCKET: str = ""
    S3_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    S3_PUBLIC_BASE_URL: str = ""

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()