"""OCR provider base class"""
from typing import List, Dict, Any
from pydantic import BaseModel


class OCRCandidate(BaseModel):
    """OCR 识别结果候选框"""
    id: str
    text: str
    confidence: float
    quad: List[List[int]]  # [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
    bbox: Dict[str, int]  # {"x": 120, "y": 80, "w": 420, "h": 64}
    angle_deg: float = 0.0


class OCRProvider:
    """OCR provider 抽象基类"""

    async def analyze(
        self,
        image_url: str,
        page_id: str,
        width: int,
        height: int,
        lang_hints: List[str] = None
    ) -> List[OCRCandidate]:
        """
        分析图片,返回候选框列表

        Args:
            image_url: 图片 URL
            page_id: 页面 ID
            width: 图片宽度
            height: 图片高度
            lang_hints: 语言提示,例如 ["zh-Hans", "en"]

        Returns:
            候选框列表
        """
        raise NotImplementedError
