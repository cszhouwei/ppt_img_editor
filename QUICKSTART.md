# 快速开始

## 首次启动 (3 步)

```bash
# 1. 初始化环境
make init

# 2. 启动所有服务
make dev

# 3. 检查服务健康
make health
```

访问:
- 前端: http://localhost:3000
- API 文档: http://localhost:8080/docs
- MinIO 控制台: http://localhost:9001 (minioadmin/minioadmin)

## 日常开发

### 修改后端代码
```bash
# Python 代码修改后
make restart

# 修改了依赖或 mock 数据后
make rebuild
```

### 启动前端
```bash
cd apps/web
npm install    # 首次或依赖更新后
npm run dev
```

### 查看日志
```bash
make logs
```

## 遇到问题?

### 上传失败
```bash
# 1. 查看日志
make logs

# 2. 如果是数据库错误
make reset-db
```

### 完全重置
```bash
make clean
make dev
```

## 常用命令

| 命令 | 说明 |
|------|------|
| `make dev` | 启动开发环境 |
| `make restart` | 重启后端 |
| `make rebuild` | 重新构建后端 |
| `make health` | 健康检查 |
| `make reset-db` | 清除数据 |
| `make logs` | 查看日志 |
| `make verify` | 验证上传 |

## 更多信息

详细文档请查看:
- [开发流程指南](docs/开发流程指南.md)
- [验收指引](docs/验收指引.md)
- [完整 README](README.md)
