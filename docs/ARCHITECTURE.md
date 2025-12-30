# 系统架构文档

## 总体架构

本项目采用前后端分离的架构,基于 Docker Compose 容器化部署。

```
┌─────────────────────────────────────────────────────────────────┐
│                          浏览器客户端                             │
│                    (React + TypeScript + Vite)                   │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP/REST API
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                       Nginx (Reverse Proxy)                      │
│                      :80 → :3000 (Frontend)                      │
│                      :80/api → :8080 (Backend)                   │
└───────────┬──────────────────────────────────┬──────────────────┘
            │                                  │
            │                                  │
┌───────────▼────────────────┐    ┌───────────▼───────────────────┐
│   Frontend (apps/web)      │    │  Backend (doc_process)        │
│   React SPA                │    │  FastAPI + Uvicorn            │
│   Port: 3000               │    │  Port: 8080                   │
│                            │    │                               │
│   Components:              │    │  Modules:                     │
│   - EditorCanvas           │    │  - API Routes (/v1/*)         │
│   - TextEditor             │    │  - OCR Providers              │
│   - LayerPanel             │    │  - Patch Pipeline             │
│   - Toolbar                │    │  - Style Estimation           │
│   - FileUpload             │    │  - Export Rendering           │
│                            │    │                               │
│   State Management:        │    │  Dependencies:                │
│   - Zustand Store          │    │  - OpenCV (图像处理)          │
│                            │    │  - Pillow (文字渲染)          │
└────────────────────────────┘    │  - NumPy (数组运算)           │
                                  │  - SQLAlchemy (ORM)           │
                                  └───┬─────────────────┬─────────┘
                                      │                 │
                    ┌─────────────────┴──┐         ┌────▼─────────┐
                    │                    │         │              │
            ┌───────▼────────┐  ┌────────▼──────┐ │  MinIO (S3)  │
            │  PostgreSQL    │  │  OCR Services │ │  Port: 9000  │
            │  Port: 5432    │  │               │ │              │
            │                │  │  - Mock       │ │  Buckets:    │
            │  Tables:       │  │  - Azure CV   │ │  - doc-edit  │
            │  - pages       │  │  - Google CV  │ │              │
            │  - candidates  │  └───────────────┘ │  Objects:    │
            │  - patches     │                    │  - assets/   │
            │  - projects    │                    │  - patches/  │
            └────────────────┘                    │  - exports/  │
                                                  └──────────────┘
```

## 核心组件

### 1. 前端应用 (apps/web)

**技术栈**:
- React 18 - UI 框架
- TypeScript 5 - 类型安全
- Vite 5 - 构建工具
- Zustand 4 - 状态管理
- Axios - HTTP 客户端

**目录结构**:
```
apps/web/src/
├── components/          # React 组件
│   ├── EditorCanvas.tsx    # Canvas 画布 (显示图片和图层)
│   ├── TextEditor.tsx      # 文本编辑器 (字号、颜色、内容)
│   ├── LayerPanel.tsx      # 图层管理面板
│   ├── Toolbar.tsx         # 工具栏 (保存、切换、重置)
│   └── FileUpload.tsx      # 文件上传组件
├── services/            # API 服务
│   └── api.ts              # 后端 API 调用封装
├── store/               # 状态管理
│   └── useEditorStore.ts   # Zustand 全局 store
├── types/               # TypeScript 类型定义
│   └── index.ts
└── App.tsx              # 应用入口
```

**状态管理 (Zustand Store)**:
```typescript
{
  currentPage: Page | null,           // 当前页面信息
  layers: Layer[],                    // 图层列表 (patch + text)
  selectedLayer: Layer | null,        // 当前选中图层
  currentProject: Project | null,     // 当前项目
  isLoading: boolean,                 // 加载状态
  loadingMessage: string,             // 加载提示文字
}
```

**关键实现细节**:
- **实时编辑**: 所有编辑操作直接调用 `updateLayer`,无需"应用"按钮
- **状态同步**: `updateLayer` 同时更新 `layers` 和 `selectedLayer` 引用
- **拖拽定位**: Canvas 监听 mouse 事件,实时更新 layer 坐标

### 2. 后端服务 (services/doc_process)

**技术栈**:
- FastAPI - Web 框架
- SQLAlchemy 2 - ORM
- Pydantic - 数据验证
- OpenCV 4 - 图像处理
- Pillow 10 - 文字渲染
- NumPy - 数组运算

**目录结构**:
```
services/doc_process/src/
├── api/                    # API 路由
│   ├── assets.py              # 资源上传/下载
│   ├── pages.py               # Page CRUD + OCR
│   └── projects.py            # Project CRUD + 导出
├── models/                 # 数据模型
│   ├── base.py                # 数据库基类
│   ├── page.py                # Page 模型
│   ├── candidate.py           # Candidate 模型
│   ├── patch.py               # Patch 模型
│   └── project.py             # Project 模型
├── ocr/                    # OCR 提供商
│   ├── base.py                # OCR 接口定义
│   ├── mock_provider.py       # Mock OCR
│   ├── azure_provider.py      # Azure Computer Vision
│   └── google_provider.py     # Google Cloud Vision
├── patch/                  # Patch 生成管道
│   ├── geometry.py            # 几何计算
│   ├── mask.py                # 掩码生成
│   ├── bg_fit.py              # 背景类型分析
│   ├── inpaint.py             # 图像修复
│   ├── compose.py             # 图像合成
│   └── pipeline.py            # 管道流程
├── utils/                  # 工具模块
│   ├── text_style.py          # 文本样式估计
│   ├── export.py              # 导出渲染
│   ├── image.py               # 图像工具
│   └── hash.py                # 哈希计算
├── storage/                # 存储层
│   └── minio_client.py        # MinIO 封装
└── main.py                 # 应用入口
```

**API 端点**:
```
POST   /v1/assets/upload                  # 上传图片
GET    /v1/assets/download?path=...       # 下载文件 (代理)

POST   /v1/pages                          # 创建 Page
POST   /v1/pages/{id}/analyze             # OCR 分析
GET    /v1/pages/{id}/candidates          # 获取候选框
POST   /v1/pages/{id}/patch               # 生成 Patch
POST   /v1/pages/{id}/estimate-style      # 估计样式

GET    /v1/projects                       # 列出项目
POST   /v1/projects                       # 创建项目
GET    /v1/projects/{id}                  # 获取项目
PUT    /v1/projects/{id}                  # 更新项目
DELETE /v1/projects/{id}                  # 删除项目
```

### 3. 数据库 (PostgreSQL)

**表结构**:

**pages** - 页面信息
```sql
id              VARCHAR(64) PRIMARY KEY
image_url       TEXT NOT NULL
width           INTEGER NOT NULL
height          INTEGER NOT NULL
created_at      TIMESTAMP
updated_at      TIMESTAMP
```

**candidates** - OCR 候选框
```sql
id              VARCHAR(64) PRIMARY KEY
page_id         VARCHAR(64) REFERENCES pages(id)
bbox            JSON NOT NULL          -- [x, y, width, height]
text            TEXT NOT NULL
confidence      FLOAT
ocr_result      JSON                   -- 原始 OCR 结果
created_at      TIMESTAMP
```

**patches** - 修复补丁
```sql
id              VARCHAR(64) PRIMARY KEY
candidate_id    VARCHAR(64) REFERENCES candidates(id)
image_url       TEXT NOT NULL
bbox            JSON NOT NULL
bg_type         VARCHAR(32)            -- solid/gradient/complex
created_at      TIMESTAMP
```

**projects** - 项目
```sql
id              VARCHAR(64) PRIMARY KEY
page_data       JSON NOT NULL          -- Page 信息
layers          JSON NOT NULL          -- 图层数组
created_at      TIMESTAMP
updated_at      TIMESTAMP
```

### 4. 对象存储 (MinIO)

**Bucket**: `doc-edit`

**目录结构**:
```
doc-edit/
├── assets/           # 原始上传图片
│   └── ast_xxxxx.png
├── patches/          # 生成的 Patch 图片
│   └── patch_xxxxx.png
└── exports/          # 导出的 PNG (已废弃)
    └── export_xxxxx.png
```

## 数据流

### 完整编辑流程

```
1. 上传图片
   用户拖拽图片 → FileUpload 组件
   → POST /v1/assets/upload
   → 上传到 MinIO (assets/)
   → 返回 image_url

2. 创建 Page
   前端调用 createPage(image_url, width, height)
   → POST /v1/pages
   → 创建 pages 表记录
   → 返回 page_id

3. OCR 分析
   用户点击"开始 OCR"
   → POST /v1/pages/{id}/analyze
   → 调用 OCR Provider (Mock/Azure/Google)
   → 解析结果,创建 candidates 记录
   → 返回候选框列表

4. 选择候选框
   Canvas 显示所有候选框
   → 用户点击选中
   → 自动调用 generatePatch + estimateStyle

5. 生成 Patch
   → POST /v1/pages/{id}/patch
   → Patch Pipeline:
      - 计算扩展边界框
      - 生成文字掩码
      - 分析背景类型
      - 图像修复/填充
      - 合成透明 PNG
   → 上传到 MinIO (patches/)
   → 创建 patches 表记录
   → 返回 patch_url

6. 估计样式
   → POST /v1/pages/{id}/estimate-style
   → 颜色估计 (kmeans/median/edge)
   → 字号估计 (bbox 高度 * 0.7)
   → 返回 { fontSize, color }

7. 创建图层
   前端自动创建两个图层:
   - Patch Layer (kind: "patch")
   - Text Layer (kind: "text")
   → 添加到 Zustand store

8. 编辑文本
   TextEditor 实时修改:
   - 文本内容 (textarea)
   - 字号 (12-500px, slider + number input)
   - 颜色 (color picker)
   → 每次修改调用 updateLayer
   → Canvas 实时重绘

9. 拖拽定位
   Canvas mousedown → mousemove → mouseup
   → 更新 layer.x, layer.y
   → Canvas 实时重绘

10. 保存项目
    用户点击"保存项目"
    → POST /v1/projects (新建)
      或 PUT /v1/projects/{id} (更新)
    → 保存 page_data + layers 到数据库
    → 返回 project_id

11. 切换项目
    用户点击"切换项目"
    → GET /v1/projects (获取列表)
    → 显示下拉菜单
    → 用户选择项目
    → GET /v1/projects/{id}
    → 加载 page_data + layers 到 store
    → Canvas 重新渲染
```

## 关键技术决策

### 1. 为什么使用 Zustand 而不是 Redux?
- **轻量级**: Zustand 只有 1KB,Redux 生态较重
- **简单易用**: 无需 actions/reducers/dispatchers
- **TypeScript 友好**: 类型推导自动完成
- **性能优秀**: 基于 React hooks,按需订阅

### 2. 为什么 selectedLayer 和 layers 需要同步?
- **Zustand 浅比较**: `Object.is()` 检查引用相等性
- **组件订阅**: TextEditor 订阅 `selectedLayer`
- **不同步问题**: 更新 `layers` 不会触发订阅 `selectedLayer` 的组件重渲染
- **解决方案**: `updateLayer` 同时更新两个字段,创建新引用

### 3. 为什么移除 PNG 导出功能?
- **复杂度高**: 需要处理 Docker 网络、CORS、async/await 嵌套
- **维护成本**: 需要额外的 proxy 端点和 URL 转换逻辑
- **需求变化**: 用户主要需求是编辑,不是导出
- **替代方案**: 数据保存在数据库中,可随时恢复编辑

### 4. 为什么 Docker 容器内需要 URL 替换?
- **网络隔离**: 容器内的 `localhost` 指向容器自己
- **服务发现**: Docker Compose 通过服务名通信 (`minio:9000`)
- **前端访问**: 浏览器通过宿主机端口映射 (`localhost:9000`)
- **解决方案**: 后端动态替换 URL (`localhost:9000` → `minio:9000`)

### 5. 为什么支持多 OCR Provider?
- **灵活性**: 不同 Provider 有不同的准确率和价格
- **开发测试**: Mock Provider 无需外部依赖
- **成本控制**: Azure/Google 按调用次数计费
- **可扩展性**: 易于添加新的 Provider (百度、腾讯等)

## 性能优化

### 前端优化
- **Canvas 离屏渲染**: 使用 `OffscreenCanvas` 减少重绘
- **防抖处理**: 文本输入使用 debounce 减少更新频率
- **懒加载图片**: 使用 `IntersectionObserver` 延迟加载
- **Zustand 选择器**: 只订阅需要的 state,避免不必要渲染

### 后端优化
- **异步 I/O**: FastAPI 全异步,提升并发性能
- **数据库索引**: 在 `page_id`、`candidate_id` 上建立索引
- **图像缓存**: OpenCV 图像处理结果缓存到内存
- **连接池**: PostgreSQL 和 MinIO 使用连接池

### Docker 优化
- **分层缓存**: Dockerfile 按依赖变化频率分层
- **多阶段构建**: 减小最终镜像体积
- **健康检查**: 容器启动后自动验证服务可用性

## 安全考虑

### 前端安全
- **XSS 防护**: React 自动转义用户输入
- **CORS 配置**: 后端设置允许的源
- **文件类型验证**: 只允许上传图片文件

### 后端安全
- **输入验证**: Pydantic 模型验证所有输入
- **SQL 注入防护**: SQLAlchemy ORM 自动转义
- **文件大小限制**: 限制上传文件大小 (默认 10MB)
- **敏感信息**: OCR API 密钥通过环境变量配置

### 存储安全
- **MinIO 访问控制**: 只允许内部服务访问
- **PostgreSQL 隔离**: 仅容器间网络可访问
- **数据持久化**: Docker volumes 保证数据不丢失

## 部署架构

### 开发环境 (本地)
```
docker-compose.yml
├── minio (对象存储)
├── postgres (数据库)
├── doc_process (后端服务)
└── web (前端开发服务器 - npm run dev)
```

### 生产环境 (建议)
```
- 前端: CDN 托管静态文件
- 后端: Kubernetes 部署多副本
- 数据库: PostgreSQL 托管服务 (AWS RDS / GCP Cloud SQL)
- 存储: S3 / GCS 替代 MinIO
- 负载均衡: Nginx / ALB
- 监控: Prometheus + Grafana
- 日志: ELK Stack
```

## 扩展性

### 水平扩展
- 后端服务无状态,可无限水平扩展
- MinIO 支持分布式部署
- PostgreSQL 可通过读写分离扩展

### 功能扩展
- 新增 OCR Provider: 实现 `OCRProvider` 接口
- 新增导出格式: 扩展 `export.py` 模块
- 支持更多文件类型: 修改 `assets.py` 验证逻辑
- 添加协作编辑: WebSocket + 操作日志 (CRDT)

## 测试策略

### 单元测试
- 后端: pytest + pytest-asyncio
- 前端: Vitest + React Testing Library

### 集成测试
- API 测试: pytest + httpx
- E2E 测试: Playwright

### 性能测试
- 负载测试: Locust / K6
- 图像处理性能: Python profiling

## 监控指标

### 应用指标
- API 响应时间 (P50, P95, P99)
- 请求成功率
- OCR 调用次数和耗时
- Patch 生成成功率

### 资源指标
- CPU 使用率
- 内存使用率
- 磁盘 I/O
- 网络流量

### 业务指标
- 日活用户数 (DAU)
- 项目创建数
- OCR 调用次数
- 平均编辑时长

---

最后更新: 2024-12-30
