import logging
from uuid import uuid4
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from io import BytesIO

from ..models.base import get_db
from ..models import Project
from ..config import get_settings, Settings
from ..storage.minio_client import get_minio_client
from ..utils.export import export_project_to_png
from minio import Minio

router = APIRouter()
logger = logging.getLogger(__name__)


# Request/Response models
class PageData(BaseModel):
    """Page 数据"""
    page_id: str
    image_url: str
    width: int
    height: int


class Layer(BaseModel):
    """图层数据 (patch 或 text)"""
    id: str
    kind: str  # "patch" or "text"
    # 其他字段根据 kind 不同而不同,这里使用 Dict 来保存所有字段
    # 前端可以自由添加字段


class CreateProjectRequest(BaseModel):
    """创建项目请求"""
    page: PageData
    layers: List[Dict[str, Any]] = []


class UpdateProjectRequest(BaseModel):
    """更新项目请求"""
    page: PageData
    layers: List[Dict[str, Any]]


class ProjectResponse(BaseModel):
    """项目响应"""
    project_id: str
    page: Dict[str, Any]
    layers: List[Dict[str, Any]]
    created_at: str = None
    updated_at: str = None


@router.post("", response_model=ProjectResponse)
async def create_project(
    request: CreateProjectRequest,
    db: Session = Depends(get_db)
) -> ProjectResponse:
    """
    创建新项目

    Args:
        request: 包含 page 和 layers

    Returns:
        ProjectResponse: 包含 project_id 和完整项目数据

    DoD:
        - 生成唯一 project_id
        - 存储 page_data 和 layers 到数据库
        - 返回完整项目信息
    """
    try:
        # 生成 project_id
        project_id = f"proj_{uuid4().hex[:12]}"

        # 创建 Project 记录
        project = Project(
            id=project_id,
            page_data=request.page.dict(),
            layers=[layer for layer in request.layers]
        )

        db.add(project)
        db.commit()
        db.refresh(project)

        logger.info(f"Created project: {project_id}")

        return ProjectResponse(**project.to_dict())

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create project: {e}")
        raise HTTPException(status_code=500, detail="Failed to create project")


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    db: Session = Depends(get_db)
) -> ProjectResponse:
    """
    获取项目

    Args:
        project_id: 项目 ID

    Returns:
        ProjectResponse: 完整项目数据

    DoD:
        - 验证 project_id 存在
        - 返回 page_data 和 layers
    """
    try:
        # 查询 project
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

        logger.info(f"Retrieved project: {project_id}")

        return ProjectResponse(**project.to_dict())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get project")


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    request: UpdateProjectRequest,
    db: Session = Depends(get_db)
) -> ProjectResponse:
    """
    更新项目 (保存)

    Args:
        project_id: 项目 ID
        request: 包含 page 和 layers

    Returns:
        ProjectResponse: 更新后的项目数据

    DoD:
        - 验证 project_id 存在
        - 更新 page_data 和 layers
        - 更新 updated_at 时间戳
        - 返回更新后的数据
    """
    try:
        # 查询 project
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

        # 更新数据
        project.page_data = request.page.dict()
        project.layers = [layer for layer in request.layers]
        project.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(project)

        logger.info(f"Updated project: {project_id}")

        return ProjectResponse(**project.to_dict())

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update project")


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    删除项目

    Args:
        project_id: 项目 ID

    Returns:
        成功消息

    DoD:
        - 验证 project_id 存在
        - 删除项目记录
    """
    try:
        # 查询 project
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

        # 删除
        db.delete(project)
        db.commit()

        logger.info(f"Deleted project: {project_id}")

        return {"message": f"Project {project_id} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete project")


class ExportResponse(BaseModel):
    """导出响应"""
    export_url: str


@router.post("/{project_id}/export/png", response_model=ExportResponse)
async def export_project_png(
    project_id: str,
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
    minio_client: Minio = Depends(get_minio_client)
) -> ExportResponse:
    """
    导出项目为 PNG 图像

    Args:
        project_id: 项目 ID

    Returns:
        ExportResponse: 包含导出文件的 URL

    DoD:
        - 验证 project_id 存在
        - 下载背景图
        - 按顺序渲染所有 layers (patch + text)
        - 上传导出文件到 MinIO
        - 返回导出文件 URL
    """
    try:
        # 查询 project
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

        logger.info(f"Exporting project {project_id} to PNG")

        # 导出项目为 PNG
        png_bytes = await export_project_to_png(
            page_data=project.page_data,
            layers=project.layers
        )

        logger.info(f"Project rendered successfully, size: {len(png_bytes)} bytes")

        # 生成导出文件名
        export_id = f"export_{uuid4().hex[:12]}"
        object_name = f"exports/{export_id}.png"

        # 上传到 MinIO
        try:
            minio_client.put_object(
                bucket_name=settings.s3_bucket,
                object_name=object_name,
                data=BytesIO(png_bytes),
                length=len(png_bytes),
                content_type="image/png"
            )
            logger.info(f"Uploaded export to MinIO: {object_name}")
        except Exception as e:
            logger.error(f"Failed to upload export to MinIO: {e}")
            raise HTTPException(status_code=500, detail="Failed to upload export to storage")

        # 构造导出 URL
        export_url = f"{settings.s3_public_base_url}/{object_name}"

        logger.info(f"Export completed successfully: {export_url}")

        return ExportResponse(export_url=export_url)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error exporting project {project_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to export project")
