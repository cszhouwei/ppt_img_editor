from functools import lru_cache
from minio import Minio
from ..config import get_settings


@lru_cache()
def get_minio_client() -> Minio:
    """
    获取 MinIO 客户端单例

    Returns:
        Minio: MinIO 客户端实例
    """
    settings = get_settings()

    # 移除协议前缀(Minio 客户端不需要)
    endpoint = settings.s3_endpoint.replace("http://", "").replace("https://", "")

    client = Minio(
        endpoint=endpoint,
        access_key=settings.s3_access_key,
        secret_key=settings.s3_secret_key,
        secure=settings.s3_secure,
        region=settings.s3_region
    )

    return client
