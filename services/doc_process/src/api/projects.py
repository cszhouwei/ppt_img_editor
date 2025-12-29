import logging
from uuid import uuid4
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from ..models.base import get_db
from ..models import Project

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
