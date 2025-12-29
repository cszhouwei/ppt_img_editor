#!/bin/bash

# Google Cloud Vision OCR 测试脚本

set -e

echo "========================================="
echo "Google Cloud Vision OCR 功能测试"
echo "========================================="
echo ""

# 1. 上传测试图片
echo "步骤 1/4: 上传测试图片..."
UPLOAD_RESPONSE=$(curl -s -X POST http://localhost:8080/v1/assets/upload \
  -F "file=@testdata/images/sample_slide.png")

echo "$UPLOAD_RESPONSE" | python3 -m json.tool

IMAGE_URL=$(echo "$UPLOAD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['image_url'])")
WIDTH=$(echo "$UPLOAD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['width'])")
HEIGHT=$(echo "$UPLOAD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['height'])")

echo ""
echo "✓ 图片上传成功!"
echo "  - URL: $IMAGE_URL"
echo "  - 尺寸: ${WIDTH}x${HEIGHT}"
echo ""

# 2. 创建 page
echo "步骤 2/4: 创建 page..."
PAGE_RESPONSE=$(curl -s -X POST http://localhost:8080/v1/pages \
  -H "Content-Type: application/json" \
  -d "{\"image_url\":\"$IMAGE_URL\",\"width\":$WIDTH,\"height\":$HEIGHT}")

echo "$PAGE_RESPONSE" | python3 -m json.tool

PAGE_ID=$(echo "$PAGE_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['page_id'])")

echo ""
echo "✓ Page 创建成功!"
echo "  - Page ID: $PAGE_ID"
echo ""

# 3. 使用 Google Cloud Vision 分析
echo "步骤 3/4: 使用 Google Cloud Vision 进行 OCR 分析..."
echo "  (这可能需要几秒钟...)"
echo ""

ANALYZE_RESPONSE=$(curl -s -X POST http://localhost:8080/v1/pages/$PAGE_ID/analyze \
  -H "Content-Type: application/json" \
  -d '{"provider":"google","lang_hints":["zh-Hans","en"]}')

echo "$ANALYZE_RESPONSE" | python3 -m json.tool

echo ""
echo "✓ OCR 分析完成!"
echo ""

# 4. 获取候选框列表
echo "步骤 4/4: 获取识别的候选框..."
CANDIDATES_RESPONSE=$(curl -s http://localhost:8080/v1/pages/$PAGE_ID/candidates)

echo "$CANDIDATES_RESPONSE" | python3 -m json.tool

CANDIDATE_COUNT=$(echo "$CANDIDATES_RESPONSE" | python3 -c "import sys, json; print(len(json.load(sys.stdin)['candidates']))")

echo ""
echo "✓ 识别完成!"
echo "  - 识别到 $CANDIDATE_COUNT 个文本候选框"
echo ""

# 5. 显示识别的文本
echo "========================================="
echo "识别的文本内容:"
echo "========================================="
echo "$CANDIDATES_RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for i, cand in enumerate(data['candidates'], 1):
    print(f\"{i}. {cand['text']} (置信度: {cand['confidence']:.2f})\")
"

echo ""
echo "========================================="
echo "✓ 测试完成!"
echo "========================================="
echo ""
echo "说明:"
echo "  - 如果看到识别的文本内容,说明 Google Cloud Vision API 配置正确"
echo "  - 如果出现错误,请检查:"
echo "    1. GOOGLE_CREDENTIALS_JSON 是否正确配置"
echo "    2. Google Cloud Vision API 是否已启用"
echo "    3. 服务账号是否有正确的权限"
echo ""
echo "日志查看命令: make logs"
echo ""
