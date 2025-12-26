from io import BytesIO
from typing import Tuple
from PIL import Image


def get_image_dimensions(image_data: bytes) -> Tuple[int, int]:
    """
    获取图片尺寸

    Args:
        image_data: 图片二进制数据

    Returns:
        Tuple[int, int]: (width, height)

    Raises:
        ValueError: 如果图片无法解析
    """
    try:
        with Image.open(BytesIO(image_data)) as img:
            return img.size
    except Exception as e:
        raise ValueError(f"Failed to read image dimensions: {e}")


def validate_image(image_data: bytes) -> bool:
    """
    验证是否为有效图片

    Args:
        image_data: 图片二进制数据

    Returns:
        bool: 是否为有效图片
    """
    try:
        with Image.open(BytesIO(image_data)) as img:
            img.verify()
        return True
    except Exception:
        return False
