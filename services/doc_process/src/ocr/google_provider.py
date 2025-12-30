"""Google Cloud Vision OCR Provider"""
import asyncio
import logging
from typing import List, Optional
import httpx

from google.cloud import vision
from google.oauth2 import service_account

from .base import OCRProvider, OCRCandidate

logger = logging.getLogger(__name__)


class GoogleOCRProvider(OCRProvider):
    """
    Google Cloud Vision Document Text Detection Provider

    使用 Google Cloud Vision API 的 DOCUMENT_TEXT_DETECTION 功能
    识别文档图像中的文字

    特点:
    - 高准确率的文字识别
    - 支持 100+ 种语言
    - 返回分层结构 (Page -> Block -> Paragraph -> Word)
    - 支持旋转文字检测
    - 支持手写文字识别
    """

    def __init__(self, credentials_path: Optional[str] = None, credentials_json: Optional[str] = None):
        """
        初始化 Google Cloud Vision 客户端

        Args:
            credentials_path: 服务账号 JSON 文件路径
            credentials_json: 服务账号 JSON 字符串
        """
        if credentials_path:
            # 从文件加载凭证
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path
            )
            self.client = vision.ImageAnnotatorClient(credentials=credentials)
        elif credentials_json:
            # 从 JSON 字符串加载凭证
            import json
            credentials_info = json.loads(credentials_json)
            credentials = service_account.Credentials.from_service_account_info(
                credentials_info
            )
            self.client = vision.ImageAnnotatorClient(credentials=credentials)
        else:
            # 使用默认凭证 (GOOGLE_APPLICATION_CREDENTIALS 环境变量)
            self.client = vision.ImageAnnotatorClient()

    async def analyze(
        self,
        image_url: str,
        page_id: str,
        width: int,
        height: int,
        lang_hints: List[str] = None
    ) -> List[OCRCandidate]:
        """
        使用 Google Cloud Vision 分析图像

        Args:
            image_url: 图像 URL
            page_id: 页面 ID
            width: 图像宽度
            height: 图像高度
            lang_hints: 语言提示列表 (例如 ["zh-Hans", "en"])

        Returns:
            OCRCandidate 列表
        """
        try:
            # 下载图像
            logger.info(f"Downloading image from {image_url}")
            image_data = await self._download_image(image_url)

            # 调用 Google Cloud Vision API (同步 -> 异步)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self._analyze_sync,
                image_data,
                lang_hints
            )

            # 解析结果
            candidates = self._parse_result(response, page_id, width, height)

            logger.info(f"Google Cloud Vision OCR completed: {len(candidates)} candidates")

            return candidates

        except Exception as e:
            logger.error(f"Google Cloud Vision OCR failed: {e}", exc_info=True)
            raise

    async def _download_image(self, url: str) -> bytes:
        """下载图像"""
        # 如果 URL 使用 localhost,替换为 minio(Docker 内部网络)
        internal_url = url.replace("http://localhost:9000", "http://minio:9000")

        async with httpx.AsyncClient() as client:
            response = await client.get(internal_url, timeout=30.0)
            if response.status_code != 200:
                raise ValueError(f"Failed to download image: {url}")
            return response.content

    def _analyze_sync(self, image_data: bytes, lang_hints: Optional[List[str]] = None) -> vision.AnnotateImageResponse:
        """
        同步调用 Google Cloud Vision API

        Args:
            image_data: 图像字节数据
            lang_hints: 语言提示

        Returns:
            Google Cloud Vision 响应
        """
        # 构造图像对象
        image = vision.Image(content=image_data)

        # 构造图像上下文 (语言提示)
        image_context = None
        if lang_hints:
            # 转换语言代码格式
            # Google Cloud Vision 使用 BCP-47 格式: zh-Hans -> zh, en -> en
            google_lang_hints = []
            for lang in lang_hints:
                if lang == "zh-Hans":
                    google_lang_hints.append("zh")
                elif lang == "zh-Hant":
                    google_lang_hints.append("zh-TW")
                else:
                    google_lang_hints.append(lang)

            image_context = vision.ImageContext(language_hints=google_lang_hints)

        # 调用 DOCUMENT_TEXT_DETECTION
        response = self.client.document_text_detection(
            image=image,
            image_context=image_context
        )

        if response.error.message:
            raise Exception(f"Google Cloud Vision API error: {response.error.message}")

        return response

    def _parse_result(
        self,
        response: vision.AnnotateImageResponse,
        page_id: str,
        image_width: int,
        image_height: int
    ) -> List[OCRCandidate]:
        """
        解析 Google Cloud Vision 结果为 OCRCandidate 格式

        Google Cloud Vision 返回结构:
        - full_text_annotation.pages[0]
          - blocks[]
            - paragraphs[]
              - words[]
                - symbols[]

        我们提取 paragraph 级别作为候选框 (相当于一行文字)

        Args:
            response: Google Cloud Vision 响应
            page_id: 页面 ID
            image_width: 图像宽度
            image_height: 图像高度

        Returns:
            OCRCandidate 列表
        """
        candidates = []
        candidate_index = 0

        # 获取文档注释
        full_text = response.full_text_annotation
        if not full_text or not full_text.pages:
            logger.warning("No text detected in image")
            return candidates

        # 遍历页面 (通常只有一页)
        for page in full_text.pages:
            # 遍历块
            for block in page.blocks:
                # 遍历段落 (我们将段落作为候选框)
                for paragraph in block.paragraphs:
                    # 提取文本
                    text = self._extract_text_from_paragraph(paragraph)

                    if not text.strip():
                        continue

                    # 生成唯一 ID
                    candidate_id = f"{page_id}_c_{candidate_index:03d}"
                    candidate_index += 1

                    # 计算置信度 (段落中所有单词的平均置信度)
                    confidence = self._calculate_confidence(paragraph)

                    # 提取边界框
                    quad = self._extract_quad(paragraph.bounding_box)
                    bbox = self._quad_to_bbox(quad)

                    # 计算角度
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

    def _extract_text_from_paragraph(self, paragraph) -> str:
        """
        从段落中提取文本，使用 DetectedBreak 智能处理空格

        通过 Google Cloud Vision 的 DetectedBreak 信息，
        我们可以精确知道每个字符后面是否需要空格，
        避免在中文字符间插入多余空格。

        DetectedBreak 类型说明：
        - SPACE: 常规空格
        - SURE_SPACE: 确定的空格（较宽）
        - EOL_SURE_SPACE: 行尾换行造成的空格
        - HYPHEN: 连字符（不添加空格）
        - LINE_BREAK: 段落结束的换行（不添加空格）
        - UNKNOWN: 未知类型（不添加空格，避免误加）
        """
        text_parts = []

        for word in paragraph.words:
            word_chars = []

            for symbol in word.symbols:
                # 添加字符本身
                word_chars.append(symbol.text)

                # 检查字符后是否有 break (空格、换行等)
                if hasattr(symbol, 'property') and symbol.property:
                    detected_break = symbol.property.detected_break

                    if detected_break:
                        break_type = detected_break.type

                        # 根据 break 类型决定是否添加空格
                        # 只在明确需要空格的类型中添加
                        if break_type.name in ['SPACE', 'SURE_SPACE', 'EOL_SURE_SPACE']:
                            word_chars.append(' ')

                        # 调试日志（可选，生产环境可注释）
                        if logger.isEnabledFor(logging.DEBUG):
                            logger.debug(
                                f"Symbol '{symbol.text}' has break type: {break_type.name}"
                            )

            text_parts.append("".join(word_chars))

        # 直接拼接，不再添加额外空格
        # 因为空格信息已经在 DetectedBreak 中处理了
        result = "".join(text_parts)

        # 调试日志
        logger.debug(f"Extracted text from paragraph: '{result}'")

        return result

    def _calculate_confidence(self, paragraph) -> float:
        """计算段落的平均置信度"""
        confidences = []
        for word in paragraph.words:
            if hasattr(word, 'confidence'):
                confidences.append(word.confidence)

        if confidences:
            return sum(confidences) / len(confidences)
        else:
            # Google Cloud Vision 不总是提供置信度,默认返回 0.9
            return 0.9

    def _extract_quad(self, bounding_box) -> List[List[int]]:
        """
        从 Google Cloud Vision BoundingPoly 提取四边形坐标

        Args:
            bounding_box: BoundingPoly 对象

        Returns:
            [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
        """
        vertices = bounding_box.vertices
        quad = [
            [vertices[0].x, vertices[0].y],  # 左上
            [vertices[1].x, vertices[1].y],  # 右上
            [vertices[2].x, vertices[2].y],  # 右下
            [vertices[3].x, vertices[3].y]   # 左下
        ]
        return quad

    def _quad_to_bbox(self, quad: List[List[int]]) -> dict:
        """
        从四边形计算轴对齐边界框

        Args:
            quad: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]

        Returns:
            {"x": int, "y": int, "w": int, "h": int}
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
        从四边形计算旋转角度

        使用左上到右上的边计算角度

        Args:
            quad: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]

        Returns:
            角度 (度数), 范围 [-180, 180]
        """
        import math

        # 使用左上 (quad[0]) 到右上 (quad[1]) 的向量
        dx = quad[1][0] - quad[0][0]
        dy = quad[1][1] - quad[0][1]

        # 计算角度 (弧度转度数)
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad)

        return angle_deg
