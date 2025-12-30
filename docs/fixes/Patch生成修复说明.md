# Patch 生成修复说明

## 问题描述

在点击 OCR 识别的候选框生成 patch 时,后端报错:

```
ValueError: cannot reshape array of size 15213 into shape (3,3)
File "/app/src/patch/pipeline.py", line 111, in generate_patch
  is_solid, mean_color = is_solid_color(bg_pixels.reshape(-1, bg_pixels.shape[-1], 3))
```

## 错误上下文

- 图片尺寸: 3218x1376
- 候选框 bbox: `{'x': 2348, 'y': 433, 'w': 209, 'h': 66}`
- 扩展后 bbox: `{'x': 2340, 'y': 425, 'w': 225, 'h': 82}`
- 背景像素总数: 15213

## 根本原因

### 代码逻辑分析

在 [pipeline.py:103](../services/doc_process/src/patch/pipeline.py#L103),我们提取背景像素:

```python
bg_pixels = roi[roi_mask == 0]  # 提取 mask=0 的背景区域
```

这会得到一个 **1D 数组**,shape 为 `(N, 3)`,其中 N 是背景像素的数量(本例中 N = 15213 / 3 = 5071)。

在原来的 line 111:

```python
is_solid, mean_color = is_solid_color(bg_pixels.reshape(-1, bg_pixels.shape[-1], 3))
```

这个 reshape 尝试将 `(5071, 3)` reshape 成 `(-1, 3, 3)`,即 `(5071, 3, 3)`,需要 `5071 * 3 * 3 = 45639` 个元素,但实际只有 `15213` 个元素,因此报错。

### `is_solid_color()` 函数期望的输入

查看 [bg_fit.py:8-34](../services/doc_process/src/patch/bg_fit.py#L8-L34),`is_solid_color()` 函数定义:

```python
def is_solid_color(region: np.ndarray, threshold: float = 10.0) -> Tuple[bool, Optional[Tuple[int, int, int]]]:
    """
    判断区域是否为纯色

    Args:
        region: RGB 图像区域 (H, W, 3)
        threshold: 标准差阈值

    Returns:
        (is_solid, mean_color)
    """
    if region.size == 0:
        return False, None

    # 计算每个通道的标准差
    std_b, std_g, std_r = np.std(region, axis=(0, 1))  # axis=(0, 1) 表示空间维度
    ...
```

函数期望输入 shape 为 `(H, W, 3)` 的 2D 空间数组,使用 `axis=(0, 1)` 计算空间维度的标准差。

## 解决方案

将 `bg_pixels` (shape: `(N, 3)`) reshape 成 `(1, N, 3)` 格式,以匹配 `is_solid_color()` 的输入要求。

### 修复代码

**位置**: [services/doc_process/src/patch/pipeline.py:109-116](../services/doc_process/src/patch/pipeline.py#L109-L116)

```python
if mode in ["auto", "solid"]:
    # 尝试纯色拟合
    # bg_pixels 是 (N, 3) 数组,需要 reshape 成 (1, N, 3) 以匹配 is_solid_color 的输入格式
    if bg_pixels.size > 0:
        bg_pixels_reshaped = bg_pixels.reshape(1, -1, 3)
    else:
        bg_pixels_reshaped = np.zeros((1, 1, 3), dtype=np.uint8)
    is_solid, mean_color = is_solid_color(bg_pixels_reshaped)
```

### 为什么这样修复

1. **原始 bg_pixels**: shape `(N, 3)`,即 N 个 RGB 像素的列表
2. **reshape 成 (1, N, 3)**: 将这些像素排列成 1 行 N 列的"图像"
3. **is_solid_color 计算**: `np.std(region, axis=(0, 1))` 会在 axis=0 (1 行) 和 axis=1 (N 列) 上计算标准差,正确获取 RGB 三个通道的标准差

### 空值处理

如果 `bg_pixels.size == 0`(没有背景像素),创建一个 `(1, 1, 3)` 的零数组,避免 reshape 失败。

## 验证修复

### 1. 重启服务

```bash
docker-compose restart doc_process
```

### 2. 测试 Patch 生成

1. 前端上传 PPT 截图
2. 点击 OCR 识别的候选框
3. 查看日志:

```bash
docker-compose logs doc_process | tail -20
```

**预期日志**:
```
src.patch.pipeline - INFO - Background model: solid, color=(255, 255, 255)
src.patch.pipeline - INFO - Patch generated successfully: 12345 bytes
src.api.pages - INFO - Patch generated successfully for candidate xxx
```

**不应该出现**:
```
ValueError: cannot reshape array of size 15213 into shape (3,3)
```

### 3. 前端功能测试

1. 上传 PPT 截图
2. 点击识别的文字框
3. 应该能看到:
   - 生成的透明 patch 图层
   - 可以拖拽和编辑的文本对象
   - patch 覆盖原文字区域

## 技术细节

### NumPy reshape 规则

```python
# 错误: (5071, 3) → (-1, 3, 3)
bg_pixels.reshape(-1, bg_pixels.shape[-1], 3)
# -1 会被计算为: total_size / (3 * 3) = 15213 / 9 = 1690.33 (无法整除,报错)

# 正确: (5071, 3) → (1, 5071, 3)
bg_pixels.reshape(1, -1, 3)
# -1 会被计算为: total_size / (1 * 3) = 15213 / 3 = 5071
```

### 为什么使用 (1, N, 3) 而不是其他形状

`is_solid_color()` 使用 `np.std(region, axis=(0, 1))` 计算标准差:

- `axis=0`: 沿高度方向 (H 维)
- `axis=1`: 沿宽度方向 (W 维)

对于纯色判断,我们只关心所有像素的颜色标准差,不关心空间排列。使用 `(1, N, 3)` 可以让 `axis=(0, 1)` 正确计算所有像素的标准差。

### 替代方案

也可以直接修改 `is_solid_color()` 函数,支持 `(N, 3)` 输入:

```python
def is_solid_color(region: np.ndarray, threshold: float = 10.0):
    if region.size == 0:
        return False, None

    # 支持 (N, 3) 和 (H, W, 3) 两种格式
    if region.ndim == 2:
        # (N, 3) 格式
        std_b, std_g, std_r = np.std(region, axis=0)
    else:
        # (H, W, 3) 格式
        std_b, std_g, std_r = np.std(region, axis=(0, 1))
    ...
```

但当前修复方案更简单,不需要修改共享的工具函数。

## 其他场景

### 场景 1: 渐变背景

如果背景不是纯色,pipeline 会尝试渐变拟合(line 120-131)。这部分代码也提取背景像素,但使用不同的处理方式:

```python
bg_region = roi[roi_mask == 0].reshape(-1, 1, 3)
```

这个 reshape 是正确的,因为后续的渐变拟合不使用这个 `bg_region`,而是对完整的 `roi` 进行分析。

### 场景 2: Inpaint 填充

如果纯色和渐变拟合都失败,使用 inpaint 算法(line 133-139)。Inpaint 直接处理完整的 ROI 和 mask,不受此 bug 影响。

## 相关文档

- [Docker 网络访问修复说明](Docker网络访问修复说明.md) - 修复图片下载问题
- [Google OCR 配置指南](Google-OCR-配置指南.md) - OCR 配置
- [开发流程指南](开发流程指南.md) - 日常开发流程

---

**修复日期**: 2025-12-29
**影响范围**: Patch 生成功能
**修复状态**: ✅ 已修复,待测试
