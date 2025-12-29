"""Mask generation utilities"""
from typing import List, Tuple
import numpy as np
import cv2


def rasterize_quad(quad: List[List[int]], image_shape: Tuple[int, int]) -> np.ndarray:
    """
    将四边形光栅化为 mask

    Args:
        quad: [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
        image_shape: (height, width)

    Returns:
        Binary mask (height, width) uint8, 255 for inside quad
    """
    mask = np.zeros(image_shape, dtype=np.uint8)
    contour = np.array(quad, dtype=np.int32).reshape((-1, 1, 2))
    cv2.fillPoly(mask, [contour], 255)
    return mask


def dilate_mask(mask: np.ndarray, kernel_size: int = 5) -> np.ndarray:
    """
    膨胀 mask

    Args:
        mask: Binary mask
        kernel_size: 膨胀核大小

    Returns:
        膨胀后的 mask
    """
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    return cv2.dilate(mask, kernel, iterations=1)


def erode_mask(mask: np.ndarray, kernel_size: int = 5) -> np.ndarray:
    """
    腐蚀 mask

    Args:
        mask: Binary mask
        kernel_size: 腐蚀核大小

    Returns:
        腐蚀后的 mask
    """
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    return cv2.erode(mask, kernel, iterations=1)


def create_ring_mask(inner_mask: np.ndarray, outer_mask: np.ndarray) -> np.ndarray:
    """
    创建环形 mask (outer - inner)

    Args:
        inner_mask: 内部 mask
        outer_mask: 外部 mask

    Returns:
        环形 mask
    """
    return cv2.subtract(outer_mask, inner_mask)


def create_edge_mask(mask: np.ndarray, edge_width: int = 8) -> np.ndarray:
    """
    创建边缘 mask,用于 inpainting

    Args:
        mask: 原始 mask
        edge_width: 边缘宽度(像素)

    Returns:
        边缘 mask (仅边缘为 255)
    """
    # 膨胀得到外边界
    dilated = dilate_mask(mask, kernel_size=edge_width)

    # 腐蚀得到内边界
    eroded = erode_mask(mask, kernel_size=edge_width)

    # 边缘 = 膨胀 - 腐蚀
    edge = cv2.subtract(dilated, eroded)

    return edge


def feather_mask(mask: np.ndarray, feather_radius: int = 3) -> np.ndarray:
    """
    羽化 mask 边缘

    Args:
        mask: Binary mask
        feather_radius: 羽化半径

    Returns:
        羽化后的 mask (0-255 float)
    """
    # 高斯模糊
    blurred = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), feather_radius)

    # 归一化到 0-255
    blurred = np.clip(blurred, 0, 255)

    return blurred.astype(np.uint8)
