"""Inpainting utilities using OpenCV"""
import numpy as np
import cv2
from typing import Literal


def inpaint_telea(image: np.ndarray, mask: np.ndarray, radius: int = 3) -> np.ndarray:
    """
    使用 Telea 算法修复图像

    Args:
        image: RGB 图像 (H, W, 3)
        mask: Binary mask (H, W), 255 表示需要修复的区域
        radius: 修复半径

    Returns:
        修复后的图像 (H, W, 3)
    """
    result = cv2.inpaint(image, mask, radius, cv2.INPAINT_TELEA)
    return result


def inpaint_ns(image: np.ndarray, mask: np.ndarray, radius: int = 3) -> np.ndarray:
    """
    使用 Navier-Stokes 算法修复图像

    Args:
        image: RGB 图像 (H, W, 3)
        mask: Binary mask (H, W), 255 表示需要修复的区域
        radius: 修复半径

    Returns:
        修复后的图像 (H, W, 3)
    """
    result = cv2.inpaint(image, mask, radius, cv2.INPAINT_NS)
    return result


def inpaint_auto(
    image: np.ndarray,
    mask: np.ndarray,
    method: Literal["telea", "ns", "auto"] = "auto",
    radius: int = 5
) -> np.ndarray:
    """
    自动选择 inpaint 算法

    Args:
        image: RGB 图像 (H, W, 3)
        mask: Binary mask (H, W), 255 表示需要修复的区域
        method: 算法选择 ("telea", "ns", "auto")
        radius: 修复半径

    Returns:
        修复后的图像 (H, W, 3)
    """
    if method == "telea":
        return inpaint_telea(image, mask, radius)
    elif method == "ns":
        return inpaint_ns(image, mask, radius)
    else:  # auto
        # 默认使用 Telea,速度较快且效果稳定
        return inpaint_telea(image, mask, radius)
