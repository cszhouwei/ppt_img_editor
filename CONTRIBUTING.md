# 贡献指南

感谢您对本项目的关注! 本文档将帮助您了解如何参与项目开发。

## 开发环境设置

### 前置要求
- Docker >= 20.10
- Docker Compose >= 2.0
- Node.js >= 18 (前端开发)
- Python >= 3.11 (后端开发)
- Make (可选,推荐)

### 快速开始

1. **克隆仓库**
```bash
git clone <repo-url>
cd ppt_img_editor
```

2. **初始化环境**
```bash
make init
# 或手动: cp .env.example .env
```

3. **启动服务**
```bash
make dev
# 或手动: docker-compose up -d
```

4. **启动前端开发服务器**
```bash
cd apps/web
npm install
npm run dev
```

5. **验证环境**
```bash
# 检查后端健康状态
curl http://localhost:8080/health

# 检查前端
open http://localhost:3000
```

## 项目结构

```
ppt_img_editor/
├── apps/
│   └── web/                   # 前端应用 (React + TypeScript)
├── services/
│   └── doc_process/           # 后端服务 (FastAPI + Python)
├── docs/                      # 文档
├── docker/                    # Docker 配置
├── testdata/                  # 测试数据
├── CHANGELOG.md               # 版本历史
├── CONTRIBUTING.md            # 本文件
└── README.md                  # 项目说明
```

## 开发流程

### 1. 创建功能分支

```bash
git checkout -b feature/your-feature-name
# 或
git checkout -b fix/bug-description
```

### 2. 进行开发

#### 前端开发 (apps/web)

**代码规范**:
- 使用 TypeScript,避免使用 `any` 类型
- 遵循 ESLint 规则
- 使用 Prettier 格式化代码
- 组件使用函数式组件 + Hooks

**运行检查**:
```bash
cd apps/web

# 类型检查
npm run type-check

# Lint 检查
npm run lint

# 格式化代码
npm run format

# 运行测试
npm test
```

**常见任务**:
- 新增组件: `src/components/YourComponent.tsx`
- 添加 API 调用: 在 `src/services/api.ts` 中添加方法
- 状态管理: 在 `src/store/useEditorStore.ts` 中添加 state

#### 后端开发 (services/doc_process)

**代码规范**:
- 遵循 PEP 8 规范
- 使用 Black 格式化代码
- 使用类型提示 (Type Hints)
- 编写 docstrings

**运行检查**:
```bash
cd services/doc_process

# 格式化代码
black src/ tests/

# 排序 imports
isort src/ tests/

# Lint 检查
ruff check src/ tests/

# 类型检查
mypy src/

# 运行测试
pytest
```

**常见任务**:
- 新增 API 端点: 在 `src/api/` 目录下相应文件中添加
- 添加数据模型: 在 `src/models/` 目录下创建新模型
- 图像处理: 在 `src/utils/` 或 `src/patch/` 中添加工具函数

### 3. 编写测试

#### 前端测试

使用 Vitest + React Testing Library:

```typescript
// src/components/__tests__/YourComponent.test.tsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import YourComponent from '../YourComponent';

describe('YourComponent', () => {
  it('renders correctly', () => {
    render(<YourComponent />);
    expect(screen.getByText('Hello')).toBeInTheDocument();
  });
});
```

#### 后端测试

使用 pytest + pytest-asyncio:

```python
# services/doc_process/tests/test_api.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
```

### 4. 提交代码

**Commit 消息规范**:

遵循 [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type**:
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式 (不影响功能)
- `refactor`: 重构 (不是新功能也不是 Bug 修复)
- `perf`: 性能优化
- `test`: 测试相关
- `chore`: 构建/工具链相关

**示例**:
```bash
git commit -m "feat(editor): add text color picker"
git commit -m "fix(api): resolve Docker network connection issue"
git commit -m "docs(readme): update installation instructions"
```

### 5. 推送分支

```bash
git push origin feature/your-feature-name
```

### 6. 创建 Pull Request

1. 前往 GitHub 仓库
2. 点击 "New Pull Request"
3. 选择您的分支
4. 填写 PR 描述:
   - **What**: 做了什么改动
   - **Why**: 为什么要做这个改动
   - **How**: 如何实现的
   - **Testing**: 如何测试
5. 等待代码审查

## 代码审查

### 审查者职责
- 检查代码逻辑正确性
- 验证测试覆盖率
- 确保遵循项目规范
- 提供建设性反馈

### 提交者职责
- 及时回复审查意见
- 修复审查中发现的问题
- 保持代码简洁清晰
- 确保 CI 通过

## 常见开发场景

### 添加新的 API 端点

1. 在 `services/doc_process/src/api/` 下相应文件中添加路由
2. 添加 Pydantic 模型进行请求/响应验证
3. 编写单元测试
4. 在前端 `apps/web/src/services/api.ts` 中添加调用方法
5. 更新 API 文档

### 添加新的前端组件

1. 在 `apps/web/src/components/` 下创建组件文件
2. 定义 TypeScript 类型
3. 使用 Zustand store 进行状态管理
4. 编写单元测试
5. 在父组件中引入使用

### 修复 Bug

1. 重现 Bug
2. 编写失败的测试用例
3. 修复代码让测试通过
4. 验证不影响其他功能
5. 提交 PR

### 性能优化

1. 使用 profiling 工具定位瓶颈
2. 实现优化方案
3. 添加性能测试
4. 对比优化前后数据
5. 在 PR 中说明性能提升

## 调试技巧

### 前端调试

**React DevTools**:
- 安装 React DevTools 浏览器插件
- 查看组件树和 state

**Zustand DevTools**:
```typescript
// 在 store 中启用 devtools
import { devtools } from 'zustand/middleware';

export const useEditorStore = create(
  devtools((set) => ({
    // ...
  }))
);
```

**浏览器控制台**:
```typescript
// 在代码中添加 console.log 查看变量
console.log('Current layer:', layer);
console.error('Error occurred:', error);
```

### 后端调试

**查看日志**:
```bash
# 实时查看后端日志
docker-compose logs -f doc_process

# 查看最近 100 行
docker-compose logs --tail=100 doc_process
```

**进入容器调试**:
```bash
# 进入容器
docker-compose exec doc_process bash

# 运行 Python shell
docker-compose exec doc_process python

# 手动测试代码
>>> from src.utils.text_style import estimate_font_size
>>> estimate_font_size(...)
```

**使用 pdb 调试器**:
```python
# 在代码中插入断点
import pdb; pdb.set_trace()

# 运行时会暂停,可以交互式调试
```

## 文档更新

### 何时更新文档
- 添加新功能
- 修改 API 接口
- 修复重要 Bug
- 更改架构设计

### 需要更新的文档
- `README.md` - 项目说明和快速开始
- `CHANGELOG.md` - 版本历史
- `docs/ARCHITECTURE.md` - 架构文档
- 相关技术文档 (在 `docs/` 目录下)

## 发布流程

### 版本号规范

遵循 [Semantic Versioning](https://semver.org/):
- MAJOR.MINOR.PATCH (例如: 1.2.3)
- MAJOR: 不兼容的 API 改动
- MINOR: 向下兼容的新功能
- PATCH: 向下兼容的 Bug 修复

### 发布步骤

1. 更新 `CHANGELOG.md`
2. 更新版本号
3. 创建 Git tag
4. 构建 Docker 镜像
5. 推送到镜像仓库

## 常见问题

### Q: Docker 容器无法启动?
A: 检查端口占用,清理旧容器:
```bash
docker-compose down
docker system prune -a
make dev
```

### Q: 前端无法访问后端 API?
A: 检查 Vite 代理配置 (`vite.config.ts`) 和后端 CORS 设置

### Q: MinIO 连接失败?
A: 确认 MinIO 容器健康状态:
```bash
docker-compose ps
docker-compose logs minio
```

### Q: 数据库迁移问题?
A: 重置数据库:
```bash
docker-compose down -v  # 删除 volumes
make dev                # 重新启动
```

## 联系方式

- 问题反馈: GitHub Issues
- 功能建议: GitHub Discussions
- 紧急问题: [联系邮箱]

## 行为准则

- 尊重所有贡献者
- 保持友善和专业
- 提供建设性反馈
- 遵守开源协议

---

感谢您的贡献! 🎉
