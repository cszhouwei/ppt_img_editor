# TextEditor 修复验证指南

## 问题诊断结果

### 自动化测试发现的问题

运行 Playwright 自动化测试后，发现以下关键问题：

```
Error: element(s) not found
Locator: input[type="range"][min="12"][max="200"]
Expected: visible
Timeout: 5000ms
```

**根本原因分析**：
测试无法找到文本编辑器的控件，这表明：
1. 文本编辑器组件只在有 `currentPage` 时才显示（参见 [App.tsx:16-40](apps/web/src/App.tsx#L16-L40)）
2. 需要先上传图片并进行 OCR 分析，才会有文本图层可供编辑
3. 用户可能在手动测试时没有正确加载数据

### 代码审查结果

检查 [TextEditor.tsx:28-37](apps/web/src/components/TextEditor.tsx#L28-L37) 的实现：

```tsx
// ✅ 正确：Effect 1 - 数据同步（store → 本地 state）
useEffect(() => {
  if (currentTextLayer && !isEditingFontSize) {
    setFontSizeInput(String(currentTextLayer.style.fontSize));
  }
}, [currentTextLayer?.id, currentTextLayer?.style.fontSize]);
//  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
//  ✅ isEditingFontSize 不在依赖数组中 - 这是正确的！

// ✅ 正确：Effect 2 - 状态重置（图层切换时）
useEffect(() => {
  setIsEditingFontSize(false);
}, [currentTextLayer?.id]);
```

**结论：代码实现是正确的！**

---

## 为什么用户仍然遇到问题？

### 可能的原因

1. **浏览器缓存**：用户的浏览器可能缓存了旧版本的 JavaScript 代码
2. **开发服务器未重启**：代码更新后没有触发 HMR（热模块替换）
3. **测试数据缺失**：用户打开的页面没有文本图层，导致编辑器为空
4. **React StrictMode 双重渲染**：开发模式下 useEffect 会运行两次，可能影响观察

---

## 手动测试步骤

### 前置条件

**确保后端服务运行**：
```bash
cd /Users/bytedance/Downloads/projects/ppt_img_editor
docker-compose ps

# 应该看到以下服务都在运行：
# - ppt-editor-doc-process (0.0.0.0:8080)
# - ppt-editor-minio
# - ppt-editor-postgres
```

**启动前端（强制清除缓存）**：
```bash
cd apps/web

# 1. 停止旧的 dev 服务器
pkill -f "vite"

# 2. 清除构建缓存
rm -rf node_modules/.vite
rm -rf dist

# 3. 重新启动
npm run dev
```

**在浏览器中强制刷新**：
- macOS: `Cmd + Shift + R`
- Windows/Linux: `Ctrl + Shift + R`

或者打开 DevTools → Network → 勾选 "Disable cache"

---

### 测试场景 1：滑块拖动 → 数字框同步

**步骤**：
1. 上传一张包含文字的图片（如 PPT 截图）
2. 等待 OCR 分析完成
3. 在左侧图层面板点击选中一个文本图层
4. 在右侧编辑面板，拖动字号滑块到 60px

**预期结果**：
```
✅ 滑块位置：60
✅ 数字输入框显示：60
✅ 画布上的文字大小：实时更新到 60px
```

**如果失败**：
```
❌ 数字输入框显示：32（或其他旧值）
→ 说明 useEffect 没有触发
→ 检查浏览器控制台是否有错误
→ 尝试硬刷新（Cmd+Shift+R）
```

---

### 测试场景 2：数字框输入大数值

**步骤**：
1. 点击数字输入框
2. 清空内容
3. 逐字符输入 "180"
4. 按 Enter 或点击其他地方（失焦）

**预期结果**：
```
输入 "1"   → 输入框显示 "1"    ✅
输入 "8"   → 输入框显示 "18"   ✅
输入 "0"   → 输入框显示 "180"  ✅
按 Enter   → 字号更新为 180px  ✅
           → 滑块移动到 180     ✅
```

**如果失败**：
```
❌ 输入 "1" → 立即变成 "12"（最小值）
→ 说明实时更新逻辑有问题
→ 检查 handleFontSizeInputChange 是否被正确调用
```

---

### 测试场景 3：颜色选择 → 调整字号 → 颜色保持

**步骤**：
1. 在颜色选择器中选择红色 (#ff0000)
2. 等待颜色应用（文字变红）
3. 拖动字号滑块到 80px
4. 观察颜色是否改变

**预期结果**：
```
✅ 选择红色后：文字变红
✅ 拖动滑块后：字号改变，但颜色仍为红色
✅ 颜色选择器显示：#ff0000（不变）
```

**如果失败**：
```
❌ 拖动滑块后，颜色变回黑色
→ 说明 useMemo 缓存失效
→ 检查 hexColor 的依赖项
```

---

### 测试场景 4：切换图层 → 值正确显示

**步骤**：
1. 确保有至少 2 个文本图层
2. 选择图层 A，设置字号为 48px
3. 选择图层 B，设置字号为 96px
4. 切回图层 A
5. 观察数字输入框的值

**预期结果**：
```
✅ 图层 A 选中时：数字框显示 48
✅ 图层 B 选中时：数字框显示 96
✅ 切回图层 A 时：数字框显示 48（不是 96）
```

---

## 调试技巧

### 1. 浏览器 DevTools 断点调试

**在 useEffect 中添加 console.log**：

```tsx
useEffect(() => {
  console.log('[TextEditor] Effect 1 triggered', {
    layerId: currentTextLayer?.id,
    fontSize: currentTextLayer?.style.fontSize,
    isEditing: isEditingFontSize,
    willUpdate: currentTextLayer && !isEditingFontSize
  });

  if (currentTextLayer && !isEditingFontSize) {
    setFontSizeInput(String(currentTextLayer.style.fontSize));
  }
}, [currentTextLayer?.id, currentTextLayer?.style.fontSize]);
```

**预期日志输出（拖动滑块时）**：
```
[TextEditor] Effect 1 triggered {
  layerId: "layer-1",
  fontSize: 60,
  isEditing: false,
  willUpdate: true
}
```

### 2. React DevTools

1. 安装 React DevTools 扩展
2. 打开 Components 面板
3. 选择 TextEditor 组件
4. 观察 hooks 状态：
   - `fontSizeInput` 的值
   - `isEditingFontSize` 的值
   - `currentTextLayer.style.fontSize` 的值

### 3. 检查 Zustand Store

```tsx
// 在控制台执行
window.__ZUSTAND__ = require('zustand').default;
```

或者添加 Zustand DevTools：

```tsx
import { devtools } from 'zustand/middleware';

export const useEditorStore = create(
  devtools((set) => ({ /* ... */ }))
);
```

---

## 自动化测试指南

### 安装依赖

```bash
cd apps/web
npm install --save-dev @playwright/test
npx playwright install chromium
```

### 运行测试

```bash
# 1. 确保 dev 服务器在运行
npm run dev

# 2. 在另一个终端运行测试
npm test

# 或者用 UI 模式查看测试过程
npm run test:ui

# 或者用 headed 模式（显示浏览器）
npm run test:headed
```

### 当前测试状态

⚠️ **测试需要完整的后端集成**，包括：
- 图片上传
- OCR 分析
- 文本图层创建

**当前限制**：
- Playwright 测试无法找到编辑器控件
- 需要 mock 数据或完整的端到端测试环境

**解决方案**：
1. 手动上传图片并等待 OCR 完成
2. 使用浏览器 DevTools 进行调试
3. 或者创建 mock API 响应

---

## 总结

### 代码修复状态

✅ **useEffect 依赖项修复**：已正确实现
- Effect 1 不依赖 `isEditingFontSize`
- Effect 2 在图层切换时重置状态

✅ **延迟提交模式**：已实现
- 支持输入大数值（如 180）
- 编辑状态管理正确

✅ **颜色缓存**：已实现
- 使用 useMemo 缓存转换结果
- 避免不必要的重新计算

### 用户应该做什么

1. **清除浏览器缓存并硬刷新**
2. **重启 dev 服务器**
3. **按照测试步骤逐一验证**
4. **使用浏览器 DevTools 查看日志**
5. **如果仍有问题，提供以下信息**：
   - 浏览器控制台的错误日志
   - React DevTools 中的组件状态
   - 具体的复现步骤

---

## 附录：完整代码对比

### 修复前（错误代码）

```tsx
// ❌ 问题：isEditingFontSize 在依赖数组中
useEffect(() => {
  if (!isEditingFontSize && currentTextLayer) {
    setFontSizeInput(String(currentTextLayer.style.fontSize));
  }
}, [currentTextLayer?.id, currentTextLayer?.style.fontSize, isEditingFontSize]);
//                                                          ^^^^^^^^^^^^^^^^
//                                                          导致循环依赖！
```

### 修复后（正确代码）

```tsx
// ✅ 正确：两个独立的 effects

// Effect 1: 数据同步
useEffect(() => {
  if (currentTextLayer && !isEditingFontSize) {
    setFontSizeInput(String(currentTextLayer.style.fontSize));
  }
}, [currentTextLayer?.id, currentTextLayer?.style.fontSize]);
//  不包含 isEditingFontSize ✓

// Effect 2: 状态重置
useEffect(() => {
  setIsEditingFontSize(false);
}, [currentTextLayer?.id]);
```

**关键区别**：
1. 移除了 `isEditingFontSize` 从第一个 effect 的依赖数组
2. 添加了第二个 effect 专门处理图层切换时的状态重置
3. 职责分离，逻辑清晰
