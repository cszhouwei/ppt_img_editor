"""Mock OCR provider for testing"""
import json
import logging
from pathlib import Path
from typing import List
from .base import OCRProvider, OCRCandidate

logger = logging.getLogger(__name__)


class MockOCRProvider(OCRProvider):
    """Mock OCR provider,从预定义 JSON 文件返回结果"""

    def __init__(self, mock_dir: str = None):
        """
        Args:
            mock_dir: Mock 数据目录,默认为 services/doc_process/mock/
        """
        if mock_dir is None:
            # 默认 mock 目录
            current_file = Path(__file__)
            self.mock_dir = current_file.parent.parent.parent / "mock"
        else:
            self.mock_dir = Path(mock_dir)

        self.mock_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"MockOCRProvider initialized with mock_dir: {self.mock_dir}")

    async def analyze(
        self,
        image_url: str,
        page_id: str,
        width: int,
        height: int,
        lang_hints: List[str] = None
    ) -> List[OCRCandidate]:
        """
        从 mock 数据文件返回候选框

        优先尝试加载:
        1. mock/page_{page_id}.json
        2. mock/default.json

        如果都不存在,返回空列表
        """
        # 尝试加载特定 page 的 mock 数据
        page_mock_file = self.mock_dir / f"page_{page_id}.json"
        default_mock_file = self.mock_dir / "default.json"

        mock_file = None
        if page_mock_file.exists():
            mock_file = page_mock_file
            logger.info(f"Using page-specific mock file: {page_mock_file}")
        elif default_mock_file.exists():
            mock_file = default_mock_file
            logger.info(f"Using default mock file: {default_mock_file}")
        else:
            logger.warning(
                f"No mock file found for page_id={page_id}. "
                f"Tried: {page_mock_file}, {default_mock_file}"
            )
            return []

        try:
            with open(mock_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            candidates = []
            for idx, item in enumerate(data.get("candidates", [])):
                # 如果 mock 数据没有 id,自动生成
                if "id" not in item:
                    item["id"] = f"c_{idx + 1:03d}"

                # 确保有 bbox
                if "bbox" not in item and "quad" in item:
                    quad = item["quad"]
                    xs = [p[0] for p in quad]
                    ys = [p[1] for p in quad]
                    item["bbox"] = {
                        "x": min(xs),
                        "y": min(ys),
                        "w": max(xs) - min(xs),
                        "h": max(ys) - min(ys)
                    }

                candidates.append(OCRCandidate(**item))

            logger.info(f"Loaded {len(candidates)} candidates from {mock_file}")
            return candidates

        except Exception as e:
            logger.error(f"Failed to load mock data from {mock_file}: {e}")
            return []
