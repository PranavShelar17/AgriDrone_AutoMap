import json
from typing import List, Union, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: str = Field(default="development", description="Current runtime environment")
    PROJECT_NAME: str = Field(default="AgriDrone AutoMap", description="Project application name")
    API_V1_STR: str = Field(default="/api/v1", description="API version prefix")
    SECRET_KEY: str = Field(default="dev_insecure_secret_key_change_in_production_min_32_chars_long", min_length=32)
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT signing algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=1440, description="Access token expiration in minutes (24h default)")
    AUTH_COOKIE_NAME: str = Field(default="agridrone_session", description="Session cookie name")
    AUTH_COOKIE_SECURE: bool = Field(default=False, description="Set Secure flag on session cookies (True in HTTPS/Prod)")
    AUTH_COOKIE_SAMESITE: str = Field(default="lax", description="SameSite policy for session cookies (lax or strict)")
    RATE_LIMIT_LOGIN_ATTEMPTS: int = Field(default=5, description="Max failed login attempts before throttling")
    RATE_LIMIT_WINDOW_SECONDS: int = Field(default=300, description="Throttling observation window in seconds")
    REQUIRE_AUTHENTICATION: bool = Field(default=True, description="Enforce strict authentication on all protected endpoints")
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql+psycopg2://agridrone_user:local_pass@localhost:5434/agridrone_db",
        description="PostgreSQL PostGIS connection string"
    )
    DB_POOL_SIZE: int = Field(default=10, description="Database connection pool size")
    DB_MAX_OVERFLOW: int = Field(default=20, description="Database pool max overflow")
    DB_TIMEOUT_SECONDS: int = Field(default=5, description="Database connectivity timeout in seconds")
    
    # Redis
    REDIS_URL: str = Field(
        default="redis://localhost:6380/0",
        description="Redis connection URL"
    )
    
    # CORS
    CORS_ORIGINS: Union[str, List[str]] = Field(
        default=["http://localhost:3000", "http://localhost:3005"],
        description="Allowed CORS origins"
    )
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Application log level")
    
    # Azure Storage (Phase 5)
    AZURE_STORAGE_CONNECTION_STRING: str = Field(default="")
    AZURE_STORAGE_ACCOUNT_NAME: str = Field(default="agridronestorage")
    AZURE_CONTAINER_RAW: str = Field(default="raw-surveys")
    AZURE_CONTAINER_ORTHO: str = Field(default="orthomosaics")
    AZURE_CONTAINER_INDICES: str = Field(default="vegetation-indices")
    AZURE_CONTAINER_REPORTS: str = Field(default="reports")
    LOCAL_STORAGE_PATH: str = Field(default="storage", description="Base local directory for storage fallback")
    MAX_UPLOAD_SIZE_BYTES: int = Field(default=524288000, description="Max allowed file size in bytes (500MB)")
    ALLOW_DEV_LOCAL_STORAGE: bool = Field(default=True, description="Allow local storage adapter in development")
    
    # WebODM (Phase 6)
    WEBODM_API_URL: str = Field(default="http://localhost:3001", description="WebODM or NodeODM service URL")
    WEBODM_USERNAME: str = Field(default="admin", description="WebODM admin username")
    WEBODM_PASSWORD: str = Field(default="admin", description="WebODM admin password")
    WEBODM_PROJECT_ID: Optional[int] = Field(default=None, description="Default WebODM project ID (auto-created if None)")
    WEBODM_TOKEN: Optional[str] = Field(default=None, description="Pre-configured WebODM authentication token")
    WEBODM_TIMEOUT_SECONDS: int = Field(default=30, description="HTTP request timeout to WebODM")
    WEBODM_POLL_INTERVAL_SECONDS: int = Field(default=10, description="Worker polling interval in seconds")
    WEBODM_MAX_RETRIES: int = Field(default=3, description="Maximum task dispatch retry attempts")

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if v and v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+psycopg2://", 1)
        elif v and v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+psycopg2://", 1)
        return v

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                return [origin.strip() for origin in v.split(",") if origin.strip()]
        elif isinstance(v, list):
            return v
        return ["http://localhost:3000", "http://localhost:3005"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
