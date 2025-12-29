import logging
from uuid import uuid4
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..config import get_settings, Settings
from ..models.base import get_db
from ..models import Page, Candidate, Patch
from ..ocr import MockOCRProvider
from ..storage.minio_client import get_minio_client
from ..patch import generate_patch
from ..utils.text_style import estimate_text_style
from minio import Minio
import httpx
import io
import numpy as np
import cv2

router = APIRouter()
logger = logging.getLogger(__name__)


# Request/Response models
class CreatePageRequest(BaseModel):
    """创建 page 请求"""
    image_url: str
    width: int
    height: int


class CreatePageResponse(BaseModel):
    """创建 page 响应"""
    page_id: str


class AnalyzeRequest(BaseModel):
    """OCR 分析请求"""
    provider: str = "mock"
    lang_hints: List[str] = ["zh-Hans", "en"]


class CandidateResponse(BaseModel):
    """候选框响应"""
    id: str
    text: str
    confidence: float
    quad: List[List[int]]
    bbox: dict
    angle_deg: float


class AnalyzeResponse(BaseModel):
    """OCR 分析响应"""
    page_id: str
    width: int
    height: int
    candidates: List[CandidateResponse]


class PatchRequest(BaseModel):
    """生成 patch 请求"""
    candidate_id: str
    padding_px: int = 8
    mode: str = "auto"  # auto|solid|gradient|inpaint
    algo_version: str = "v1"


class PatchResponse(BaseModel):
    """生成 patch 响应"""
    patch: dict


class EstimateStyleRequest(BaseModel):
    """估计文本样式请求"""
    candidate_id: str


class EstimateStyleResponse(BaseModel):
    """估计文本样式响应"""
    candidate_id: str
    style: dict


@router.post("", response_model=CreatePageResponse)
async def create_page(
    request: CreatePageRequest,
    db: Session = Depends(get_db)
) -> CreatePageResponse:
    """
    创建 Page

    Args:
        request: 包含 image_url, width, height

    Returns:
        CreatePageResponse: 包含 page_id

    DoD:
        - 生成唯一 page_id
        - 存储到数据库
        - 返回 page_id
    """
    try:
        # 生成 page_id
        page_id = f"page_{uuid4().hex[:12]}"

        # 创建 Page 记录
        page = Page(
            id=page_id,
            image_url=request.image_url,
            width=request.width,
            height=request.height
        )

        db.add(page)
        db.commit()
        db.refresh(page)

        logger.info(f"Created page: {page_id}")

        return CreatePageResponse(page_id=page_id)

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create page: {e}")
        raise HTTPException(status_code=500, detail="Failed to create page")


@router.post("/{page_id}/analyze", response_model=AnalyzeResponse)
async def analyze_page(
    page_id: str,
    request: AnalyzeRequest,
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db)
) -> AnalyzeResponse:
    """
    OCR 分析页面

    Args:
        page_id: 页面 ID
        request: 包含 provider 和 lang_hints

    Returns:
        AnalyzeResponse: 包含 page_id, width, height, candidates

    DoD:
        - 验证 page_id 存在
        - 调用 OCR provider (mock)
        - 将候选框存储到数据库
        - 返回候选框列表
    """
    try:
        # 查询 page
        page = db.query(Page).filter(Page.id == page_id).first()
        if not page:
            raise HTTPException(status_code=404, detail=f"Page not found: {page_id}")

        # 使用 Mock OCR provider
        if request.provider == "mock" or settings.ocr_provider == "mock":
            ocr_provider = MockOCRProvider()
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported OCR provider: {request.provider}"
            )

        # 调用 OCR
        ocr_candidates = await ocr_provider.analyze(
            image_url=page.image_url,
            page_id=page_id,
            width=page.width,
            height=page.height,
            lang_hints=request.lang_hints
        )

        # 删除旧的候选框(如果重新分析)
        db.query(Candidate).filter(Candidate.page_id == page_id).delete()

        # 存储候选框到数据库
        candidates = []
        for ocr_cand in ocr_candidates:
            candidate = Candidate(
                id=ocr_cand.id,
                page_id=page_id,
                text=ocr_cand.text,
                confidence=ocr_cand.confidence,
                quad=ocr_cand.quad,
                bbox=ocr_cand.bbox,
                angle_deg=ocr_cand.angle_deg
            )
            db.add(candidate)
            candidates.append(candidate)

        db.commit()

        logger.info(f"Analyzed page {page_id}: {len(candidates)} candidates")

        return AnalyzeResponse(
            page_id=page_id,
            width=page.width,
            height=page.height,
            candidates=[
                CandidateResponse(**cand.to_dict()) for cand in candidates
            ]
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to analyze page {page_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze page")


@router.get("/{page_id}/candidates", response_model=AnalyzeResponse)
async def get_candidates(
    page_id: str,
    db: Session = Depends(get_db)
) -> AnalyzeResponse:
    """
    获取页面的候选框列表

    Args:
        page_id: 页面 ID

    Returns:
        AnalyzeResponse: 包含 page_id, width, height, candidates
    """
    try:
        # 查询 page
        page = db.query(Page).filter(Page.id == page_id).first()
        if not page:
            raise HTTPException(status_code=404, detail=f"Page not found: {page_id}")

        # 查询 candidates
        candidates = db.query(Candidate).filter(Candidate.page_id == page_id).all()

        logger.info(f"Retrieved {len(candidates)} candidates for page {page_id}")

        return AnalyzeResponse(
            page_id=page_id,
            width=page.width,
            height=page.height,
            candidates=[
                CandidateResponse(**cand.to_dict()) for cand in candidates
            ]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get candidates for page {page_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get candidates")
@router.post("/{page_id}/patch", response_model=PatchResponse)
async def generate_patch_for_candidate(
    page_id: str,
    request: PatchRequest,
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
    minio_client: Minio = Depends(get_minio_client)
) -> PatchResponse:
    """
    为指定的 candidate 生成 patch

    Args:
        page_id: 页面 ID
        request: 包含 candidate_id, padding_px, mode, algo_version

    Returns:
        PatchResponse: 包含 patch 信息

    DoD:
        - 验证 page_id 和 candidate_id 存在
        - 下载原图
        - 调用 patch generation pipeline
        - 上传 patch 到 MinIO
        - 保存 patch 记录到数据库
        - 返回 patch 信息
    """
    try:
        # 验证 page 存在
        page = db.query(Page).filter(Page.id == page_id).first()
        if not page:
            raise HTTPException(status_code=404, detail=f"Page not found: {page_id}")

        # 验证 candidate 存在
        candidate = db.query(Candidate).filter(
            Candidate.id == request.candidate_id,
            Candidate.page_id == page_id
        ).first()
        if not candidate:
            raise HTTPException(
                status_code=404,
                detail=f"Candidate not found: {request.candidate_id}"
            )

        logger.info(f"Generating patch for page={page_id}, candidate={request.candidate_id}")

        # 下载原图
        async with httpx.AsyncClient() as client:
            image_response = await client.get(page.image_url, timeout=30.0)
            if image_response.status_code != 200:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to download image: {image_response.status_code}"
                )
            image_bytes = image_response.content

        # 调用 patch generation pipeline
        candidate_data = {
            "quad": candidate.quad,
            "bbox": candidate.bbox
        }

        result = generate_patch(
            image_bytes=image_bytes,
            candidate=candidate_data,
            padding_px=request.padding_px,
            mode=request.mode,
            algo_version=request.algo_version
        )

        if not result.success:
            raise HTTPException(
                status_code=500,
                detail=f"Patch generation failed: {result.error}"
            )

        # 生成 patch_id
        patch_id = f"p_{uuid4().hex[:12]}"

        # 上传 patch 到 MinIO
        object_name = f"patches/{patch_id}.png"

        try:
            minio_client.put_object(
                bucket_name=settings.s3_bucket,
                object_name=object_name,
                data=io.BytesIO(result.patch_bytes),
                length=len(result.patch_bytes),
                content_type="image/png"
            )
            logger.info(f"Uploaded patch to MinIO: {object_name}")
        except Exception as e:
            logger.error(f"Failed to upload patch to MinIO: {e}")
            raise HTTPException(status_code=500, detail="Failed to upload patch to storage")

        # 构造 patch URL
        patch_url = f"{settings.s3_public_base_url}/{object_name}"

        # 保存 patch 记录到数据库
        patch_record = Patch(
            id=patch_id,
            page_id=page_id,
            candidate_id=request.candidate_id,
            bbox=result.bbox,
            image_url=patch_url,
            debug_info=result.debug_info
        )

        db.add(patch_record)
        db.commit()
        db.refresh(patch_record)

        logger.info(f"Patch generated successfully: {patch_id}")

        return PatchResponse(
            patch=patch_record.to_dict()
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error generating patch: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate patch")


@router.post("/{page_id}/estimate-style", response_model=EstimateStyleResponse)
async def estimate_style_for_candidate(
    page_id: str,
    request: EstimateStyleRequest,
    db: Session = Depends(get_db)
) -> EstimateStyleResponse:
    """
    为指定的 candidate 估计文本样式

    Args:
        page_id: 页面 ID
        request: 包含 candidate_id

    Returns:
        EstimateStyleResponse: 包含估计的样式

    DoD:
        - 验证 page_id 和 candidate_id 存在
        - 下载原图
        - 估计字体颜色、大小、粗细
        - 返回样式信息
    """
    try:
        # 验证 page 存在
        page = db.query(Page).filter(Page.id == page_id).first()
        if not page:
            raise HTTPException(status_code=404, detail=f"Page not found: {page_id}")

        # 验证 candidate 存在
        candidate = db.query(Candidate).filter(
            Candidate.id == request.candidate_id,
            Candidate.page_id == page_id
        ).first()
        if not candidate:
            raise HTTPException(
                status_code=404,
                detail=f"Candidate not found: {request.candidate_id}"
            )

        logger.info(f"Estimating style for page={page_id}, candidate={request.candidate_id}")

        # 下载原图
        async with httpx.AsyncClient() as client:
            image_response = await client.get(page.image_url, timeout=30.0)
            if image_response.status_code != 200:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to download image: {image_response.status_code}"
                )
            image_bytes = image_response.content

        # 解码图像
        image_array = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

        if image is None:
            raise HTTPException(status_code=500, detail="Failed to decode image")

        # 估计样式
        candidate_data = {
            "quad": candidate.quad,
            "bbox": candidate.bbox
        }

        style = estimate_text_style(image, candidate_data)

        logger.info(f"Style estimated successfully for {request.candidate_id}")

        return EstimateStyleResponse(
            candidate_id=request.candidate_id,
            style=style
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error estimating style: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to estimate style")
