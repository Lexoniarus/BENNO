"""Configuration classes for BENNO."""


class BaseConfig:
    """Base configuration shared by all environments."""

    AI_PROVIDER = "gemini"
    GEMINI_API_KEY = None
    GEMINI_MODEL = "gemini-3.1-flash-lite"
    SECRET_KEY = "development-secret-key"
    SQLALCHEMY_DATABASE_URI = None
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = False


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
