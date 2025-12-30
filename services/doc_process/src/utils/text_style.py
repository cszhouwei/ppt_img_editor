"""Text style estimation utilities"""
import numpy as np
import cv2
from typing import Dict, List, Tuple, Optional


def estimate_text_color(
    image: np.ndarray,
    mask: np.ndarray,
    method: str = "kmeans"
) -> Tuple[int, int, int, int]:
    """
    从原图中估计文字颜色 (改进版)

    Args:
        image: 原图 (H, W, 3) BGR
        mask: 文字 mask (H, W), 255 表示文字区域
        method: 估计方法 ("kmeans", "median", "mean", "edge")

    Returns:
        RGBA 颜色 (r, g, b, a)

    改进算法:
    1. 使用形态学腐蚀收缩 mask，避免边缘背景干扰
    2. K-means 聚类找主色调（适合纯色文字）
    3. 边缘增强方法（提取笔画中心色）
    4. 智能过滤异常值
    """
    # 提取文字像素
    text_pixels = image[mask > 0]  # (N, 3) BGR

    if len(text_pixels) == 0:
        return (30, 30, 30, 255)

    # 转换为 RGB
    text_pixels_rgb = text_pixels[:, ::-1]  # BGR -> RGB

    # 方法 1: K-means 聚类找主色调 (推荐)
    if method == "kmeans":
        # 使用形态学腐蚀缩小 mask，避免边缘背景
        kernel = np.ones((3, 3), np.uint8)
        eroded_mask = cv2.erode(mask, kernel, iterations=2)

        # 重新提取像素
        eroded_pixels = image[eroded_mask > 0]
        if len(eroded_pixels) < 10:
            eroded_pixels = text_pixels  # 退回原像素

        eroded_pixels_rgb = eroded_pixels[:, ::-1]

        # K-means 聚类 (k=3, 找文字、阴影、高光)
        n_clusters = min(3, len(eroded_pixels_rgb))
        if n_clusters >= 2:
            pixels_float = eroded_pixels_rgb.astype(np.float32)
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
            _, labels, centers = cv2.kmeans(
                pixels_float, n_clusters, None, criteria, 10, cv2.KMEANS_PP_CENTERS
            )

            # 找最大的簇（主色调）
            unique, counts = np.unique(labels, return_counts=True)
            main_cluster_idx = unique[np.argmax(counts)]
            r, g, b = centers[main_cluster_idx].astype(int)
        else:
            # 样本太少，使用中位数
            r, g, b = np.median(eroded_pixels_rgb, axis=0).astype(int)

    # 方法 2: 边缘提取（提取笔画中心）
    elif method == "edge":
        # 收缩 mask 到笔画中心
        kernel = np.ones((5, 5), np.uint8)
        eroded_mask = cv2.erode(mask, kernel, iterations=3)

        center_pixels = image[eroded_mask > 0]
        if len(center_pixels) < 10:
            center_pixels = text_pixels

        center_pixels_rgb = center_pixels[:, ::-1]
        r, g, b = np.median(center_pixels_rgb, axis=0).astype(int)

    # 方法 3: 改进的中位数（排除异常值）
    elif method == "median":
        # 计算亮度
        luminance = 0.299 * text_pixels_rgb[:, 0] + 0.587 * text_pixels_rgb[:, 1] + 0.114 * text_pixels_rgb[:, 2]

        # 排除极端值 (保留 20th-80th 百分位)
        p20, p80 = np.percentile(luminance, [20, 80])
        valid_mask = (luminance >= p20) & (luminance <= p80)

        if np.sum(valid_mask) > 10:
            filtered_pixels = text_pixels_rgb[valid_mask]
        else:
            filtered_pixels = text_pixels_rgb

        r, g, b = np.median(filtered_pixels, axis=0).astype(int)

    # 方法 4: 均值
    else:  # mean
        r, g, b = np.mean(text_pixels_rgb, axis=0).astype(int)

    # 限制范围
    r = max(0, min(255, r))
    g = max(0, min(255, g))
    b = max(0, min(255, b))

    return (r, g, b, 255)


def estimate_font_size(
    bbox: Dict[str, int],
    scale_factor: float = 0.75
) -> int:
    """
    从 bbox 估计字号 (简单版本，保留用于向后兼容)

    Args:
        bbox: {"x": ..., "y": ..., "w": ..., "h": ...}
        scale_factor: bbox 高度到字号的缩放系数 (经验值)

    Returns:
        估计的字号 (px)

    算法:
    fontSize ≈ bbox_h * scale_factor
    """
    bbox_h = bbox.get("h", 0)
    font_size = int(bbox_h * scale_factor)

    # 限制最小值
    font_size = max(12, font_size)

    return font_size


def estimate_font_size_adaptive(
    bbox: Dict[str, int],
    text: str,
    confidence: float = 1.0
) -> int:
    """
    自适应估计字号 (改进版)

    根据文本内容和 bbox 高度动态调整缩放系数，
    相比固定系数有更高的准确度。

    Args:
        bbox: {"x": ..., "y": ..., "w": ..., "h": ...}
        text: 文本内容
        confidence: OCR 置信度 (0-1)

    Returns:
        估计的字号 (px)

    算法改进：
    1. 根据文本类型（中文/英文大小写）动态选择缩放系数
    2. 根据 bbox 高度分段调整（小字体和大字体比例不同）
    3. 低置信度时保守估计
    """
    bbox_h = bbox.get("h", 0)

    if bbox_h == 0:
        return 12

    # Step 1: 分析文本类型，选择基础缩放系数
    has_chinese = any('\u4e00' <= c <= '\u9fff' for c in text)
    has_uppercase = any(c.isupper() for c in text if c.isalpha())
    has_lowercase = any(c.islower() for c in text if c.isalpha())

    if has_chinese:
        # 中文方块字，填充率较高
        base_scale = 0.80
    elif has_uppercase and not has_lowercase:
        # 纯大写英文，字符较高
        base_scale = 0.70
    elif has_lowercase and not has_uppercase:
        # 纯小写英文，字符较矮（有 descender）
        base_scale = 0.85
    else:
        # 混合或默认
        base_scale = 0.75

    # Step 2: 根据 bbox 高度分段微调
    # 小字体往往填充率更高，大字体填充率略低
    if bbox_h < 20:
        height_adjust = 1.05  # +5%
    elif bbox_h < 40:
        height_adjust = 1.0   # 不调整
    elif bbox_h < 60:
        height_adjust = 0.97  # -3%
    else:
        height_adjust = 0.94  # -6%

    # Step 3: 置信度调整
    # 低置信度时保守估计，避免过大
    if confidence < 0.7:
        confidence_adjust = 0.95
    elif confidence < 0.85:
        confidence_adjust = 0.98
    else:
        confidence_adjust = 1.0

    # 计算最终字号
    scale = base_scale * height_adjust * confidence_adjust
    font_size = int(bbox_h * scale)

    # 限制范围
    font_size = max(12, min(font_size, 500))

    return font_size


def estimate_font_size_from_pixels(
    image: np.ndarray,
    mask: np.ndarray,
    bbox: Dict[str, int],
    text: str = ""
) -> int:
    """
    通过像素分布分析估计字号 (精细版)

    分析文字区域的垂直投影，测量实际的字符主体高度（cap-height），
    然后根据字体学原理推算字号。

    Args:
        image: 原图 (H, W, 3) BGR
        mask: 文字 mask (H, W), 255 表示文字区域
        bbox: 边界框
        text: 文本内容（用于回退）

    Returns:
        估计的字号 (px)

    算法原理：
    1. 计算文字区域的垂直投影（Y 轴方向的像素密度）
    2. 找出主体区域（去除稀疏的 ascender/descender 部分）
    3. 主体高度 ≈ cap-height ≈ font_size * 0.65-0.70
    4. 反推 font_size
    """
    bbox_h = bbox.get("h", 0)

    if bbox_h == 0 or mask.size == 0:
        # 回退到简单方法
        return estimate_font_size(bbox)

    try:
        # 提取 mask 的 ROI 区域
        y, x = bbox.get("y", 0), bbox.get("x", 0)
        h, w = bbox.get("h", 0), bbox.get("w", 0)

        # 边界检查
        img_h, img_w = mask.shape[:2]
        y = max(0, min(y, img_h - 1))
        x = max(0, min(x, img_w - 1))
        h = min(h, img_h - y)
        w = min(w, img_w - x)

        if h <= 0 or w <= 0:
            return estimate_font_size(bbox)

        roi_mask = mask[y:y+h, x:x+w]

        # 计算垂直投影（每一行的像素数）
        y_projection = np.sum(roi_mask > 0, axis=1).astype(np.float32)

        if len(y_projection) == 0 or np.max(y_projection) == 0:
            return estimate_font_size(bbox)

        # 归一化
        y_projection = y_projection / np.max(y_projection)

        # 找出主体区域（阈值：30% 以上的像素密度）
        # 这可以过滤掉稀疏的 ascender（如 l, t）和 descender（如 g, y）
        threshold = 0.3
        main_rows = np.where(y_projection > threshold)[0]

        if len(main_rows) == 0:
            return estimate_font_size(bbox)

        # 计算主体高度
        main_height = len(main_rows)

        # cap-height 通常是 font-size 的 0.65-0.70
        # 对于中文，这个比例更接近 0.75-0.80（因为中文是方块字）
        has_chinese = any('\u4e00' <= c <= '\u9fff' for c in text)

        if has_chinese:
            cap_ratio = 0.75  # 中文填充率高
        else:
            cap_ratio = 0.68  # 英文

        font_size = int(main_height / cap_ratio)

        # 限制范围
        font_size = max(12, min(font_size, 500))

        return font_size

    except Exception as e:
        # 如果像素分析失败，回退到简单方法
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Pixel-based font size estimation failed: {e}, falling back to simple method")
        return estimate_font_size(bbox)


def estimate_font_weight(
    image: np.ndarray,
    mask: np.ndarray
) -> int:
    """
    估计字重 (粗细)

    Args:
        image: 原图 (H, W, 3) BGR
        mask: 文字 mask (H, W), 255 表示文字区域

    Returns:
        font_weight (400=normal, 600=semibold, 700=bold)

    算法:
    通过 mask 的填充率粗略估计字重
    填充率高 -> 笔画粗 -> 字重大
    """
    # 计算 mask 的边界框
    coords = cv2.findNonZero(mask)
    if coords is None:
        return 400  # 默认 normal

    x, y, w, h = cv2.boundingRect(coords)

    # 计算填充率
    mask_area = np.sum(mask > 0)
    bbox_area = w * h

    if bbox_area == 0:
        return 400

    fill_ratio = mask_area / bbox_area

    # 根据填充率估计字重
    # 这是一个粗略的启发式规则
    if fill_ratio > 0.5:
        return 700  # bold
    elif fill_ratio > 0.35:
        return 600  # semibold
    else:
        return 400  # normal


def estimate_text_style(
    image: np.ndarray,
    candidate: Dict,
    color_method: str = "kmeans",
    font_size_method: str = "auto",
    debug: bool = False
) -> Dict:
    """
    从原图和 candidate 估计完整的文本样式

    Args:
        image: 原图 (H, W, 3) BGR
        candidate: 候选框数据 {"quad": ..., "bbox": ..., "text": ..., "confidence": ...}
        color_method: 颜色估计方法 ("kmeans", "median", "edge", "mean")
        font_size_method: 字号估计方法
            - "auto": 组合方法（先像素分析，失败则自适应）
            - "pixel": 仅像素分析
            - "adaptive": 仅自适应缩放
            - "simple": 简单固定缩放（向后兼容）
        debug: 是否返回调试信息

    Returns:
        样式字典
        {
            "fontFamily": "System",
            "fontSize": 32,
            "fontWeight": 600,
            "fill": "rgba(30,30,30,1)",
            "letterSpacing": 0,
            "lineHeight": 1.2,
            "debug": {  # 仅当 debug=True 时返回
                "color_rgb": [r, g, b],
                "color_method": "kmeans",
                "font_size_method": "pixel",
                "sample_count": 1234
            }
        }
    """
    from ..patch.mask import rasterize_quad
    import logging
    logger = logging.getLogger(__name__)

    # 生成 mask
    quad = candidate["quad"]
    bbox = candidate["bbox"]
    text = candidate.get("text", "")
    confidence = candidate.get("confidence", 1.0)
    h, w = image.shape[:2]
    mask = rasterize_quad(quad, (h, w))

    # 估计颜色
    r, g, b, a = estimate_text_color(image, mask, method=color_method)
    fill = f"rgba({r},{g},{b},{a / 255.0:.2f})"

    # 估计字号（使用改进的组合方法）
    actual_method = font_size_method

    if font_size_method == "auto":
        # 组合方法：先尝试像素分析，失败则用自适应
        try:
            font_size = estimate_font_size_from_pixels(image, mask, bbox, text)
            actual_method = "pixel"
            logger.debug(f"Font size estimated using pixel analysis: {font_size}px")
        except Exception as e:
            logger.debug(f"Pixel analysis failed, falling back to adaptive: {e}")
            font_size = estimate_font_size_adaptive(bbox, text, confidence)
            actual_method = "adaptive"
    elif font_size_method == "pixel":
        font_size = estimate_font_size_from_pixels(image, mask, bbox, text)
    elif font_size_method == "adaptive":
        font_size = estimate_font_size_adaptive(bbox, text, confidence)
    else:  # simple or unknown
        font_size = estimate_font_size(bbox)
        actual_method = "simple"

    # 估计字重
    font_weight = estimate_font_weight(image, mask)

    style = {
        "fontFamily": "System",  # MVP 不做字体匹配
        "fontSize": font_size,
        "fontWeight": font_weight,
        "fill": fill,
        "letterSpacing": 0,
        "lineHeight": 1.2
    }

    # 添加调试信息
    if debug:
        sample_count = np.sum(mask > 0)
        style["debug"] = {
            "color_rgb": [int(r), int(g), int(b)],
            "color_method": color_method,
            "font_size_method": actual_method,
            "sample_count": int(sample_count),
            "text_preview": text[:20] + "..." if len(text) > 20 else text
        }

    return style
