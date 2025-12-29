"""Azure Computer Vision OCR Provider"""
import logging
import asyncio
from typing import List, Dict
from uuid import uuid4

from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.core.credentials import AzureKeyCredential
import httpx

from .base import OCRProvider, OCRCandidate

logger = logging.getLogger(__name__)


class AzureOCRProvider(OCRProvider):
    """
    Azure Computer Vision Read API Provider

    使用 Azure AI Vision 4.0 SDK 进行 OCR 识别
    """

    def __init__(self, endpoint: str, api_key: str):
        """
        初始化 Azure OCR Provider

        Args:
            endpoint: Azure Computer Vision endpoint (e.g., "https://xxx.cognitiveservices.azure.com/")
            api_key: Azure API key
        """
        self.endpoint = endpoint
        self.api_key = api_key
        self.client = ImageAnalysisClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(api_key)
        )
        logger.info(f"AzureOCRProvider initialized with endpoint: {endpoint}")

    async def analyze(
        self,
        image_url: str,
        page_id: str,
        width: int,
        height: int,
        lang_hints: List[str] = None
    ) -> List[OCRCandidate]:
        """
        使用 Azure Computer Vision Read API 分析图片

        Args:
            image_url: 图片 URL
            page_id: 页面 ID (用于生成唯一的 candidate ID)
            width: 图片宽度
            height: 图片高度
            lang_hints: 语言提示 (Azure 支持自动检测,此参数可选)

        Returns:
            候选框列表
        """
        try:
            logger.info(f"Analyzing image with Azure OCR: {image_url}")

            # 下载图片
            image_data = await self._download_image(image_url)

            # 调用 Azure Vision API (同步调用,在线程池中执行)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._analyze_sync,
                image_data
            )

            # 解析结果
            candidates = self._parse_result(result, page_id, width, height)

            logger.info(f"Azure OCR completed: {len(candidates)} candidates found")

            return candidates

        except Exception as e:
            logger.error(f"Azure OCR failed: {e}", exc_info=True)
            raise

    def _analyze_sync(self, image_data: bytes):
        """
        同步调用 Azure Vision API

        Args:
            image_data: 图片字节数据

        Returns:
            分析结果
        """
        result = self.client.analyze(
            image_data=image_data,
            visual_features=[VisualFeatures.READ]
        )
        return result

    async def _download_image(self, image_url: str) -> bytes:
        """
        下载图片

        Args:
            image_url: 图片 URL

        Returns:
            图片字节数据
        """
        # 如果 URL 使用 localhost,替换为 minio(Docker 内部网络)
        internal_url = image_url.replace("http://localhost:9000", "http://minio:9000")

        async with httpx.AsyncClient() as client:
            response = await client.get(internal_url, timeout=30.0)
            if response.status_code != 200:
                raise ValueError(f"Failed to download image: {image_url}")
            return response.content

    def _parse_result(
        self,
        result,
        page_id: str,
        image_width: int,
        image_height: int
    ) -> List[OCRCandidate]:
        """
        解析 Azure Vision 结果

        Args:
            result: Azure Vision 分析结果
            page_id: 页面 ID
            image_width: 图片宽度
            image_height: 图片高度

        Returns:
            候选框列表
        """
        candidates = []

        if not result.read or not result.read.blocks:
            logger.warning("No text detected in image")
            return candidates

        candidate_index = 0

        # 遍历所有 blocks (段落)
        for block in result.read.blocks:
            # 遍历所有 lines (行)
            for line in block.lines:
                # 生成唯一 ID
                candidate_id = f"{page_id}_c_{candidate_index:03d}"
                candidate_index += 1

                # 提取文本
                text = line.text

                # 计算平均置信度 (基于所有 words)
                if line.words:
                    confidence = sum(word.confidence for word in line.words) / len(line.words)
                else:
                    confidence = 0.0

                # 提取 bounding polygon (通常是 4 个点)
                polygon = line.bounding_polygon
                if len(polygon) >= 4:
                    # Azure 返回的是 [Point(x, y), ...]
                    quad = [
                        [int(polygon[0].x), int(polygon[0].y)],
                        [int(polygon[1].x), int(polygon[1].y)],
                        [int(polygon[2].x), int(polygon[2].y)],
                        [int(polygon[3].x), int(polygon[3].y)]
                    ]
                else:
                    # 如果点数不足,跳过
                    logger.warning(f"Skipping line with insufficient polygon points: {len(polygon)}")
                    continue

                # 计算 axis-aligned bounding box
                bbox = self._quad_to_bbox(quad)

                # 计算角度 (基于 quad 的第一条边)
                angle_deg = self._calculate_angle(quad)

                # 创建候选框
                candidate = OCRCandidate(
                    id=candidate_id,
                    text=text,
                    confidence=confidence,
                    quad=quad,
                    bbox=bbox,
                    angle_deg=angle_deg
                )

                candidates.append(candidate)

        return candidates

    def _quad_to_bbox(self, quad: List[List[int]]) -> Dict[str, int]:
        """
        从 quad 计算 axis-aligned bounding box

        Args:
            quad: [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]

        Returns:
            {"x": ..., "y": ..., "w": ..., "h": ...}
        """
        xs = [p[0] for p in quad]
        ys = [p[1] for p in quad]

        x_min = min(xs)
        y_min = min(ys)
        x_max = max(xs)
        y_max = max(ys)

        return {
            "x": x_min,
            "y": y_min,
            "w": x_max - x_min,
            "h": y_max - y_min
        }

    def _calculate_angle(self, quad: List[List[int]]) -> float:
        """
        计算 quad 的旋转角度

        Args:
            quad: [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]

        Returns:
            角度 (度),范围 [-90, 90]
        """
        import math

        # 使用第一条边 (p0 -> p1) 计算角度
        dx = quad[1][0] - quad[0][0]
        dy = quad[1][1] - quad[0][1]

        # 计算角度 (弧度转度)
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad)

        # 归一化到 [-90, 90]
        if angle_deg > 90:
            angle_deg -= 180
        elif angle_deg < -90:
            angle_deg += 180

        return round(angle_deg, 2)
