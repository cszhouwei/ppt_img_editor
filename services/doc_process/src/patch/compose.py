"""Patch composition utilities"""
import numpy as np
import cv2
from typing import Dict
from io import BytesIO
from PIL import Image


def create_transparent_patch(
    background: np.ndarray,
    mask: np.ndarray,
    bbox: Dict[str, int],
    feather: bool = True
) -> bytes:
    """
    创建透明 patch PNG

    Args:
        background: 修复后的背景图像 (H, W, 3) BGR
        mask: 原始文字 mask (H, W), 255 表示文字区域
        bbox: 裁剪区域 {"x", "y", "w", "h"}
        feather: 是否羽化边缘

    Returns:
        PNG 图像字节流
    """
    h, w = background.shape[:2]

    # 裁剪到 bbox
    x, y, bw, bh = bbox["x"], bbox["y"], bbox["w"], bbox["h"]

    # 确保裁剪区域在图像范围内
    x = max(0, x)
    y = max(0, y)
    x2 = min(w, x + bw)
    y2 = min(h, y + bh)

    # 裁剪背景和 mask
    bg_crop = background[y:y2, x:x2]
    mask_crop = mask[y:y2, x:x2]

    # 创建 alpha 通道 (文字区域 alpha=255, 背景区域 alpha=0)
    alpha = mask_crop.copy()

    # 可选: 羽化边缘使过渡更自然
    if feather:
        alpha = cv2.GaussianBlur(alpha, (0, 0), 1.5)

    # 转换为 RGBA (OpenCV BGR -> RGB)
    rgb = cv2.cvtColor(bg_crop, cv2.COLOR_BGR2RGB)
    rgba = np.dstack([rgb, alpha])

    # 转换为 PIL Image 并保存为 PNG
    pil_image = Image.fromarray(rgba, mode='RGBA')

    buffer = BytesIO()
    pil_image.save(buffer, format='PNG', optimize=True)
    return buffer.getvalue()


def blend_patch_with_alpha(
    base_image: np.ndarray,
    patch: np.ndarray,
    patch_alpha: np.ndarray,
    offset: tuple
) -> np.ndarray:
    """
    使用 alpha 混合将 patch 叠加到基础图像上

    Args:
        base_image: 基础图像 (H, W, 3) BGR
        patch: Patch 图像 (h, w, 3) BGR
        patch_alpha: Patch alpha 通道 (h, w), 0-255
        offset: (x, y) patch 在基础图像中的位置

    Returns:
        混合后的图像 (H, W, 3)
    """
    result = base_image.copy()
    x, y = offset
    ph, pw = patch.shape[:2]

    # 确保在范围内
    h, w = base_image.shape[:2]
    if x < 0 or y < 0 or x + pw > w or y + ph > h:
        return result

    # Alpha 混合
    alpha = patch_alpha.astype(np.float32) / 255.0
    alpha_3ch = np.stack([alpha, alpha, alpha], axis=2)

    # 计算混合
    roi = result[y:y+ph, x:x+pw]
    blended = (patch * alpha_3ch + roi * (1 - alpha_3ch)).astype(np.uint8)

    result[y:y+ph, x:x+pw] = blended

    return result
