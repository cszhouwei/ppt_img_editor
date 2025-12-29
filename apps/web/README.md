# PPT 截图文字编辑器 - 前端

基于 React + TypeScript + Vite 构建的 PPT 截图文字编辑器前端应用。

## 快速开始

### 安装依赖

```bash
cd apps/web
npm install
```

### 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:3000

## 功能特性

- 图片上传 (支持拖拽)
- OCR 文字识别
- 候选框可视化
- 交互式文字编辑
- 项目保存/加载
- PNG 导出

## 技术栈

- **React 18** - UI 框架
- **TypeScript** - 类型安全
- **Vite** - 构建工具
- **Zustand** - 状态管理
- **Axios** - HTTP 客户端

## 项目结构

```
src/
├── components/       # React 组件
│   ├── ImageUploader.tsx
│   └── EditorCanvas.tsx
├── services/         # API 服务
│   └── api.ts
├── store/            # 状态管理
│   └── useEditorStore.ts
├── types/            # TypeScript 类型
│   └── index.ts
├── App.tsx           # 主应用
└── main.tsx          # 入口文件
```

## API 代理

开发环境下,所有 `/api/*` 请求会自动代理到 `http://localhost:8080`。

确保后端服务已启动:

```bash
cd ../..
make dev
```
