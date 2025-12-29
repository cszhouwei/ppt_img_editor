"""Geometry utilities for patch generation"""
from typing import List, Tuple, Dict
import numpy as np
import math


def quad_to_bbox(quad: List[List[int]]) -> Dict[str, int]:
    """
    将四边形转换为边界框

    Args:
        quad: [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]

    Returns:
        {"x": min_x, "y": min_y, "w": width, "h": height}
    """
    xs = [p[0] for p in quad]
    ys = [p[1] for p in quad]

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    return {
        "x": min_x,
        "y": min_y,
        "w": max_x - min_x,
        "h": max_y - min_y
    }


def expand_bbox(bbox: Dict[str, int], padding: int) -> Dict[str, int]:
    """
    扩展边界框

    Args:
        bbox: {"x", "y", "w", "h"}
        padding: 扩展像素数

    Returns:
        扩展后的 bbox
    """
    return {
        "x": bbox["x"] - padding,
        "y": bbox["y"] - padding,
        "w": bbox["w"] + 2 * padding,
        "h": bbox["h"] + 2 * padding
    }


def calculate_angle(quad: List[List[int]]) -> float:
    """
    计算四边形的旋转角度

    Args:
        quad: [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]

    Returns:
        角度(度数),-90 到 90
    """
    # 使用顶边计算角度
    p1, p2 = quad[0], quad[1]
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]

    angle_rad = math.atan2(dy, dx)
    angle_deg = math.degrees(angle_rad)

    # 归一化到 [-90, 90]
    while angle_deg > 90:
        angle_deg -= 180
    while angle_deg < -90:
        angle_deg += 180

    return angle_deg


def clip_bbox_to_image(bbox: Dict[str, int], image_width: int, image_height: int) -> Dict[str, int]:
    """
    将 bbox 裁剪到图片范围内

    Args:
        bbox: {"x", "y", "w", "h"}
        image_width: 图片宽度
        image_height: 图片高度

    Returns:
        裁剪后的 bbox
    """
    x = max(0, bbox["x"])
    y = max(0, bbox["y"])

    x2 = min(image_width, bbox["x"] + bbox["w"])
    y2 = min(image_height, bbox["y"] + bbox["h"])

    return {
        "x": x,
        "y": y,
        "w": x2 - x,
        "h": y2 - y
    }


def quad_to_contour(quad: List[List[int]]) -> np.ndarray:
    """
    将 quad 转换为 OpenCV contour 格式

    Args:
        quad: [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]

    Returns:
        numpy array shape (4, 1, 2)
    """
    return np.array(quad, dtype=np.int32).reshape((-1, 1, 2))
