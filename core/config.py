import secrets
from typing import Any, List, Optional, Union
from pydantic import BaseSettings, RedisDsn, validator


class Settings(BaseSettings):
    API_V1_STR = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8

    BACKEND_CORS_ORIGINS: List[str] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assembleCORSOrigins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    PROJECT_NAME: str

    MYSQL_SERVER: str
    MYSQL_USER: str
    MYSQL_PASSWORD: str
    MYSQL_DB: str
    SQLALCHEMY_DATABASE_URI: Optional[str] = None

    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assembleDBConnection(cls, v: Optional[str], values: dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return f"mysql+aiomysql://{values['MYSQL_USER']}:{values['MYSQL_PASSWORD']}@{values['MYSQL_SERVER']}/{values['MYSQL_DB']}?charset=utf8mb4"

    REDIS_SERVER: str
    REDIS_USER: str
    REDIS_PASSWORD: str
    REDIS_DB: int
    REDIS_URI: Optional[RedisDsn] = None

    @validator("REDIS_URI", pre=True)
    def assembleRedisConnection(cls, v: Optional[str], values: dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return f"redis://{values['REDIS_USER']}:{values['REDIS_PASSWORD']}@{values['REDIS_SERVER']}/{values['REDIS_DB']}"

    S3_API_ENDPOINT: str
    S3_API_ACCESS_KEY: str
    S3_API_SECRET_KEY: str

    FIRST_ADMIN_ID: str
    FIRST_ADMIN_PASSWORD: str

    class Config:
        case_sensitive = True
        env_file = ".env.local"


settings = Settings()
