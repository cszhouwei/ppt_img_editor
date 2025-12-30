# 文字空格优化：使用 Google Cloud Vision DetectedBreak

## 问题背景

原有实现在提取 OCR 文字时，简单地在所有单词之间插入空格：

```python
# 旧实现
def _extract_text_from_paragraph(self, paragraph) -> str:
    text_parts = []
    for word in paragraph.words:
        word_text = "".join([symbol.text for symbol in word.symbols])
        text_parts.append(word_text)
    return " ".join(text_parts)  # ❌ 所有单词间都加空格
```

这导致以下问题：
- ✅ 英文正常：`"Hello" + "World"` → `"Hello World"`
- ❌ 中文错误：`"你" + "好"` → `"你 好"` (应该是 `"你好"`)
- ❌ 中英混合：`"Python" + "编程"` → `"Python 编程"` (可能有多余空格)

## 解决方案：使用 DetectedBreak

Google Cloud Vision API 在每个字符（Symbol）的 `property.detected_break` 中提供了精确的分隔信息。

### DetectedBreak 类型

| Break Type | 值 | 说明 | 是否添加空格 |
|-----------|---|------|------------|
| `UNKNOWN` | 0 | 未知类型 | ❌ 否 |
| `SPACE` | 1 | 常规空格 | ✅ 是 |
| `SURE_SPACE` | 2 | 确定的空格（较宽） | ✅ 是 |
| `EOL_SURE_SPACE` | 3 | 行尾换行造成的空格 | ✅ 是 |
| `HYPHEN` | 4 | 连字符（行尾） | ❌ 否 |
| `LINE_BREAK` | 5 | 段落结束的换行 | ❌ 否 |

### 新实现

```python
def _extract_text_from_paragraph(self, paragraph) -> str:
    """使用 DetectedBreak 智能处理空格"""
    text_parts = []

    for word in paragraph.words:
        word_chars = []

        for symbol in word.symbols:
            # 添加字符本身
            word_chars.append(symbol.text)

            # 检查字符后是否有 break
            if hasattr(symbol, 'property') and symbol.property:
                detected_break = symbol.property.detected_break

                if detected_break:
                    break_type = detected_break.type

                    # 只在明确需要空格的类型中添加
                    if break_type.name in ['SPACE', 'SURE_SPACE', 'EOL_SURE_SPACE']:
                        word_chars.append(' ')

        text_parts.append("".join(word_chars))

    # 直接拼接，空格信息已在 DetectedBreak 中处理
    return "".join(text_parts)
```

## 优化效果

### 场景 1：纯中文
- **旧实现**: `"你 好 世 界"` ❌
- **新实现**: `"你好世界"` ✅

### 场景 2：纯英文
- **旧实现**: `"Hello World"` ✅
- **新实现**: `"Hello World"` ✅

### 场景 3：中英混合
- **旧实现**: `"使 用 Python 编 程"` ❌
- **新实现**: `"使用 Python 编程"` ✅

### 场景 4：带标点
- **旧实现**: `"你 好 ， 世 界 ！"` ❌
- **新实现**: `"你好，世界！"` ✅

## 测试方法

1. 重启服务：
   ```bash
   make restart
   ```

2. 上传包含中文、英文、中英混合文字的图片

3. 检查 OCR 结果中的文字是否没有多余空格

4. 查看调试日志（如果启用了 DEBUG 级别）：
   ```bash
   docker-compose logs doc_process | grep "Symbol.*break type"
   ```

## 注意事项

1. **只影响 Google Cloud Vision Provider**
   Azure OCR Provider 使用不同的 API，需要单独优化

2. **调试日志**
   默认日志级别为 INFO，看不到 Symbol 级别的详细日志
   如需调试，可临时设置 `LOG_LEVEL=DEBUG`

3. **向后兼容**
   此优化不影响已有数据，只影响新识别的文字

## 参考资料

- [Google Cloud Vision API - DetectedBreak Structure](https://github.com/googleapis/googleapis/blob/master/google/cloud/vision/v1/text_annotation.proto)
- [TextAnnotation.DetectedBreak.BreakType Documentation](http://googleapis.github.io/googleapis/java/grpc-google-cloud-vision-v1/0.1.5/apidocs/com/google/cloud/vision/v1/TextAnnotation.DetectedBreak.BreakType.html)
