import io
import logging
from uuid import uuid4
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from pydantic import BaseModel
from minio import Minio

from ..config import get_settings, Settings
from ..storage.minio_client import get_minio_client
from ..utils.image import get_image_dimensions
from ..utils.hash import compute_sha256

router = APIRouter()
logger = logging.getLogger(__name__)


class AssetUploadResponse(BaseModel):
    """资源上传响应"""
    asset_id: str
    image_url: str
    width: int
    height: int
    sha256: str


@router.post("/upload", response_model=AssetUploadResponse)
async def upload_asset(
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
    minio_client: Minio = Depends(get_minio_client)
) -> AssetUploadResponse:
    """
    上传图片资源

    Args:
        file: 上传的图片文件(支持 PNG, JPEG, JPG)

    Returns:
        AssetUploadResponse: 包含 asset_id, image_url, 宽高和 SHA256

    DoD:
        - 验证文件格式
        - 计算 SHA256
        - 获取图片尺寸
        - 上传到 MinIO
        - 返回可访问的 image_url
    """
    # 验证文件类型
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    allowed_types = ["image/png", "image/jpeg", "image/jpg"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image type. Allowed types: {', '.join(allowed_types)}"
        )

    try:
        # 读取文件内容
        contents = await file.read()

        # 计算 SHA256
        sha256 = compute_sha256(contents)
        logger.info(f"File SHA256: {sha256}")

        # 获取图片尺寸
        try:
            width, height = get_image_dimensions(contents)
            logger.info(f"Image dimensions: {width}x{height}")
        except Exception as e:
            logger.error(f"Failed to get image dimensions: {e}")
            raise HTTPException(status_code=400, detail="Invalid image file")

        # 生成 asset_id
        asset_id = f"ast_{uuid4().hex[:12]}"

        # 确定文件扩展名
        extension = "png" if file.content_type == "image/png" else "jpg"
        object_name = f"assets/{asset_id}.{extension}"

        # 上传到 MinIO
        try:
            minio_client.put_object(
                bucket_name=settings.s3_bucket,
                object_name=object_name,
                data=io.BytesIO(contents),
                length=len(contents),
                content_type=file.content_type
            )
            logger.info(f"Uploaded to MinIO: {object_name}")
        except Exception as e:
            logger.error(f"Failed to upload to MinIO: {e}")
            raise HTTPException(status_code=500, detail="Failed to upload file to storage")

        # 构造公网访问 URL
        image_url = f"{settings.s3_public_base_url}/{object_name}"

        return AssetUploadResponse(
            asset_id=asset_id,
            image_url=image_url,
            width=width,
            height=height,
            sha256=sha256
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during upload: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
