"""Background fitting utilities"""
from typing import Tuple, Dict, Optional
import numpy as np
import cv2
from scipy import stats


def is_solid_color(region: np.ndarray, threshold: float = 10.0) -> Tuple[bool, Optional[Tuple[int, int, int]]]:
    """
    判断区域是否为纯色

    Args:
        region: RGB 图像区域 (H, W, 3)
        threshold: 标准差阈值

    Returns:
        (is_solid, mean_color)
        is_solid: 是否为纯色
        mean_color: 平均颜色 (B, G, R) 或 None
    """
    if region.size == 0:
        return False, None

    # 计算每个通道的标准差
    std_b, std_g, std_r = np.std(region, axis=(0, 1))

    # 如果所有通道标准差都小于阈值,认为是纯色
    is_solid = (std_b < threshold and std_g < threshold and std_r < threshold)

    if is_solid:
        mean_color = tuple(np.mean(region, axis=(0, 1)).astype(int).tolist())
        return True, mean_color
    else:
        return False, None


def fit_linear_gradient(region: np.ndarray) -> Tuple[bool, Dict]:
    """
    拟合线性渐变

    Args:
        region: RGB 图像区域 (H, W, 3)

    Returns:
        (is_gradient, gradient_params)
        is_gradient: 是否可以用线性渐变拟合
        gradient_params: 渐变参数 {"direction": "horizontal|vertical", "start_color": (B,G,R), "end_color": (B,G,R), "mae": float}
    """
    if region.size == 0:
        return False, {}

    h, w, c = region.shape

    # 尝试水平渐变
    h_mae = _fit_horizontal_gradient(region)

    # 尝试垂直渐变
    v_mae = _fit_vertical_gradient(region)

    # 选择误差较小的方向
    if h_mae < v_mae and h_mae < 15.0:  # MAE < 15 认为是可接受的渐变
        direction = "horizontal"
        mae = h_mae
        start_color = tuple(np.mean(region[:, :5, :], axis=(0, 1)).astype(int).tolist())
        end_color = tuple(np.mean(region[:, -5:, :], axis=(0, 1)).astype(int).tolist())
    elif v_mae < 15.0:
        direction = "vertical"
        mae = v_mae
        start_color = tuple(np.mean(region[:5, :, :], axis=(0, 1)).astype(int).tolist())
        end_color = tuple(np.mean(region[-5:, :, :], axis=(0, 1)).astype(int).tolist())
    else:
        return False, {}

    return True, {
        "direction": direction,
        "start_color": start_color,
        "end_color": end_color,
        "mae": mae
    }


def _fit_horizontal_gradient(region: np.ndarray) -> float:
    """拟合水平渐变,返回 MAE"""
    h, w, c = region.shape

    # 平均每列的颜色
    col_means = np.mean(region, axis=0)  # (W, 3)

    # 对每个通道拟合线性模型
    x = np.arange(w)
    errors = []

    for ch in range(c):
        y = col_means[:, ch]
        slope, intercept, _, _, _ = stats.linregress(x, y)
        y_pred = slope * x + intercept
        mae = np.mean(np.abs(y - y_pred))
        errors.append(mae)

    return np.mean(errors)


def _fit_vertical_gradient(region: np.ndarray) -> float:
    """拟合垂直渐变,返回 MAE"""
    h, w, c = region.shape

    # 平均每行的颜色
    row_means = np.mean(region, axis=1)  # (H, 3)

    # 对每个通道拟合线性模型
    y = np.arange(h)
    errors = []

    for ch in range(c):
        x = row_means[:, ch]
        slope, intercept, _, _, _ = stats.linregress(y, x)
        x_pred = slope * y + intercept
        mae = np.mean(np.abs(x - x_pred))
        errors.append(mae)

    return np.mean(errors)


def generate_solid_fill(shape: Tuple[int, int], color: Tuple[int, int, int]) -> np.ndarray:
    """
    生成纯色填充

    Args:
        shape: (height, width)
        color: (B, G, R)

    Returns:
        RGB 图像 (H, W, 3)
    """
    h, w = shape
    fill = np.zeros((h, w, 3), dtype=np.uint8)
    fill[:, :] = color
    return fill


def generate_gradient_fill(shape: Tuple[int, int], params: Dict) -> np.ndarray:
    """
    生成渐变填充

    Args:
        shape: (height, width)
        params: {"direction": "horizontal|vertical", "start_color": (B,G,R), "end_color": (B,G,R)}

    Returns:
        RGB 图像 (H, W, 3)
    """
    h, w = shape
    direction = params["direction"]
    start_color = np.array(params["start_color"], dtype=np.float32)
    end_color = np.array(params["end_color"], dtype=np.float32)

    fill = np.zeros((h, w, 3), dtype=np.uint8)

    if direction == "horizontal":
        for x in range(w):
            t = x / max(w - 1, 1)
            color = start_color * (1 - t) + end_color * t
            fill[:, x, :] = color.astype(np.uint8)
    else:  # vertical
        for y in range(h):
            t = y / max(h - 1, 1)
            color = start_color * (1 - t) + end_color * t
            fill[y, :, :] = color.astype(np.uint8)

    return fill
