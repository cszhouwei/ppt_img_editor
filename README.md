# PPT 截图文字可编辑化工具

一个支持 PPT 页面截图文字识别、抹除和可编辑化的 Web 编辑器项目。

## 项目简介

本项目旨在解决用户在 Web 编辑器中导入 PPT 页面截图后无法直接修改图片内文字的问题。通过 OCR 识别、智能背景修复和文本对象化技术,用户可以点选图片中的文字区域,将其转换为可编辑的文本对象,实现真正的文字内容编辑。

## 快速开始

### 前置要求
- Docker >= 20.10
- Docker Compose >= 2.0
- Make (可选,但推荐)

### 本地开发环境

1. 克隆仓库并初始化环境
```bash
make init
# 或手动: cp .env.example .env
```

2. 启动所有服务
```bash
make dev
# 或手动: docker-compose up -d
```

3. 验证服务
```bash
# 健康检查
curl http://localhost:8080/health

# 上传测试图片
curl -X POST http://localhost:8080/v1/assets/upload \
  -F "file=@testdata/images/sample_slide.png"

# 创建 page
curl -X POST http://localhost:8080/v1/pages \
  -H "Content-Type: application/json" \
  -d '{"image_url":"http://localhost:9000/doc-edit/assets/ast_xxx.png","width":1920,"height":1080}'

# OCR 分析 (使用 Mock)
curl -X POST http://localhost:8080/v1/pages/page_xxx/analyze \
  -H "Content-Type: application/json" \
  -d '{"provider":"mock","lang_hints":["zh-Hans","en"]}'

# OCR 分析 (使用 Azure)
# 需要先配置 AZURE_VISION_ENDPOINT 和 AZURE_VISION_KEY
curl -X POST http://localhost:8080/v1/pages/page_xxx/analyze \
  -H "Content-Type: application/json" \
  -d '{"provider":"azure","lang_hints":["zh-Hans","en"]}'

# OCR 分析 (使用 Google Cloud Vision)
# 需要先配置 GOOGLE_CREDENTIALS_PATH 或 GOOGLE_CREDENTIALS_JSON
curl -X POST http://localhost:8080/v1/pages/page_xxx/analyze \
  -H "Content-Type: application/json" \
  -d '{"provider":"google","lang_hints":["zh-Hans","en"]}'
```

### 访问地址
- **前端应用**: http://localhost:3000
- **API 文档**: http://localhost:8080/docs
- **MinIO 控制台**: http://localhost:9001 (minioadmin/minioadmin)
- **健康检查**: http://localhost:8080/health

### 启动前端

```bash
cd apps/web
npm install
npm run dev
```

### 常用命令
```bash
make dev      # 启动开发环境
make down     # 停止所有服务
make logs     # 查看日志
make test     # 运行测试
make clean    # 清理环境
make verify   # 验证上传功能
```

## 项目结构
```
repo/
  apps/web/              # 前端(待实现)
  services/
    doc_process/         # FastAPI 后端服务
      src/
        api/             # API 路由
        storage/         # 存储层
        utils/           # 工具函数
      tests/             # 测试
  docker/                # Docker 配置
  testdata/              # 测试数据
  docs/                  # 文档
```

## 核心功能

- **OCR 文字识别**: 支持多种 OCR 提供商 (Mock / Azure Computer Vision / Google Cloud Vision)
- **智能背景修复**: 抹除原文字并自动补齐背景
- **文本可编辑化**: 将识别的文字转换为可编辑的文本对象
- **实时富文本编辑**: 支持实时修改内容、字号(12-500px)、颜色,变更即时生效
- **拖拽定位**: 鼠标拖拽调整文本位置
- **项目管理**: 保存项目到数据库,随时切换加载历史项目
- **图层管理**: 可视化图层面板,支持选择、删除图层

## 开发状态

### Milestone 1 - 基础骨架与存储 ✅
- [x] Monorepo 结构初始化
- [x] Docker Compose 开发环境
- [x] FastAPI 服务框架
- [x] GET /health 接口
- [x] MinIO 存储封装
- [x] POST /v1/assets/upload 接口

### Milestone 2 - Mock OCR 和 Page 管理 ✅
- [x] 数据库表设计 (pages, candidates)
- [x] SQLAlchemy models 实现
- [x] Mock OCR provider
- [x] POST /v1/pages 接口 (创建 page)
- [x] POST /v1/pages/{id}/analyze 接口 (Mock OCR 分析)
- [x] GET /v1/pages/{id}/candidates 接口 (查询候选框)

### Milestone 3 - Patch Pipeline (核心) ✅
- [x] Patch 生成模块 (geometry, mask, bg_fit, inpaint, compose, pipeline)
- [x] Patches 数据库模型和表
- [x] POST /v1/pages/{id}/patch 接口 (生成 patch)
- [x] OpenCV 图像处理集成
- [x] 背景类型分析 (纯色/渐变/复杂)
- [x] 透明 patch PNG 生成

### Milestone 4 - 文本层编辑与保存 ✅
- [x] Projects 数据库模型和表
- [x] POST /v1/projects 接口 (创建项目)
- [x] GET /v1/projects/{id} 接口 (加载项目)
- [x] PUT /v1/projects/{id} 接口 (保存项目)
- [x] DELETE /v1/projects/{id} 接口 (删除项目)
- [x] 文本样式估计工具 (颜色、字号、字重)
- [x] POST /v1/pages/{id}/estimate-style 接口 (估计样式)

### Milestone 5 - 导出功能 ✅
- [x] 图像合成工具 (下载、混合、渲染)
- [x] POST /v1/projects/{id}/export/png 接口 (导出 PNG)
- [x] Patch 层叠加 (透明 alpha 混合)
- [x] 文本层渲染 (PIL ImageDraw)
- [x] 字体支持 (DejaVu Sans)
- [x] 导出文件上传到 MinIO

### Milestone 6 - 真实 OCR 接入 ✅
- [x] OCR Provider 抽象接口设计
- [x] Azure Computer Vision Read API 集成
- [x] Google Cloud Vision API 集成
- [x] OCR provider 配置和特性开关
- [x] 结果格式解析和归一化 (Azure/Google)
- [x] 错误处理和重试逻辑
- [x] 环境变量配置 (Azure/Google)
- [x] Provider 选择逻辑 (mock/azure/google)

### Milestone 7 - 前端实现 ✅
- [x] React + TypeScript + Vite 项目初始化
- [x] 图片上传组件 (支持拖拽)
- [x] OCR 结果可视化 (Canvas 渲染)
- [x] 交互式候选框选择
- [x] 自动生成 Patch 和文本图层
- [x] Zustand 状态管理
- [x] API 服务封装
- [x] TypeScript 类型定义

### Milestone 7 - 前端 UI 增强 ✅
- [x] 文本内容编辑 (TextEditor 组件)
- [x] 文本样式编辑 (颜色、字号、字重)
- [x] 项目保存 UI (Toolbar 组件)
- [x] 图层管理面板 (LayerPanel 组件)
- [x] 响应式三栏布局
- [x] 加载状态和错误处理
- [x] 拖拽调整文本位置

### Milestone 8 - 实时编辑与状态管理优化 ✅
- [x] 实时编辑功能 - 无需"应用更改"按钮
- [x] 字号范围扩展至 12-500px
- [x] Zustand 状态同步修复 (selectedLayer 与 layers 同步)
- [x] 编辑控件实时显示当前值
- [x] 字号滑块和数字输入框独立工作并正确同步
- [x] 颜色选择器实时更新

### Milestone 9 - 项目管理增强 ✅
- [x] 项目列表查询接口 (GET /v1/projects)
- [x] 项目切换菜单 - 下拉显示已保存项目
- [x] 项目加载功能 - 一键恢复历史项目
- [x] 当前项目高亮显示
- [x] 项目更新时间显示 (中文本地化)
- [x] 加载状态指示器

## 技术栈

- **后端**: Python 3.11 + FastAPI + Uvicorn
- **数据库**: PostgreSQL 15
- **对象存储**: MinIO (S3 兼容)
- **OCR**: Azure Computer Vision / Google Cloud Vision (可配置为 Mock)
- **图像处理**: OpenCV + Pillow + NumPy
- **前端**: React 18 + TypeScript + Vite + Zustand
- **容器化**: Docker + Docker Compose

## 详细文档

### 📚 文档导航
- **[docs/README.md](docs/README.md)** - 完整的文档导航和分类索引

### 核心文档
- **[CHANGELOG.md](CHANGELOG.md)** - 版本历史和更新记录
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - 贡献指南和开发规范
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - 系统架构和技术设计
- **[docs/MAINTENANCE_SUMMARY.md](docs/MAINTENANCE_SUMMARY.md)** - 维护总结和项目状态

### 规划文档 (docs/planning/)
- [产品需求文档 (PRD)](docs/planning/PRD-PPT截图文字可编辑化-MVP.md)
- [技术规格文档 (TechSpec)](docs/planning/TechSpec-PPT截图文字可编辑化-MVP.md)
- [执行计划与任务分解](docs/planning/Codex执行计划与任务分解-PPT截图文字可编辑化-MVP.md)

### 使用指南 (docs/guides/)
- **[开发流程指南](docs/guides/开发流程指南.md)** - 日常开发、调试流程
- **[验收指引](docs/guides/验收指引.md)** - 功能测试和验收清单
- **[OCR Provider 切换指南](docs/guides/OCR-Provider-切换指南.md)** - OCR 服务配置
- **[Google OCR 配置指南](docs/guides/Google-OCR-配置指南.md)** - Google Cloud Vision 配置

### Bug 修复说明 (docs/fixes/)
- [selectedLayer 同步修复](docs/fixes/selectedLayer同步修复说明.md)
- [Docker 网络访问修复](docs/fixes/Docker网络访问修复说明.md)
- [Patch 生成修复](docs/fixes/Patch生成修复说明.md)
- [更多修复说明...](docs/fixes/)

### 技术优化说明 (docs/technical/)
- [实时编辑功能实现](docs/technical/实时编辑功能说明.md)
- [字体大小估算优化](docs/technical/字体大小估算优化说明.md)
- [文字颜色估计优化](docs/technical/文字颜色估计优化说明.md)
- [更多技术说明...](docs/technical/)

### 已知问题与限制
- 字体目前仅支持 DejaVu Sans (系统内置)
- 导出功能已移除,项目数据保存在数据库中
- 大文件上传可能需要较长时间

## License

待定
