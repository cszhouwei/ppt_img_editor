"""Patch generation pipeline"""
import logging
from typing import Dict, List, Optional
import numpy as np
import cv2
from PIL import Image
import io

from .geometry import quad_to_bbox, expand_bbox, clip_bbox_to_image
from .mask import rasterize_quad, create_edge_mask, feather_mask
from .bg_fit import is_solid_color, fit_linear_gradient, generate_solid_fill, generate_gradient_fill
from .inpaint import inpaint_auto
from .compose import create_transparent_patch

logger = logging.getLogger(__name__)


class PatchGenerationResult:
    """Patch 生成结果"""

    def __init__(
        self,
        success: bool,
        patch_bytes: Optional[bytes] = None,
        bbox: Optional[Dict[str, int]] = None,
        debug_info: Optional[Dict] = None,
        error: Optional[str] = None
    ):
        self.success = success
        self.patch_bytes = patch_bytes
        self.bbox = bbox
        self.debug_info = debug_info or {}
        self.error = error


def generate_patch(
    image_bytes: bytes,
    candidate: Dict,
    padding_px: int = 8,
    mode: str = "auto",
    algo_version: str = "v1"
) -> PatchGenerationResult:
    """
    生成 patch 的端到端 pipeline

    Args:
        image_bytes: 原始图片字节流
        candidate: 候选框数据 {"quad": [[x,y],...], "bbox": {...}}
        padding_px: 扩展像素数
        mode: 模式 "auto"|"solid"|"gradient"|"inpaint"
        algo_version: 算法版本

    Returns:
        PatchGenerationResult

    Pipeline 步骤:
    1. 加载图像
    2. 生成 mask
    3. 分析背景类型(纯色/渐变/复杂)
    4. 生成背景填充
    5. (可选) 边缘 inpaint
    6. 合成透明 patch PNG
    """
    debug_info = {
        "mode": mode,
        "algo_version": algo_version,
        "padding_px": padding_px
    }

    try:
        # Step 1: 加载图像
        image = Image.open(io.BytesIO(image_bytes))
        image_np = np.array(image.convert('RGB'))
        image_bgr = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
        h, w = image_bgr.shape[:2]

        logger.info(f"Loaded image: {w}x{h}")

        # Step 2: 生成 mask
        quad = candidate["quad"]
        bbox_orig = candidate.get("bbox") or quad_to_bbox(quad)

        # 扩展 bbox
        bbox_padded = expand_bbox(bbox_orig, padding_px)
        bbox_final = clip_bbox_to_image(bbox_padded, w, h)

        logger.info(f"Bbox: orig={bbox_orig}, padded={bbox_padded}, final={bbox_final}")

        # 光栅化 quad 为 mask
        mask = rasterize_quad(quad, (h, w))

        debug_info["bbox_orig"] = bbox_orig
        debug_info["bbox_final"] = bbox_final

        # Step 3: 提取文字周围的背景区域用于分析
        x, y, bw, bh = bbox_final["x"], bbox_final["y"], bbox_final["w"], bbox_final["h"]

        # 提取 ROI
        roi = image_bgr[y:y+bh, x:x+bw].copy()
        roi_mask = mask[y:y+bh, x:x+bw]

        # 提取背景像素 (mask=0 的区域)
        bg_pixels = roi[roi_mask == 0]

        # Step 4: 分析背景类型并生成填充
        bg_model = "fallback"
        filled_roi = roi.copy()

        if mode in ["auto", "solid"]:
            # 尝试纯色拟合
            is_solid, mean_color = is_solid_color(bg_pixels.reshape(-1, bg_pixels.shape[-1], 3))
            if is_solid:
                bg_model = "solid"
                fill = generate_solid_fill((bh, bw), mean_color)
                # 用纯色填充文字区域
                filled_roi[roi_mask > 0] = fill[roi_mask > 0]
                debug_info["solid_color"] = mean_color
                logger.info(f"Background model: solid, color={mean_color}")

        if bg_model == "fallback" and mode in ["auto", "gradient"]:
            # 尝试渐变拟合
            bg_region = roi[roi_mask == 0].reshape(-1, 1, 3) if bg_pixels.size > 0 else np.array([])
            if bg_region.size > 100:  # 需要足够的背景像素
                # 重新提取完整 ROI 进行渐变分析
                is_grad, grad_params = fit_linear_gradient(roi)
                if is_grad:
                    bg_model = "gradient"
                    fill = generate_gradient_fill((bh, bw), grad_params)
                    filled_roi[roi_mask > 0] = fill[roi_mask > 0]
                    debug_info["gradient_params"] = grad_params
                    logger.info(f"Background model: gradient, MAE={grad_params.get('mae', 0):.2f}")

        # Step 5: 如果无法拟合,使用 inpaint
        if bg_model == "fallback" or mode == "inpaint":
            bg_model = "inpaint"
            edge_mask = create_edge_mask(roi_mask, edge_width=6)
            filled_roi = inpaint_auto(roi, roi_mask, method="telea", radius=7)
            debug_info["inpaint_method"] = "telea"
            logger.info("Background model: inpaint (fallback)")

        debug_info["bg_model"] = bg_model

        # Step 6: 合成透明 patch PNG
        # 将填充后的 ROI 放回完整图像
        result_image = image_bgr.copy()
        result_image[y:y+bh, x:x+bw] = filled_roi

        # 创建透明 patch
        patch_bytes = create_transparent_patch(
            result_image,
            mask,
            bbox_final,
            feather=True
        )

        logger.info(f"Patch generated successfully: {len(patch_bytes)} bytes")

        return PatchGenerationResult(
            success=True,
            patch_bytes=patch_bytes,
            bbox=bbox_final,
            debug_info=debug_info
        )

    except Exception as e:
        logger.error(f"Patch generation failed: {e}", exc_info=True)
        return PatchGenerationResult(
            success=False,
            error=str(e),
            debug_info=debug_info
        )
