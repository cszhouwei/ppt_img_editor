# Docker 网络访问修复说明

## 问题描述

在 Docker 容器内运行的后端服务无法访问 `localhost:9000` 的 MinIO 服务,导致以下功能失败:

1. **OCR 分析**: Google/Azure OCR provider 下载图片失败
2. **Patch 生成**: 点击候选框时无法下载原图生成 patch
3. **样式估计**: 点击候选框时无法下载原图估计文本样式

## 错误日志

```
httpcore.ConnectError: All connection attempts failed
```

## 根本原因

- 数据库中存储的 `page.image_url` 使用外部 URL: `http://localhost:9000/...`
- 在 Docker 容器内,`localhost` 指向容器自身,而不是宿主机
- MinIO 服务在 Docker 网络中的地址是 `http://minio:9000`
- 容器无法通过 `localhost:9000` 访问 MinIO

## 解决方案

在所有需要下载图片的地方,将 URL 从 `localhost` 替换为 `minio`:

```python
# 修复前
image_response = await client.get(page.image_url, timeout=30.0)

# 修复后
internal_url = page.image_url.replace("http://localhost:9000", "http://minio:9000")
image_response = await client.get(internal_url, timeout=30.0)
```

## 修复的文件

### 1. services/doc_process/src/ocr/google_provider.py

**位置**: `_download_image()` 方法

```python
async def _download_image(self, url: str) -> bytes:
    """下载图像"""
    # 如果 URL 使用 localhost,替换为 minio(Docker 内部网络)
    internal_url = url.replace("http://localhost:9000", "http://minio:9000")

    async with httpx.AsyncClient() as client:
        response = await client.get(internal_url, timeout=30.0)
        if response.status_code != 200:
            raise ValueError(f"Failed to download image: {url}")
        return response.content
```

### 2. services/doc_process/src/ocr/azure_provider.py

**位置**: `_download_image()` 方法

```python
async def _download_image(self, image_url: str) -> bytes:
    """下载图片"""
    # 如果 URL 使用 localhost,替换为 minio(Docker 内部网络)
    internal_url = image_url.replace("http://localhost:9000", "http://minio:9000")

    async with httpx.AsyncClient() as client:
        response = await client.get(internal_url, timeout=30.0)
        if response.status_code != 200:
            raise ValueError(f"Failed to download image: {image_url}")
        return response.content
```

### 3. services/doc_process/src/api/pages.py

**位置 1**: `generate_patch_for_candidate()` 函数 (line ~325)

```python
# 下载原图 (将 localhost 替换为 minio 用于 Docker 内部网络)
internal_url = page.image_url.replace("http://localhost:9000", "http://minio:9000")
async with httpx.AsyncClient() as client:
    image_response = await client.get(internal_url, timeout=30.0)
```

**位置 2**: `estimate_style_for_candidate()` 函数 (line ~447)

```python
# 下载原图 (将 localhost 替换为 minio 用于 Docker 内部网络)
internal_url = page.image_url.replace("http://localhost:9000", "http://minio:9000")
async with httpx.AsyncClient() as client:
    image_response = await client.get(internal_url, timeout=30.0)
```

## 验证修复

### 1. OCR 分析测试

```bash
./test-google-ocr.sh
```

**预期结果**: 识别到 3 个候选框,无错误

### 2. Patch 生成测试

1. 前端上传图片
2. 点击 OCR 识别的候选框
3. 查看日志:

```bash
docker-compose logs doc_process | tail -20
```

**预期日志**:
```
src.api.pages - INFO - Generating patch for page=xxx, candidate=xxx
src.api.pages - INFO - Estimating style for page=xxx, candidate=xxx
```

**不应该出现**:
```
httpcore.ConnectError: All connection attempts failed
```

### 3. 前端功能测试

1. 上传 PPT 截图
2. 点击识别的文字框
3. 应该能看到:
   - 生成的透明 patch 图层
   - 估计的文本样式(颜色、字号等)
   - 可编辑的文本对象

## 为什么这样修复

### 不修改数据库的原因

我们选择在代码中替换 URL,而不是在数据库中存储内部 URL,原因:

1. **前端需要外部 URL**: 前端浏览器需要通过 `localhost:9000` 访问图片
2. **后端需要内部 URL**: Docker 容器需要通过 `minio:9000` 访问
3. **灵活性**: 代码转换更灵活,适应不同部署环境

### URL 转换逻辑

```python
internal_url = url.replace("http://localhost:9000", "http://minio:9000")
```

- **开发环境**: localhost → minio (Docker 网络)
- **生产环境**: 可能不需要替换(使用外部域名)
- **简单有效**: 一行代码解决问题

## 其他网络场景

### 场景 1: 使用外部 MinIO

如果 MinIO 部署在外部服务器:

```python
# 不需要替换
image_response = await client.get(page.image_url, timeout=30.0)
```

因为外部 URL 在容器内也可以直接访问。

### 场景 2: 使用域名

如果配置了域名:

```bash
S3_PUBLIC_ENDPOINT=https://minio.example.com
```

也不需要替换,域名在容器内外都可以访问。

### 场景 3: 多环境部署

可以通过环境变量控制是否需要替换:

```python
# config.py
s3_internal_endpoint: str = "http://minio:9000"  # Docker 内部地址

# pages.py
internal_url = url.replace(settings.s3_public_endpoint, settings.s3_internal_endpoint)
```

## 最佳实践

### 1. 开发环境

- 使用 `docker-compose` 部署所有服务
- 使用 Docker 网络内部通信
- 代码中进行 URL 转换

### 2. 生产环境

- MinIO 使用独立服务器或云存储
- 使用公网域名或内网 IP
- 可能不需要 URL 转换

### 3. 健壮性

在代码中添加防御性检查:

```python
def get_internal_url(public_url: str) -> str:
    """将公网 URL 转换为 Docker 内部 URL"""
    if "localhost:9000" in public_url:
        return public_url.replace("http://localhost:9000", "http://minio:9000")
    return public_url
```

## 故障排查

### 问题: 修复后还是连接失败

**检查步骤**:

1. 确认 MinIO 容器正在运行:
   ```bash
   docker-compose ps minio
   ```

2. 确认容器在同一网络:
   ```bash
   docker network inspect ppt_img_editor_ppt-editor-network
   ```

3. 测试容器间连通性:
   ```bash
   docker-compose exec doc_process curl http://minio:9000/minio/health/live
   ```

4. 检查代码是否真的更新:
   ```bash
   docker-compose exec doc_process grep -n "internal_url" /app/src/api/pages.py
   ```

### 问题: 前端显示图片失败

**原因**: 前端使用的是 `localhost` URL,浏览器可以访问

**确认**: 在浏览器中打开图片 URL,应该能看到图片

### 问题: 部署到生产环境后失败

**原因**: 生产环境可能使用不同的 MinIO 地址

**解决**: 通过环境变量配置内部地址

## 相关文档

- [开发流程指南](开发流程指南.md) - 日常开发流程
- [Google OCR 配置指南](Google-OCR-配置指南.md) - OCR 配置
- [docker-compose.yml](../docker-compose.yml) - Docker 网络配置

---

**修复日期**: 2025-12-29
**影响范围**: OCR 分析、Patch 生成、样式估计
**修复状态**: ✅ 已验证
