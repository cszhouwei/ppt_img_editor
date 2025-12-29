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
```

### 访问地址
- API 文档: http://localhost:8080/docs
- MinIO 控制台: http://localhost:9001 (minioadmin/minioadmin)
- 健康检查: http://localhost:8080/health

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

- **OCR 文字识别**: 自动识别 PPT 截图中的文字区域
- **智能背景修复**: 抹除原文字并自动补齐背景
- **文本可编辑化**: 将识别的文字转换为可编辑的文本对象
- **富文本编辑**: 支持修改内容、样式、位置等
- **项目保存与导出**: 支持保存为 JSON 项目文件和导出为 PNG

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

### 后续计划
- [ ] Milestone 5: 导出
- [ ] Milestone 6: 真实 OCR 接入

## 技术栈

- **后端**: Python 3.11 + FastAPI + Uvicorn
- **数据库**: PostgreSQL 15
- **对象存储**: MinIO (S3 兼容)
- **前端**: React + TypeScript (待实现)
- **容器化**: Docker + Docker Compose

## 详细文档

- [产品需求文档 (PRD)](docs/PRD-PPT截图文字可编辑化-MVP.md) - 产品背景、目标和功能范围
- [技术规格文档 (TechSpec)](docs/TechSpec-PPT截图文字可编辑化-MVP.md) - 技术架构和实现方案
- [执行计划与任务分解](docs/Codex执行计划与任务分解-PPT截图文字可编辑化-MVP.md) - 详细的开发计划

## License

待定
