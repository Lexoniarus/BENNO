"""Configuration classes for BENNO."""


class BaseConfig:
    """Base configuration shared by all environments."""

    AI_PROVIDER = "gemini"
    GEMINI_API_KEY = None
    GEMINI_MODEL = "gemini-3.1-flash-lite"
    LANGFUSE_BASE_URL = None
    LANGFUSE_CAPTURE_FULL_CONTEXT = False
    LANGFUSE_ENABLED = False
    LANGFUSE_FLUSH_ON_TURN = False
    LANGFUSE_HOST = None
    LANGFUSE_PUBLIC_KEY = None
    LANGFUSE_SECRET_KEY = None
    SECRET_KEY = "development-secret-key"
    SQLALCHEMY_DATABASE_URI = None
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    KOKORO_BASE_URL = "http://127.0.0.1:8881"
    KOKORO_TTS_MODEL = "kokoro"
    KOKORO_TTS_VOICE = "martin"
    SPEACHES_BASE_URL = "http://127.0.0.1:8000"
    SPEACHES_STT_LANGUAGE = "de"
    SPEACHES_STT_MODEL = "Systran/faster-whisper-base"
    TESTING = False
    VOICE_ENABLED = True


class DevelopmentConfig(BaseConfig):
    """Configuration for local development."""

    DEBUG = True


class TestingConfig(BaseConfig):
    """Configuration for automated tests."""

    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProductionConfig(BaseConfig):
    """Configuration for production-like runs."""

    DEBUG = False


CONFIG_BY_NAME = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
