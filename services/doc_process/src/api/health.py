from fastapi import APIRouter, Depends
from pydantic import BaseModel
from ..config import get_settings, Settings
from ..storage.minio_client import get_minio_client
from minio import Minio

router = APIRouter()


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    service: str
    version: str
    storage: str


@router.get("/health", response_model=HealthResponse)
async def health_check(
    settings: Settings = Depends(get_settings),
    minio_client: Minio = Depends(get_minio_client)
) -> HealthResponse:
    """
    健康检查接口

    DoD: 返回 200 OK,包含服务状态和存储连接状态
    """
    # 检查 MinIO 连接
    storage_status = "connected"
    try:
        # 检查 bucket 是否存在
        bucket_exists = minio_client.bucket_exists(settings.s3_bucket)
        if not bucket_exists:
            storage_status = "bucket_not_found"
    except Exception as e:
        storage_status = f"error: {str(e)}"

    return HealthResponse(
        status="ok",
        service="doc_process",
        version="0.1.0",
        storage=storage_status
    )
