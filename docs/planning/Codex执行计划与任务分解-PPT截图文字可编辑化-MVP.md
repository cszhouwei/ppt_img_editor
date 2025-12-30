# 《Codex 执行计划与任务分解：PPT 截图文字可编辑化 MVP》

> 目标：让 Codex 基本不需要再向你追问即可开干，并且每一步都有可验证的“完成定义（DoD）”。

## 0. 交付目标（MVP Definition of Done）
1. 本地 `docker-compose up` 后可完整跑通：
   - 上传图片 → OCR 分析 → 前端显示候选框 → 点击转换 → 生成 patch → 创建可编辑文本层 → 修改文本 → 保存项目 JSON → 重新加载 → 导出 PNG
2. 有可重复运行的测试：
   - Python 单测：mask/拟合/inpaint/patch 合成核心逻辑
   - 集成测试：Analyze/Patch API 端到端（mock OCR）
3. 有可回归的 golden set（至少 20 张 PPT 截图 + manifest）。

## 1. 工程假设（可替换）
- 后端：Python + FastAPI + OpenCV
- 前端：React + TypeScript（若你们自研编辑器已有，实现 API/IR 适配即可）
- 存储：S3 兼容对象存储（本地用 MinIO）
- 缓存：Redis
- 元数据：Postgres
- OCR：先落 **Azure Read** 或 **Google Vision** 的其中一个；另一个保留 adapter stub + feature flag
- Dev 环境：docker-compose 一键起全栈

## 2. 仓库结构（建议 monorepo）
```
repo/
  apps/
    web/                       # Web 编辑器（React/TS，或替换为你们现有工程）
  services/
    doc_process/               # FastAPI 服务（OCR + Patch 生成 + Project CRUD）
  packages/
    shared/                    # 共享 schema、类型、IR 定义（可选）
  testdata/
    images/                    # golden set 图片
    manifests/                 # golden set 清单与期望
  docker/
    nginx/                     # 可选：反向代理、统一域名、CORS
  docker-compose.yml
  Makefile
  README.md
  .env.example
```

### 2.1 共享 Schema（强烈建议）
用一个 `packages/shared/schema/` 放 JSON Schema（或 zod 定义），避免前后端各写一份。

## 3. 环境与启动方式
### 3.1 `.env.example`
后端（doc_process）至少需要：
```
# Server
PORT=8080
BASE_URL=http://localhost:8080

# Storage (S3 compatible)
S3_ENDPOINT=http://minio:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=doc-edit
S3_REGION=us-east-1
S3_PUBLIC_BASE_URL=http://localhost:9000/doc-edit

# DB/Cache
POSTGRES_DSN=postgresql+psycopg://postgres:postgres@postgres:5432/docedit
REDIS_URL=redis://redis:6379/0

# OCR Provider
OCR_PROVIDER=mock   # mock|azure_read|google_vision
AZURE_OCR_ENDPOINT=
AZURE_OCR_KEY=
GOOGLE_APPLICATION_CREDENTIALS=
```

### 3.2 `docker-compose.yml`（最小服务）
- postgres
- redis
- minio（带初始化 bucket）
- doc_process
- web（或本地起 dev server，compose 可先不包含）

**DoD：** `docker-compose up` 后：
- MinIO 控制台可访问
- `GET /health` 返回 OK
- 前端能加载页面并能调通后端（可先用 mock OCR）

## 4. API 契约（强约束）
> 这里的 API 是 Codex 写代码的“判题标准”。除非你明确要求变更，否则不要在实现中随意改字段名。

### 4.1 上传图片
`POST /v1/assets/upload`
- multipart/form-data: `file`
- Response
```json
{
  "asset_id": "ast_123",
  "image_url": "http://localhost:9000/doc-edit/assets/ast_123.png",
  "width": 1920,
  "height": 1080,
  "sha256": "..."
}
```

### 4.2 创建 Page
`POST /v1/pages`
```json
{
  "image_url": "...",
  "width": 1920,
  "height": 1080
}
```
Response
```json
{ "page_id": "page_123" }
```

### 4.3 OCR Analyze
`POST /v1/pages/{page_id}/analyze`
```json
{
  "provider": "mock",
  "lang_hints": ["zh-Hans", "en"]
}
```
Response
```json
{
  "page_id": "page_123",
  "width": 1920,
  "height": 1080,
  "candidates": [
    {
      "id": "c_001",
      "text": "Revenue +12%",
      "confidence": 0.93,
      "quad": [[120,80],[540,80],[540,144],[120,144]],
      "bbox": {"x":120,"y":80,"w":420,"h":64},
      "angle_deg": 0.0
    }
  ]
}
```

### 4.4 Generate Patch（按需）
`POST /v1/pages/{page_id}/patch`
```json
{
  "candidate_id": "c_001",
  "padding_px": 8,
  "mode": "auto",
  "algo_version": "v1"
}
```
Response
```json
{
  "patch": {
    "id": "p_001",
    "bbox": {"x":110,"y":72,"w":440,"h":84},
    "image_url": "http://localhost:9000/doc-edit/patches/p_001.png"
  },
  "debug": {
    "bg_model": "solid|gradient|fallback",
    "telea_or_ns": "telea|ns",
    "mae": 6.1,
    "latency_ms": 132
  }
}
```

### 4.5 Project 保存/加载
`PUT /v1/projects/{project_id}`
```json
{
  "page": {"page_id":"page_123","image_url":"...","width":1920,"height":1080},
  "layers": [
    {"id":"p_001","kind":"patch","bbox":{"x":110,"y":72,"w":440,"h":84},"image_url":"..."},
    {"id":"t_001","kind":"text","quad":[[...]],"text":"Revenue +12%","style":{"fontFamily":"System","fontSize":32,"fontWeight":600,"fill":"rgba(30,30,30,1)"}}
  ]
}
```
`GET /v1/projects/{project_id}` 返回同结构。

### 4.6 Export PNG（MVP 可前端合成；若后端导出则）
`POST /v1/projects/{project_id}/export/png`
Response
```json
{ "export_url": "http://localhost:9000/doc-edit/exports/proj_123.png" }
```

## 5. Mock OCR（必须先做，降低联调风险）
### 5.1 Mock 数据文件格式
`services/doc_process/mock/ocr_response.json`
```json
{
  "page_sha256": "optional",
  "candidates": [
    {"id":"c_001","text":"Revenue +12%","confidence":0.93,"quad":[[120,80],[540,80],[540,144],[120,144]]}
  ]
}
```

### 5.2 Mock 行为
- `OCR_PROVIDER=mock` 时，Analyze 直接读上述 JSON 返回
- 可支持按 `page_id` 映射不同 mock 文件：`mock/page_{page_id}.json`

**DoD：** 不配置任何云 OCR key，也能完整跑通 MVP 主链路。

## 6. Patch 生成模块（必须按“可测试”方式拆分）
建议实现为纯函数 + 少量 I/O 包装，利于单测。

### 6.1 模块拆分
`services/doc_process/src/patch/`
- `geometry.py`：quad/bbox/旋转矩形等
- `mask.py`：quad rasterize、dilate/erode、ring/edge_mask
- `bg_fit.py`：纯色判定、平面（渐变）拟合、残差计算
- `inpaint.py`：OpenCV inpaint（telea/ns）封装
- `compose.py`：生成透明 patch PNG（alpha feather）
- `pipeline.py`：端到端 `generate_patch(image, candidate, params)` orchestrator

### 6.2 单测要求（最低）
- `test_mask.py`
  - quad rasterize 结果面积合理
  - dilate 后面积增长符合预期
  - ring 非空
- `test_bg_fit.py`
  - 人造纯色图 → 判定为 solid，输出色接近
  - 人造线性渐变图 → 判定为 gradient，MAE 低
- `test_pipeline_smoke.py`
  - 对 testdata 图片 + 若干候选：生成 patch 不报错，输出 png alpha 非全 0

**DoD：** `pytest` 全绿；失败样本在日志里能定位到具体阶段（fit/inpaint/compose）。

## 7. 前端编辑器 MVP（若需要从零搭）
### 7.1 最小前端能力（页面级）
- 上传图片（调用 `/assets/upload`）
- 创建 page（`/pages`）
- Analyze（`/pages/{id}/analyze`）并绘制 candidates overlay
- 点击 candidate：
  - 调 `/patch`
  - 插入 patch layer（image）
  - 插入 text layer（可编辑 input）
- 保存/加载 project JSON（简单按钮）
- 导出：MVP 优先前端合成
  - HTMLCanvas：绘制背景图 → 绘制 patch PNG（透明）→ 绘制文本

### 7.2 坐标系统要求
- world 坐标 = 原图像素坐标
- viewport 只做 scale/translate
- overlay、patch、text 必须同坐标系，否则会对不齐

### 7.3 文本编辑（MVP）
- 选中文本对象后显示 textarea/输入框（overlay），失焦时写回 layer.text
- style：fontSize/fontWeight/fill 最小三项，右侧面板控制

**DoD：** 用 mock OCR + 任意图片能完成“点选转 editable → 改字 → 导出 PNG”。

## 8. Golden Set（回归基线）
### 8.1 图片数量与类别
建议至少 20 张：
- 纯色背景：6
- 线性渐变：6
- 轻纹理/网格：4
- 中英混排：4
（每张至少 6–12 个可识别文本块）

### 8.2 Manifest 格式（不依赖云 OCR）
`testdata/manifests/golden_v1.json`
```json
{
  "version": "v1",
  "cases": [
    {
      "image": "images/slide_001.png",
      "width": 1920,
      "height": 1080,
      "candidates": [
        {
          "id": "c_001",
          "text": "Q4 OKR Review",
          "quad": [[120,80],[760,80],[760,150],[120,150]]
        }
      ]
    }
  ]
}
```

### 8.3 回归断言（MVP 合理约束）
- patch png 存在，尺寸与 bbox 一致
- alpha 非全 0
- patch 生成耗时 < 上限（例如 2s，防止算法退化）
- （可选）对纯色/渐变 case：patch 内部像素方差不应异常增大

## 9. 里程碑任务拆解（严格顺序）
### Milestone 1：基础骨架与存储
1. 初始化 repo（monorepo/或双 repo）
2. doc_process FastAPI 起服务：`GET /health`
3. MinIO 存储封装：上传/下载 helper
4. `POST /v1/assets/upload` 完成（返回 image_url + 宽高 + sha256）
**DoD：** curl 上传图片可拿到可访问的 image_url。

### Milestone 2：Analyze（mock OCR）
1. `/v1/pages` 创建 page
2. `/v1/pages/{id}/analyze`：mock provider 返回 candidates
3. 前端：上传→创建 page→analyze→overlay 显示 quad
**DoD：** 不用云 key，就能看到候选框。

### Milestone 3：Patch pipeline（核心）
1. 实现 `generate_patch()` pipeline（mask→fit→edge_inpaint→compose png）
2. `/v1/pages/{id}/patch`：生成 patch 并上传 MinIO
3. 前端点击候选框：插入 patch layer 覆盖原字
**DoD：** 点击后原字区域被“擦掉”，背景基本自然（纯色/渐变至少可用）。

### Milestone 4：文本层编辑与保存加载
1. 前端创建 text layer（内容来自 OCR）
2. 支持编辑 text、拖拽移动（可选但建议）
3. `/v1/projects/{id}` 保存与加载
**DoD：** 刷新页面后加载 project 可恢复图层与编辑状态。

### Milestone 5：导出
1. 前端导出 PNG（canvas 合成）
2. （可选）后端导出接口
**DoD：** 导出图片中原字已被替换为新字，patch 生效。

### Milestone 6：接入真实 OCR
1. 加入 Azure Read 或 Google Vision adapter（先落一个）
2. feature flag：`OCR_PROVIDER=azure_read` 切换
3. 增加重试与超时
**DoD：** 使用真实 OCR 时仍能跑通全链路；失败会自动降级（仍可手动加文本层）。

## 10. Codex 总指令模板（可直接复制）
```text
你将实现一个“PPT 截图文字可编辑化 MVP”全栈项目。请严格遵守以下要求：
1) 先实现 OCR_PROVIDER=mock 的全链路闭环，再接真实 OCR。
2) API 契约不得随意改名/改字段；必须与文档一致。
3) patch 生成必须 ROI 级处理，包含：mask 生成、纯色/渐变拟合、仅边缘 inpaint、透明 patch 合成。
4) 每个 Milestone 完成后必须提供：
   - 本地启动命令
   - curl/或 UI 操作验证步骤
   - 关键单测/集测通过输出
5) 提交应小步可验证，保持可运行主干。
```

## 11. 风险点与明确的 MVP 取舍
- **OCR 误识别**：MVP 允许用户手动改文字内容；不追求自动纠错。
- **复杂背景修复**：MVP 不保证；提供“patch 失败仅加文本层”的降级。
- **字体还原**：MVP 不追求 font family 精确匹配，先做到字号/颜色/粗细可调即可。
- **旋转/透视**：MVP 支持小角度旋转（angle_deg），不支持透视变形的精确文字重建。
