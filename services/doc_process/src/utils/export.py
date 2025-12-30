"""Export utilities for rendering project to image"""
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from typing import Dict, List, Any, Tuple
import logging
import httpx

logger = logging.getLogger(__name__)


async def download_image(url: str) -> np.ndarray:
    """
    下载图像并转换为 numpy 数组

    Args:
        url: 图像 URL

    Returns:
        图像数组 (H, W, 3) BGR
    """
    # 在 Docker 容器内，需要将 localhost 替换为服务名
    internal_url = url.replace("http://localhost:9000", "http://minio:9000")

    async with httpx.AsyncClient() as client:
        response = await client.get(internal_url, timeout=30.0)
        if response.status_code != 200:
            raise ValueError(f"Failed to download image: {url}")

        image_bytes = response.content
        image_array = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

        if image is None:
            raise ValueError(f"Failed to decode image: {url}")

        return image


async def blend_patch_layer(
    base_image: np.ndarray,
    patch_layer: Dict[str, Any]
) -> np.ndarray:
    """
    将 patch 层叠加到基础图像

    Args:
        base_image: 基础图像 (H, W, 3) BGR
        patch_layer: patch 层数据 {"bbox": {...}, "image_url": "..."}

    Returns:
        叠加后的图像
    """
    # 下载 patch 图像
    patch_url = patch_layer["image_url"]
    patch_image = await download_image(patch_url)

    # 获取 bbox
    bbox = patch_layer["bbox"]
    x, y, w, h = bbox["x"], bbox["y"], bbox["w"], bbox["h"]

    # 确保 patch 图像有 alpha 通道
    if patch_image.shape[2] == 3:
        # 如果没有 alpha 通道,添加一个全不透明的 alpha
        alpha = np.ones((patch_image.shape[0], patch_image.shape[1], 1), dtype=np.uint8) * 255
        patch_rgba = np.concatenate([patch_image, alpha], axis=2)
    else:
        patch_rgba = patch_image

    # 提取 alpha 通道
    patch_rgb = patch_rgba[:, :, :3]
    patch_alpha = patch_rgba[:, :, 3:4] / 255.0

    # 调整大小以匹配 bbox
    if patch_rgb.shape[0] != h or patch_rgb.shape[1] != w:
        patch_rgb = cv2.resize(patch_rgb, (w, h), interpolation=cv2.INTER_LINEAR)
        patch_alpha = cv2.resize(patch_alpha, (w, h), interpolation=cv2.INTER_LINEAR)
        patch_alpha = patch_alpha[:, :, np.newaxis]

    # 确保坐标在范围内
    base_h, base_w = base_image.shape[:2]
    x = max(0, min(x, base_w - 1))
    y = max(0, min(y, base_h - 1))

    # 计算实际可用的区域
    available_w = min(w, base_w - x)
    available_h = min(h, base_h - y)

    if available_w <= 0 or available_h <= 0:
        logger.warning(f"Patch bbox out of bounds: {bbox}")
        return base_image

    # 裁剪 patch 以匹配可用区域
    patch_rgb = patch_rgb[:available_h, :available_w]
    patch_alpha = patch_alpha[:available_h, :available_w]

    # Alpha 混合
    roi = base_image[y:y+available_h, x:x+available_w]
    blended = (patch_rgb * patch_alpha + roi * (1 - patch_alpha)).astype(np.uint8)

    # 写回
    result = base_image.copy()
    result[y:y+available_h, x:x+available_w] = blended

    return result


def render_text_layer(
    base_image: np.ndarray,
    text_layer: Dict[str, Any]
) -> np.ndarray:
    """
    将文本层渲染到图像上

    Args:
        base_image: 基础图像 (H, W, 3) BGR
        text_layer: 文本层数据 {"text": "...", "quad": [...], "style": {...}}

    Returns:
        渲染后的图像
    """
    # 转换为 PIL Image 以便使用文本渲染
    image_rgb = cv2.cvtColor(base_image, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(image_rgb)
    draw = ImageDraw.Draw(pil_image)

    # 获取文本和样式
    text = text_layer.get("text", "")
    style = text_layer.get("style", {})
    quad = text_layer.get("quad", [])

    if not text or not quad:
        return base_image

    # 解析样式
    font_size = style.get("fontSize", 32)
    font_weight = style.get("fontWeight", 400)
    fill_str = style.get("fill", "rgba(30,30,30,1)")

    # 解析颜色 (rgba(r,g,b,a))
    fill_color = parse_rgba_color(fill_str)

    # 加载字体 (使用系统默认字体)
    try:
        # 尝试加载更好的字体
        if font_weight >= 700:
            # Bold
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        else:
            # Normal
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
    except:
        # 回退到默认字体
        font = ImageFont.load_default()
        logger.warning("Failed to load TrueType font, using default")

    # 计算文本位置 (使用 quad 的左上角)
    x, y = quad[0][0], quad[0][1]

    # 绘制文本
    draw.text((x, y), text, font=font, fill=fill_color)

    # 转换回 OpenCV 格式
    result_rgb = np.array(pil_image)
    result_bgr = cv2.cvtColor(result_rgb, cv2.COLOR_RGB2BGR)

    return result_bgr


def parse_rgba_color(color_str: str) -> Tuple[int, int, int, int]:
    """
    解析 RGBA 颜色字符串

    Args:
        color_str: 颜色字符串,格式如 "rgba(30,30,30,1)" 或 "rgba(30,30,30,1.00)"

    Returns:
        (r, g, b, a) 元组,a 范围 0-255
    """
    try:
        # 移除 "rgba(" 和 ")"
        color_str = color_str.replace("rgba(", "").replace(")", "").replace(" ", "")
        parts = color_str.split(",")

        r = int(parts[0])
        g = int(parts[1])
        b = int(parts[2])
        a = float(parts[3])

        # 将 alpha 从 0-1 转换为 0-255
        a = int(a * 255)

        return (r, g, b, a)
    except Exception as e:
        logger.warning(f"Failed to parse color '{color_str}': {e}, using default")
        return (30, 30, 30, 255)


async def export_project_to_png(
    page_data: Dict[str, Any],
    layers: List[Dict[str, Any]]
) -> bytes:
    """
    将项目导出为 PNG 图像

    Args:
        page_data: 页面数据 {"image_url": "...", "width": ..., "height": ...}
        layers: 图层列表,按顺序渲染

    Returns:
        PNG 图像字节流

    渲染顺序:
    1. 背景图 (原图)
    2. patch layers
    3. text layers
    """
    # 下载背景图
    logger.info(f"Downloading base image: {page_data['image_url']}")
    base_image = await download_image(page_data["image_url"])

    logger.info(f"Base image loaded: {base_image.shape}")

    # 按顺序渲染 layers
    result_image = base_image.copy()

    for i, layer in enumerate(layers):
        kind = layer.get("kind")
        layer_id = layer.get("id", f"layer_{i}")

        logger.info(f"Rendering layer {i+1}/{len(layers)}: {kind} ({layer_id})")

        if kind == "patch":
            # 渲染 patch 层
            result_image = await blend_patch_layer(result_image, layer)
        elif kind == "text":
            # 渲染文本层
            result_image = render_text_layer(result_image, layer)
        else:
            logger.warning(f"Unknown layer kind: {kind}")

    # 转换为 PNG
    success, encoded_image = cv2.imencode('.png', result_image)

    if not success:
        raise ValueError("Failed to encode image as PNG")

    return encoded_image.tobytes()
