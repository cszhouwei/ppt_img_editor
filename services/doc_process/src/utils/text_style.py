"""Text style estimation utilities"""
import numpy as np
import cv2
from typing import Dict, List, Tuple, Optional


def estimate_text_color(
    image: np.ndarray,
    mask: np.ndarray,
    method: str = "median"
) -> Tuple[int, int, int, int]:
    """
    从原图中估计文字颜色

    Args:
        image: 原图 (H, W, 3) BGR
        mask: 文字 mask (H, W), 255 表示文字区域
        method: 估计方法 ("median" 或 "mean")

    Returns:
        RGBA 颜色 (r, g, b, a)

    算法:
    1. 从 mask 区域提取文字像素
    2. 排除极端值(可能是阴影或高光)
    3. 使用中位数或均值估计主色调
    """
    # 提取文字像素
    text_pixels = image[mask > 0]  # (N, 3) BGR

    if len(text_pixels) == 0:
        # 如果没有文字像素,返回黑色
        return (30, 30, 30, 255)

    # 转换为 RGB
    text_pixels_rgb = text_pixels[:, ::-1]  # BGR -> RGB

    # 计算亮度用于排除异常值
    luminance = 0.299 * text_pixels_rgb[:, 0] + 0.587 * text_pixels_rgb[:, 1] + 0.114 * text_pixels_rgb[:, 2]

    # 排除极端值 (可能是阴影/高光)
    # 保留 10th-90th 百分位的像素
    p10, p90 = np.percentile(luminance, [10, 90])
    valid_mask = (luminance >= p10) & (luminance <= p90)

    if np.sum(valid_mask) > 0:
        filtered_pixels = text_pixels_rgb[valid_mask]
    else:
        filtered_pixels = text_pixels_rgb

    # 计算颜色
    if method == "median":
        r, g, b = np.median(filtered_pixels, axis=0).astype(int)
    else:  # mean
        r, g, b = np.mean(filtered_pixels, axis=0).astype(int)

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
    从 bbox 估计字号

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
    color_method: str = "median"
) -> Dict:
    """
    从原图和 candidate 估计完整的文本样式

    Args:
        image: 原图 (H, W, 3) BGR
        candidate: 候选框数据 {"quad": ..., "bbox": ...}
        color_method: 颜色估计方法

    Returns:
        样式字典
        {
            "fontFamily": "System",
            "fontSize": 32,
            "fontWeight": 600,
            "fill": "rgba(30,30,30,1)",
            "letterSpacing": 0,
            "lineHeight": 1.2
        }
    """
    from ..patch.mask import rasterize_quad

    # 生成 mask
    quad = candidate["quad"]
    bbox = candidate["bbox"]
    h, w = image.shape[:2]
    mask = rasterize_quad(quad, (h, w))

    # 估计颜色
    r, g, b, a = estimate_text_color(image, mask, method=color_method)
    fill = f"rgba({r},{g},{b},{a / 255.0:.2f})"

    # 估计字号
    font_size = estimate_font_size(bbox)

    # 估计字重
    font_weight = estimate_font_weight(image, mask)

    return {
        "fontFamily": "System",  # MVP 不做字体匹配
        "fontSize": font_size,
        "fontWeight": font_weight,
        "fill": fill,
        "letterSpacing": 0,
        "lineHeight": 1.2
    }
