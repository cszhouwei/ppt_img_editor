from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""

    # 服务配置
    port: int = 8080
    base_url: str = "http://localhost:8080"
    environment: str = "development"

    # MinIO 存储配置
    s3_endpoint: str
    s3_public_endpoint: str = ""  # 公网访问地址
    s3_access_key: str
    s3_secret_key: str
    s3_bucket: str = "doc-edit"
    s3_region: str = "us-east-1"
    s3_secure: bool = False

    # 数据库配置
    postgres_dsn: str

    # OCR 配置
    ocr_provider: str = "mock"

    # 日志配置
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    @property
    def s3_public_base_url(self) -> str:
        """获取 S3 公网访问基础 URL"""
        endpoint = self.s3_public_endpoint or self.s3_endpoint
        return f"{endpoint}/{self.s3_bucket}"


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()
