# OCR Provider 切换指南

本项目支持三种 OCR 提供商:
- **Mock OCR**: 测试用,返回固定的模拟数据
- **Google Cloud Vision**: 高精度的商业 OCR 服务
- **Azure Computer Vision**: 微软的商业 OCR 服务

## 快速切换 OCR Provider

### 方法 1: 修改环境变量(推荐)

在 `.env` 文件中修改 `OCR_PROVIDER`:

```bash
# 使用 Mock OCR (测试用)
OCR_PROVIDER=mock

# 使用 Google Cloud Vision (推荐)
OCR_PROVIDER=google

# 使用 Azure Computer Vision
OCR_PROVIDER=azure
```

修改后重启服务:

```bash
docker-compose down
docker-compose up -d
```

**注意**: 使用 `make restart` 不会重新读取 `.env` 文件,必须使用 `docker-compose down && docker-compose up -d`。

### 方法 2: 通过 API 参数指定

前端或 API 调用时可以显式指定 provider:

```typescript
// 前端调用
await analyzePage(pageId, {
  provider: 'google',  // 或 'mock', 'azure'
  lang_hints: ['zh-Hans', 'en']
});
```

```bash
# API 调用
curl -X POST http://localhost:8080/v1/pages/<page_id>/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "google",
    "lang_hints": ["zh-Hans", "en"]
  }'
```

如果不指定 `provider` 参数,会使用 `.env` 中配置的默认值。

## 配置各个 OCR Provider

### Mock OCR

无需配置,开箱即用:

```bash
OCR_PROVIDER=mock
```

测试数据位于: `services/doc_process/mock/default.json`

### Google Cloud Vision

1. **获取凭证** (参考 [Google OCR 配置指南](Google-OCR-配置指南.md))
   - 创建 Google Cloud 项目
   - 启用 Cloud Vision API
   - 创建服务账号并下载 JSON 凭证

2. **配置 .env**:

```bash
OCR_PROVIDER=google
GOOGLE_CREDENTIALS_JSON='{"type":"service_account",...}'
```

3. **重启服务**:

```bash
docker-compose down
docker-compose up -d
```

4. **测试**:

```bash
./test-google-ocr.sh
```

### Azure Computer Vision

1. **获取凭证**:
   - 在 Azure Portal 创建 Computer Vision 资源
   - 获取 Endpoint 和 API Key

2. **配置 .env**:

```bash
OCR_PROVIDER=azure
AZURE_VISION_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_VISION_KEY=your-api-key
```

3. **重启服务**:

```bash
docker-compose down
docker-compose up -d
```

## 前端行为

前端 (`apps/web`) 的 OCR provider 选择逻辑:

1. 如果调用 `analyzePage()` 时指定了 `provider` 参数,使用指定的 provider
2. 如果没有指定,API 请求不传 `provider` 字段
3. 后端收到请求后,如果没有 `provider` 字段,使用 `.env` 中的 `OCR_PROVIDER` 值
4. 这样用户只需修改 `.env`,前端会自动使用对应的 OCR

**代码位置**: [apps/web/src/services/api.ts:70-74](apps/web/src/services/api.ts#L70-L74)

```typescript
return api.post(`/v1/pages/${pageId}/analyze`, {
  // 如果没有指定 provider,后端会使用 OCR_PROVIDER 环境变量的值
  ...(params.provider ? { provider: params.provider } : {}),
  lang_hints: params.lang_hints || ['zh-Hans', 'en'],
});
```

## 验证当前使用的 Provider

### 方法 1: 查看日志

```bash
make logs
```

查找以下日志:
- Mock: `MockOCRProvider initialized`
- Google: `Google Cloud Vision OCR completed`
- Azure: `Azure OCR completed`

### 方法 2: 查看环境变量

```bash
docker-compose exec doc_process env | grep OCR_PROVIDER
```

### 方法 3: 测试识别结果

不同 provider 的识别结果会有差异:
- **Mock**: 始终返回固定的 6 个候选框
- **Google/Azure**: 返回实际识别的文字,数量和内容取决于图片

## 费用对比

| Provider | 免费额度 | 付费价格 | 特点 |
|----------|---------|---------|------|
| Mock | 无限 | 免费 | 测试用,固定数据 |
| Google Cloud Vision | 1,000 次/月 | $1.50 / 1,000 次 | 高精度,支持 100+ 语言 |
| Azure Computer Vision | 5,000 次/月 | $1.00 / 1,000 次 | 微软生态,性能稳定 |

## 常见问题

### Q: 修改 .env 后为什么还是用旧的 provider?

A: 需要使用 `docker-compose down && docker-compose up -d` 重新创建容器,而不是 `make restart`。

### Q: 如何让不同环境使用不同的 provider?

A:
- 开发环境: `.env` 中设置 `OCR_PROVIDER=mock`
- 生产环境: 在服务器上设置环境变量 `OCR_PROVIDER=google`

### Q: 可以混合使用多个 provider 吗?

A: 可以!通过 API 参数指定不同的 provider,例如:
```javascript
// 使用 Google OCR
await analyzePage(pageId, { provider: 'google' });

// 使用 Azure OCR
await analyzePage(pageId, { provider: 'azure' });
```

### Q: 前端如何选择 OCR provider?

A: 目前前端使用后端的默认配置。如果需要前端选择器,可以:
1. 在前端添加下拉菜单选择 provider
2. 调用 `analyzePage(pageId, { provider: selectedProvider })`

## 开发建议

1. **日常开发**: 使用 `OCR_PROVIDER=mock`,速度快,无费用
2. **集成测试**: 使用 `OCR_PROVIDER=google`,测试真实识别效果
3. **生产环境**: 根据预算和精度需求选择 Google 或 Azure

## 相关文档

- [Google OCR 配置指南](Google-OCR-配置指南.md) - Google Cloud Vision 详细配置
- [开发流程指南](开发流程指南.md) - 日常开发流程
- [验收指引](验收指引.md) - 功能测试清单
