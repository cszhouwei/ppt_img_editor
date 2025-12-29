# Google Cloud Vision OCR 完整配置总结

## ✅ 配置状态

- ✅ Google Cloud Vision API 凭证已配置
- ✅ 后端环境变量已设置 (`OCR_PROVIDER=google`)
- ✅ Docker 容器环境变量传递已修复
- ✅ Docker 内部网络访问已修复
- ✅ 前端代码已更新,自动使用后端配置的 provider
- ✅ API 测试通过,成功识别文字

## 修改的文件

### 配置文件
1. **`.env`**
   - 设置 `OCR_PROVIDER=google`
   - 添加 `GOOGLE_CREDENTIALS_JSON` (单行格式的 JSON)

2. **`docker-compose.yml`**
   - 添加环境变量传递:
     ```yaml
     OCR_PROVIDER: ${OCR_PROVIDER:-mock}
     GOOGLE_CREDENTIALS_JSON: ${GOOGLE_CREDENTIALS_JSON:-}
     ```

### 后端代码
3. **`services/doc_process/src/api/pages.py`**
   - 修改 `AnalyzeRequest.provider` 类型为 `Optional[str] = None`
   - 允许不传 provider,使用环境变量配置

4. **`services/doc_process/src/ocr/google_provider.py`**
   - 修复 `_download_image()` 方法
   - 将 `localhost:9000` 替换为 `minio:9000` (Docker 内部网络)

5. **`services/doc_process/src/ocr/azure_provider.py`**
   - 同样的网络修复

### 前端代码
6. **`apps/web/src/services/api.ts`**
   - 修改 `analyzePage()` 函数
   - 不传 `provider` 参数时,让后端使用环境变量的默认值

### 文档
7. **`docs/Google-OCR-配置指南.md`** - 详细配置步骤
8. **`docs/OCR-Provider-切换指南.md`** - Provider 切换指南
9. **`GOOGLE_OCR_SETUP_SUMMARY.md`** - 配置总结
10. **`.env.google-example`** - 配置示例
11. **`test-google-ocr.sh`** - 自动化测试脚本

## 测试结果

### API 测试
```bash
$ ./test-google-ocr.sh

✓ 识别完成!
  - 识别到 3 个文本候选框

识别的文本内容:
1. PPT Screenshot Sample (置信度: 0.98)
2. Revenue + 12 % (置信度: 0.95)
3. Q4 2024 Performance (置信度: 0.96)
```

### 日志验证
```
ppt-editor-doc-process  | 2025-12-29 14:26:08,132 - src.ocr.google_provider - INFO - Google Cloud Vision OCR completed: 3 candidates
```

## 使用方法

### 前端使用(推荐)
1. 访问 http://localhost:3000
2. 上传 PPT 截图
3. 点击"分析"按钮
4. 系统自动使用 Google Cloud Vision OCR
5. 在画布上看到识别的候选框

### API 使用
```bash
# 1. 上传图片
curl -X POST http://localhost:8080/v1/assets/upload \
  -F "file=@your_image.png"

# 2. 创建 page
curl -X POST http://localhost:8080/v1/pages \
  -H "Content-Type: application/json" \
  -d '{"image_url":"<URL>","width":1920,"height":1080}'

# 3. OCR 分析 (不指定 provider,使用环境变量的 google)
curl -X POST http://localhost:8080/v1/pages/<page_id>/analyze \
  -H "Content-Type: application/json" \
  -d '{"lang_hints":["zh-Hans","en"]}'

# 或显式指定 provider
curl -X POST http://localhost:8080/v1/pages/<page_id>/analyze \
  -H "Content-Type: application/json" \
  -d '{"provider":"google","lang_hints":["zh-Hans","en"]}'
```

### 快速测试
```bash
./test-google-ocr.sh
```

## 切换 OCR Provider

### 切换到 Mock (测试用)
```bash
# 1. 修改 .env
OCR_PROVIDER=mock

# 2. 重启服务
docker-compose down
docker-compose up -d
```

### 切换到 Azure
```bash
# 1. 修改 .env
OCR_PROVIDER=azure
AZURE_VISION_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_VISION_KEY=your-api-key

# 2. 重启服务
docker-compose down
docker-compose up -d
```

### 切换回 Google
```bash
# 1. 修改 .env
OCR_PROVIDER=google

# 2. 重启服务
docker-compose down
docker-compose up -d
```

**注意**: 必须使用 `docker-compose down && up` 而不是 `make restart`,因为需要重新读取环境变量。

## 验证当前 Provider

### 方法 1: 查看日志
```bash
make logs
```
- Mock: `MockOCRProvider initialized`
- Google: `Google Cloud Vision OCR completed`
- Azure: `Azure OCR completed`

### 方法 2: 查看环境变量
```bash
docker-compose exec doc_process env | grep OCR_PROVIDER
```

### 方法 3: 测试识别
- Mock: 总是返回固定的 6 个候选框
- Google/Azure: 返回真实识别结果

## 费用说明

- **免费额度**: 1,000 次/月
- **付费价格**: $1.50 / 1,000 次
- **开发建议**: 日常开发使用 Mock,集成测试使用 Google

详见: https://cloud.google.com/vision/pricing

## 故障排查

### 问题 1: 修改 .env 后还是用旧的 provider
**解决**: 使用 `docker-compose down && docker-compose up -d`,不要用 `make restart`

### 问题 2: 认证失败
**解决**:
- 检查 `GOOGLE_CREDENTIALS_JSON` 格式(单行,单引号包裹)
- 检查 Google Cloud Vision API 是否启用
- 检查服务账号权限

### 问题 3: 连接超时
**解决**:
- 检查网络连接
- 检查 MinIO 服务状态: `docker-compose ps`
- 查看详细日志: `make logs`

### 问题 4: 前端还在用 Mock
**解决**:
- 确认后端 `.env` 中 `OCR_PROVIDER=google`
- 确认已执行 `docker-compose down && up`
- 刷新前端页面
- 查看后端日志确认使用的 provider

## 架构说明

### 默认 Provider 选择逻辑

```
用户上传图片并点击"分析"
    ↓
前端调用 analyzePage(pageId)
    ↓
前端不传 provider 参数
    ↓
后端 AnalyzeRequest 收到请求 (provider = None)
    ↓
后端使用 settings.ocr_provider (从 .env 读取)
    ↓
加载对应的 OCR Provider (GoogleOCRProvider)
    ↓
下载图片 (localhost → minio 内部 URL)
    ↓
调用 Google Cloud Vision API
    ↓
返回识别结果
```

### 文件职责

| 文件 | 职责 |
|------|------|
| `.env` | 存储配置(OCR_PROVIDER, GOOGLE_CREDENTIALS_JSON) |
| `docker-compose.yml` | 将 .env 传递给容器 |
| `config.py` | 从环境变量读取配置 |
| `pages.py` | API 路由,选择 OCR provider |
| `google_provider.py` | Google Cloud Vision 集成 |
| `api.ts` | 前端 API 调用 |

## 下一步

1. ✅ 已完成: 配置 Google Cloud Vision OCR
2. ✅ 已完成: 前端自动使用配置的 provider
3. 可选: 添加前端 provider 选择器(下拉菜单)
4. 可选: 添加 OCR 结果缓存(减少 API 调用)
5. 可选: 添加多 provider 对比功能

## 相关文档

- [Google OCR 配置指南](docs/Google-OCR-配置指南.md) - 详细配置步骤
- [OCR Provider 切换指南](docs/OCR-Provider-切换指南.md) - 切换 provider
- [开发流程指南](docs/开发流程指南.md) - 日常开发流程
- [README.md](README.md) - 项目总览

---

**配置完成日期**: 2025-12-29
**配置状态**: ✅ 测试通过
**当前 Provider**: Google Cloud Vision
**前端状态**: 自动使用后端配置
