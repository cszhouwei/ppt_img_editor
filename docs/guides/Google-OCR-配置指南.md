# Google Cloud Vision OCR 配置指南

本文档说明如何配置项目使用 Google Cloud Vision API 进行 OCR 识别。

## 前置要求

1. Google Cloud 账号
2. 已启用 Cloud Vision API 的项目
3. 服务账号 JSON 凭证文件

## 步骤 1: 创建 Google Cloud 项目和服务账号

### 1.1 创建项目(如果还没有)

1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 点击顶部项目选择器,选择"新建项目"
3. 输入项目名称(例如: `ppt-ocr`)
4. 点击"创建"

### 1.2 启用 Cloud Vision API

1. 在 Google Cloud Console 中,选择你的项目
2. 导航到"API 和服务" > "库"
3. 搜索"Cloud Vision API"
4. 点击"启用"

### 1.3 创建服务账号

1. 导航到"IAM 和管理" > "服务账号"
2. 点击"创建服务账号"
3. 输入服务账号名称(例如: `ppt-ocr-service`)
4. 点击"创建并继续"
5. 选择角色:"Cloud Vision API 用户" 或 "编辑者"
6. 点击"完成"

### 1.4 下载 JSON 凭证

1. 在服务账号列表中,点击你刚创建的服务账号
2. 切换到"密钥"标签页
3. 点击"添加密钥" > "创建新密钥"
4. 选择"JSON"格式
5. 点击"创建",JSON 文件会自动下载

## 步骤 2: 配置项目

你有两种配置方式:

### 方式 A: 使用 JSON 字符串(推荐,更简单)

1. **打开下载的 JSON 文件**,复制全部内容

2. **修改 .env 文件**:

```bash
# OCR 配置
OCR_PROVIDER=google

# Google Cloud Vision 配置
# 将 JSON 内容粘贴到下面(用单引号包裹,保持在一行)
GOOGLE_CREDENTIALS_JSON='{"type":"service_account","project_id":"your-project-id",...}'
```

**注意**:
- 整个 JSON 必须用单引号 `'` 包裹
- JSON 内容保持在一行(不要换行)
- 如果 JSON 中有换行符(如 `\n`),保持原样

### 方式 B: 使用文件路径

1. **将 JSON 文件复制到项目目录**:

```bash
cp ~/Downloads/your-service-account.json /Users/bytedance/Downloads/projects/ppt_img_editor/google-credentials.json
```

2. **修改 docker-compose.yml**,在 `doc_process` 服务的 `volumes` 部分添加:

```yaml
volumes:
  - ./services/doc_process/src:/app/src
  - ./testdata:/app/testdata
  - ./google-credentials.json:/app/google-credentials.json  # 新增
```

3. **修改 docker-compose.yml**,在 `doc_process` 服务的 `environment` 部分添加:

```yaml
environment:
  # ... 其他配置 ...
  OCR_PROVIDER: google
  GOOGLE_CREDENTIALS_PATH: /app/google-credentials.json  # 新增
```

4. **修改 .env 文件**:

```bash
# OCR 配置
OCR_PROVIDER=google

# Google Cloud Vision 配置
GOOGLE_CREDENTIALS_PATH=/app/google-credentials.json
```

5. **更新 .gitignore**,避免提交凭证文件:

```bash
echo "google-credentials.json" >> .gitignore
```

## 步骤 3: 重启服务

无论使用哪种方式,都需要重启服务使配置生效:

```bash
make rebuild
```

或者手动执行:

```bash
docker-compose down
docker-compose up -d
```

## 步骤 4: 验证配置

### 4.1 检查服务健康

```bash
make health
```

### 4.2 上传图片并分析

```bash
# 1. 上传图片
curl -X POST http://localhost:8080/v1/assets/upload \
  -F "file=@testdata/images/sample_slide.png" \
  | python3 -m json.tool

# 记录返回的 image_url

# 2. 创建 page
curl -X POST http://localhost:8080/v1/pages \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "http://localhost:9000/doc-edit/assets/ast_xxx.png",
    "width": 1920,
    "height": 1080
  }' | python3 -m json.tool

# 记录返回的 page_id

# 3. 使用 Google Cloud Vision 分析
curl -X POST http://localhost:8080/v1/pages/page_xxx/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "google",
    "lang_hints": ["zh-Hans", "en"]
  }' | python3 -m json.tool
```

如果配置正确,你会看到 Google Cloud Vision 识别的文字结果。

### 4.3 检查日志

```bash
make logs
```

查找日志中的信息:
- `Google Cloud Vision OCR completed: X candidates` - 表示成功
- `Google Cloud Vision API error: ...` - 表示 API 调用失败
- `Failed to download image: ...` - 表示图片下载失败

## 常见问题

### 1. 认证失败

**错误**: `google.auth.exceptions.DefaultCredentialsError`

**原因**: 凭证配置不正确

**解决**:
- 确认 `GOOGLE_CREDENTIALS_JSON` 或 `GOOGLE_CREDENTIALS_PATH` 已正确设置
- 确认 JSON 格式正确(没有多余的换行或空格)
- 确认文件路径正确(使用绝对路径 `/app/...`)

### 2. API 未启用

**错误**: `Cloud Vision API has not been used in project XXX before`

**原因**: 项目中未启用 Cloud Vision API

**解决**:
1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 导航到"API 和服务" > "库"
3. 搜索"Cloud Vision API"并启用

### 3. 权限不足

**错误**: `Permission denied` 或 `Forbidden`

**原因**: 服务账号权限不足

**解决**:
1. 访问"IAM 和管理" > "IAM"
2. 找到你的服务账号
3. 添加"Cloud Vision API 用户"角色

### 4. 配额超限

**错误**: `Quota exceeded`

**原因**: 超过免费配额或 API 调用限制

**解决**:
- 检查 [Google Cloud Console 配额页面](https://console.cloud.google.com/iam-admin/quotas)
- 考虑升级到付费账号或申请配额增加

### 5. 网络连接问题

**错误**: `Failed to download image`

**原因**: 容器无法访问 MinIO 或外部 URL

**解决**:
- 确认 MinIO 服务正常运行: `docker-compose ps`
- 确认网络配置正确
- 使用内部 URL (http://minio:9000) 而非外部 URL

## 切换回 Mock OCR

如果需要切换回 Mock OCR(用于测试):

```bash
# 修改 .env
OCR_PROVIDER=mock

# 重启服务
make restart
```

## 费用说明

Google Cloud Vision API 定价(2024):
- 前 1,000 次/月: 免费
- 1,001 - 5,000,000 次: $1.50 / 1,000 次
- 5,000,001+ 次: $0.60 / 1,000 次

详细定价请参考: https://cloud.google.com/vision/pricing

## 支持的语言

Google Cloud Vision 支持 100+ 种语言,包括:
- `zh-Hans`: 简体中文
- `zh-Hant`: 繁体中文
- `en`: 英文
- `ja`: 日文
- `ko`: 韩文
- 等等...

完整语言列表: https://cloud.google.com/vision/docs/languages

## 参考文档

- [Google Cloud Vision API 文档](https://cloud.google.com/vision/docs)
- [Python 客户端库](https://cloud.google.com/python/docs/reference/vision/latest)
- [认证指南](https://cloud.google.com/docs/authentication/getting-started)
