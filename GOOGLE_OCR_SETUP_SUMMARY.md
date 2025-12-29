# Google Cloud Vision OCR 配置总结

## ✅ 配置成功!

Google Cloud Vision API 已经成功配置并测试通过。

## 配置步骤回顾

### 1. 环境变量配置

在 `.env` 文件中配置:

```bash
# OCR 配置
OCR_PROVIDER=google

# Google Cloud Vision 配置 (单行格式)
GOOGLE_CREDENTIALS_JSON='{"type":"service_account","project_id":"eighth-sensor-472211-k5",...}'
```

### 2. Docker Compose 配置

更新了 `docker-compose.yml`,将环境变量传递给容器:

```yaml
environment:
  OCR_PROVIDER: ${OCR_PROVIDER:-mock}
  GOOGLE_CREDENTIALS_PATH: ${GOOGLE_CREDENTIALS_PATH:-}
  GOOGLE_CREDENTIALS_JSON: ${GOOGLE_CREDENTIALS_JSON:-}
```

### 3. 代码修复

修复了 Docker 容器内网络访问问题:
- `services/doc_process/src/ocr/google_provider.py` - 将 localhost URL 替换为 minio 内部 URL
- `services/doc_process/src/ocr/azure_provider.py` - 同样的修复

## 测试结果

运行 `./test-google-ocr.sh` 测试结果:

```
✓ 识别完成!
  - 识别到 3 个文本候选框

识别的文本内容:
1. PPT Screenshot Sample (置信度: 0.98)
2. Revenue + 12 % (置信度: 0.95)
3. Q4 2024 Performance (置信度: 0.96)
```

## 使用方法

### 通过前端使用

1. 启动服务: `make dev`
2. 访问前端: http://localhost:3000
3. 上传 PPT 截图
4. 点击"分析"按钮,自动使用 Google Cloud Vision OCR

### 通过 API 使用

```bash
# 1. 上传图片
curl -X POST http://localhost:8080/v1/assets/upload \
  -F "file=@your_image.png"

# 2. 创建 page
curl -X POST http://localhost:8080/v1/pages \
  -H "Content-Type: application/json" \
  -d '{"image_url":"<返回的URL>","width":1920,"height":1080}'

# 3. 使用 Google OCR 分析
curl -X POST http://localhost:8080/v1/pages/<page_id>/analyze \
  -H "Content-Type: application/json" \
  -d '{"provider":"google","lang_hints":["zh-Hans","en"]}'
```

### 快速测试

运行测试脚本:

```bash
./test-google-ocr.sh
```

## 切换 OCR Provider

在 `.env` 文件中修改 `OCR_PROVIDER`:

```bash
# 使用 Mock OCR (测试用)
OCR_PROVIDER=mock

# 使用 Google Cloud Vision
OCR_PROVIDER=google

# 使用 Azure Computer Vision
OCR_PROVIDER=azure
```

修改后重启服务:

```bash
docker-compose down
docker-compose up -d
```

## 相关文档

- [Google OCR 配置指南](docs/Google-OCR-配置指南.md) - 详细配置步骤
- [开发流程指南](docs/开发流程指南.md) - 日常开发流程

## 费用说明

Google Cloud Vision API 定价:
- 前 1,000 次/月: **免费**
- 1,001 - 5,000,000 次: $1.50 / 1,000 次

对于开发和测试,免费额度完全够用。

## 故障排查

如果遇到问题,请查看:

1. **查看日志**:
   ```bash
   make logs
   ```

2. **检查配置**:
   ```bash
   # 确认环境变量已正确加载
   docker-compose exec doc_process env | grep GOOGLE
   ```

3. **验证凭证**:
   - 确认 JSON 格式正确(单行,用单引号包裹)
   - 确认 Google Cloud Vision API 已启用
   - 确认服务账号有正确权限

## 已知问题

- ✅ Docker 容器内网络访问 - 已修复
- ✅ 环境变量传递 - 已修复
- ✅ JSON 格式化 - 已修复

## 下一步

可以尝试:
1. 上传真实的 PPT 截图测试识别效果
2. 对比 Mock、Azure、Google 三种 OCR 的识别效果
3. 测试中文、英文混合文本的识别
4. 测试倾斜文字的识别

---

配置日期: 2025-12-29
测试状态: ✅ 通过
