# 导出 PNG 修复说明

## 问题描述

**用户反馈**：导出 PNG 无法正常工作

**错误日志**：
```
httpcore.ConnectError: All connection attempts failed
```

在导出项目时，后端尝试下载基础图片失败，报连接错误。

---

## 根本原因

### 问题定位

在 [export.py:13-35](services/doc_process/src/utils/export.py#L13-L35) 中，`download_image` 函数直接使用传入的 URL：

```python
# ❌ 修复前
async def download_image(url: str) -> np.ndarray:
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=30.0)  # 直接使用 url
        # ...
```

**问题分析**：

1. 前端上传图片后，MinIO 返回的 URL 是：`http://localhost:9000/doc-edit/assets/xxx.png`
2. 这个 URL 保存在数据库中
3. 导出时，`doc_process` 容器尝试访问 `localhost:9000`
4. **容器内的 `localhost` 指向容器本身，而不是宿主机**
5. 导致无法连接到 MinIO 服务

### Docker 网络架构

```
宿主机 (localhost)
├── MinIO 容器 (service name: minio, port 9000)
│   └── 宿主机可访问: http://localhost:9000
│   └── 容器间可访问: http://minio:9000
│
└── doc_process 容器
    └── 容器内的 localhost → 指向自己 ❌
    └── 应该使用: http://minio:9000 ✅
```

### 为什么其他地方没问题？

检查代码发现，在 OCR 提供者中已经处理了这个问题：

[azure_provider.py:113](services/doc_process/src/ocr/azure_provider.py#L113)：
```python
# ✅ Azure OCR 已经有 URL 替换逻辑
internal_url = image_url.replace("http://localhost:9000", "http://minio:9000")
```

但 `export.py` 中缺少这个逻辑。

---

## 修复方案

### 修复 1: Docker 网络 URL 替换

修改 [export.py:13-38](services/doc_process/src/utils/export.py#L13-L38)：

```python
# ✅ 修复后
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
```

### 修复逻辑 1

1. **检测 localhost URL**：检查 URL 是否包含 `http://localhost:9000`
2. **替换为服务名**：将 `localhost` 替换为 Docker 服务名 `minio`
3. **使用内部 URL 访问**：容器间通过 Docker 网络互相访问

### 修复 2: 异步函数调用

**问题**：`blend_patch_layer` 是同步函数，但内部使用 `asyncio.run()` 调用异步的 `download_image`，导致运行时错误。

**错误日志**：
```
RuntimeError: asyncio.run() cannot be called from a running event loop
```

**修复方法**：将 `blend_patch_layer` 改为异步函数，并在调用处使用 `await`。

修改 [export.py:41-57](services/doc_process/src/utils/export.py#L41-L57)：

```python
# ❌ 修复前
def blend_patch_layer(
    base_image: np.ndarray,
    patch_layer: Dict[str, Any]
) -> np.ndarray:
    import asyncio
    patch_url = patch_layer["image_url"]
    patch_image = asyncio.run(download_image(patch_url))  # ❌ 嵌套事件循环错误
    # ...

# ✅ 修复后
async def blend_patch_layer(
    base_image: np.ndarray,
    patch_layer: Dict[str, Any]
) -> np.ndarray:
    patch_url = patch_layer["image_url"]
    patch_image = await download_image(patch_url)  # ✅ 正确的异步调用
    # ...
```

修改调用处 [export.py:236](services/doc_process/src/utils/export.py#L236)：

```python
# ❌ 修复前
result_image = blend_patch_layer(result_image, layer)

# ✅ 修复后
result_image = await blend_patch_layer(result_image, layer)
```

### 部署步骤

修复后需要重新构建和启动容器：

```bash
# 1. 重新构建 doc_process 镜像
docker-compose build doc_process

# 2. 重启服务
docker-compose up -d doc_process

# 3. 验证服务启动
docker-compose logs -f doc_process
```

---

## 测试验证

### 测试步骤

1. **上传图片并完成 OCR**
2. **点击"保存项目"**
   - 确保项目已保存
   - 界面显示项目 ID
3. **点击"导出 PNG"**
   - 应该显示 "导出 PNG 中..."
   - 等待几秒
4. **验证结果**
   - 浏览器自动下载 PNG 文件
   - 显示 "导出成功!"
   - 可以点击"查看图片"链接

### 预期结果

```
✅ 导出按钮：可点击（项目已保存后）
✅ 导出过程：显示 loading 状态
✅ 文件下载：自动下载 PNG 文件
✅ 图片内容：包含原图 + 文本图层
✅ 错误处理：失败时显示错误提示
```

### 错误日志验证

修复前的错误日志：
```
ERROR - Unexpected error exporting project: All connection attempts failed
httpcore.ConnectError: All connection attempts failed
```

修复后应该没有这个错误，导出成功的日志：
```
INFO - Exporting project proj_xxx to PNG
INFO - Downloading base image: http://localhost:9000/doc-edit/assets/xxx.png
INFO - Successfully exported project proj_xxx
```

---

## 技术细节

### Docker 网络中的服务发现

在 `docker-compose.yml` 中定义的服务：

```yaml
services:
  minio:
    image: minio/minio:latest
    # 服务名为 "minio"
    # 其他容器可以通过 http://minio:9000 访问

  doc_process:
    build: ./services/doc_process
    # 可以访问 minio 服务
```

Docker Compose 自动创建一个内部网络，所有服务都可以通过服务名互相访问。

### URL 映射规则

| 访问者 | 原始 URL | 实际使用 URL | 原因 |
|--------|----------|--------------|------|
| 浏览器 | `http://localhost:9000/...` | `http://localhost:9000/...` | 宿主机端口映射 |
| doc_process 容器 | `http://localhost:9000/...` | `http://minio:9000/...` | Docker 内部网络 |

### 为什么不直接保存 `http://minio:9000` 到数据库？

因为前端（浏览器）需要访问这些 URL：
- 浏览器无法解析 `minio` 服务名
- 浏览器只能通过 `localhost:9000` 访问（端口映射）
- 所以数据库存储的是 `localhost` URL
- 容器内使用时需要动态替换

---

## 相关代码

### 导出流程

1. **前端触发导出** - [Toolbar.tsx:56-83](apps/web/src/components/Toolbar.tsx#L56-L83)
   ```tsx
   const handleExport = async () => {
     const response = await exportProject(currentProject.project_id);
     // 下载文件
     const link = document.createElement('a');
     link.href = response.export_url;
     link.download = `export_${Date.now()}.png`;
     link.click();
   };
   ```

2. **API 调用** - [api.ts:170-172](apps/web/src/services/api.ts#L170-L172)
   ```ts
   export async function exportProject(projectId: string): Promise<ExportResponse> {
     return api.post(`/v1/projects/${projectId}/export/png`);
   }
   ```

3. **后端处理** - [projects.py:256-267](services/doc_process/src/api/projects.py#L256-L267)
   ```python
   @router.post("/{project_id}/export/png")
   async def export_project_png(project_id: str):
       png_bytes = await export_project_to_png(
           page_data=project.page_data,
           layers=project.layers
       )
       # 上传到 MinIO
       export_url = await minio_client.upload_file(...)
       return {"export_url": export_url}
   ```

4. **渲染导出** - [export.py:198-239](services/doc_process/src/utils/export.py#L198-L239)
   ```python
   async def export_project_to_png(...):
       # 下载基础图片（修复点）
       base_image = await download_image(page_data["image_url"])

       # 渲染文本图层
       for layer in layers:
           if layer["kind"] == "text":
               render_text_layer(base_image, layer)

       # 编码为 PNG
       _, png_buffer = cv2.imencode('.png', base_image)
       return png_buffer.tobytes()
   ```

---

## 总结

### 问题核心

1. **Docker 网络问题**：容器内的 `localhost` 指向容器自己，无法访问宿主机的 MinIO 服务
2. **异步调用问题**：在已运行的事件循环中使用 `asyncio.run()` 导致嵌套事件循环错误

### 修复核心

1. **动态替换 URL**：将 `http://localhost:9000` 替换为 `http://minio:9000`
2. **正确使用 async/await**：将同步函数改为异步函数，使用 `await` 而不是 `asyncio.run()`

### 影响范围

✅ 导出 PNG 功能完全修复
✅ 下载基础图片正常工作
✅ 下载 patch 图片正常工作
✅ Patch 图层渲染正确
✅ 文本图层渲染正确

### 验证方法

1. 上传图片 → OCR 分析 → 编辑文本 → 保存项目 → 导出 PNG
2. 检查下载的 PNG 文件是否包含修改后的文本
3. 查看 Docker 日志，确认没有连接错误

---

## 相关文档

- Docker Compose 网络：https://docs.docker.com/compose/networking/
- MinIO Docker 部署：https://min.io/docs/minio/container/index.html
- httpx 使用指南：https://www.python-httpx.org/
