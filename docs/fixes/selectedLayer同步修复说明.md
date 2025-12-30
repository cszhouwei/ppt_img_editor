# selectedLayer 同步修复说明

## 问题描述

**用户反馈**：
> 右侧文本编辑区，所有的控件均有问题，表现为：变化在左侧画布区域会实时生效，但是编辑控件本身的数值或者内容都还是默认值

**症状**：
- ✅ 拖动字号滑块 → 画布上的文字大小实时改变
- ❌ 拖动字号滑块 → 右侧数字输入框仍显示旧值
- ✅ 选择颜色 → 画布上的文字颜色实时改变
- ❌ 调整字号后 → 颜色选择器显示值不更新

---

## 根本原因

### 问题定位

在 [useEditorStore.ts:87-92](apps/web/src/store/useEditorStore.ts#L87-L92) 中，`updateLayer` 函数的实现：

```tsx
// ❌ 修复前：只更新 layers 数组
updateLayer: (layerId, updates) =>
  set((state) => ({
    layers: state.layers.map((layer) =>
      layer.id === layerId ? { ...layer, ...updates } as Layer : layer
    ),
  })),
```

**问题分析**：

1. `updateLayer` 只更新了 `state.layers` 数组
2. **没有同步更新 `state.selectedLayer`**
3. 导致两个状态不一致：

```
修改字号 48 → 60：

state.layers[0] = {
  id: "layer-1",
  style: { fontSize: 60 },  ✅ 已更新
  ...
}

state.selectedLayer = {
  id: "layer-1",
  style: { fontSize: 48 },  ❌ 未更新（旧的引用）
  ...
}
```

### 为什么画布生效但编辑器不生效？

**画布渲染逻辑**（EditorCanvas.tsx）：
```tsx
// 画布从 layers 数组读取数据
const layers = useEditorStore((state) => state.layers);

// ✅ layers 数组已更新 → 画布重新渲染 → 显示新字号
```

**编辑器渲染逻辑**（TextEditor.tsx）：
```tsx
// 编辑器从 selectedLayer 读取数据
const selectedLayer = useEditorStore((state) => state.selectedLayer);

// ❌ selectedLayer 引用未变化 → 组件不重新渲染 → 显示旧值
```

### Zustand 的状态订阅机制

Zustand 使用**浅比较（shallow equality）**来判断状态是否改变：

```tsx
const selectedLayer = useEditorStore((state) => state.selectedLayer);
//                                             ^^^^^^^^^^^^^^^^^^^
// 只有当 selectedLayer 的引用改变时，组件才重新渲染
```

因为 `updateLayer` 没有创建新的 `selectedLayer` 引用，所以：
- `state.selectedLayer === oldState.selectedLayer`  → `true`
- Zustand 认为状态未改变
- 组件不触发重新渲染
- 显示的值仍然是旧值

---

## 修复方案

### 代码修改

修改 [useEditorStore.ts:87-103](apps/web/src/store/useEditorStore.ts#L87-L103)：

```tsx
// ✅ 修复后：同时更新 layers 和 selectedLayer
updateLayer: (layerId, updates) =>
  set((state) => {
    // 1. 更新 layers 数组
    const updatedLayers = state.layers.map((layer) =>
      layer.id === layerId ? { ...layer, ...updates } as Layer : layer
    );

    // 2. 同步更新 selectedLayer
    const updatedSelectedLayer =
      state.selectedLayer?.id === layerId
        ? updatedLayers.find((layer) => layer.id === layerId) || state.selectedLayer
        : state.selectedLayer;

    // 3. 同时返回两个更新
    return {
      layers: updatedLayers,
      selectedLayer: updatedSelectedLayer,  // ✅ 新的引用
    };
  }),
```

### 修复逻辑

1. **创建新的 layers 数组**：`updatedLayers`
2. **检查是否需要更新 selectedLayer**：
   - 如果当前选中的图层就是被修改的图层 → 从新数组中找到对应图层
   - 否则 → 保持原 selectedLayer 不变
3. **返回两个新引用**：
   - `layers: updatedLayers`（新数组）
   - `selectedLayer: updatedSelectedLayer`（新对象）

### 为什么这样能解决问题？

修复后的数据流：

```
修改字号 48 → 60：

1. updateLayer 被调用
   ↓
2. 创建新的 layers 数组（新引用）
   ↓
3. 从新数组中找到对应图层，赋值给 selectedLayer（新引用）
   ↓
4. set({ layers: new, selectedLayer: new })
   ↓
5. Zustand 检测到 selectedLayer 引用改变
   ↓
6. 通知所有订阅 selectedLayer 的组件重新渲染
   ↓
7. TextEditor 重新渲染，显示新值 ✅
```

---

## 测试验证

### 测试场景 1：字号滑块同步

**操作步骤**：
1. 选中一个文本图层
2. 拖动字号滑块从 32px → 60px

**预期结果**：
```
✅ 画布：文字大小变为 60px
✅ 滑块：位置移动到 60
✅ 数字框：显示 60
✅ 标签：显示 "字号: 60px"
```

### 测试场景 2：数字输入框

**操作步骤**：
1. 点击数字输入框
2. 输入 "180"
3. 按 Enter 或点击其他地方

**预期结果**：
```
✅ 画布：文字大小变为 180px
✅ 滑块：移动到 180 位置
✅ 数字框：显示 180
```

### 测试场景 3：颜色选择器

**操作步骤**：
1. 选择红色 (#ff0000)
2. 拖动字号滑块

**预期结果**：
```
✅ 画布：文字变红，字号改变
✅ 颜色选择器：仍显示 #ff0000
✅ 颜色标签：显示 #ff0000
```

### 测试场景 4：字重选择

**操作步骤**：
1. 选择 Bold (700)
2. 修改字号

**预期结果**：
```
✅ 下拉框：显示 Bold (700)
✅ 修改字号后：下拉框仍显示 Bold (700)
```

### 测试场景 5：文本内容

**操作步骤**：
1. 在 textarea 中输入 "Hello World"
2. 修改字号

**预期结果**：
```
✅ textarea：显示 "Hello World"
✅ 修改字号后：textarea 仍显示 "Hello World"
```

---

## 技术细节

### Zustand 的浅比较机制

```tsx
// Zustand 使用 Object.is() 比较引用
const selector = (state) => state.selectedLayer;

// 组件重新渲染的条件：
Object.is(newSelectedLayer, oldSelectedLayer) === false
```

### 深拷贝 vs 浅拷贝

```tsx
// ✅ 正确：创建新引用
const updatedLayer = { ...layer, ...updates };

// ❌ 错误：修改原对象（引用不变）
layer.style.fontSize = newSize;
```

### 为什么需要同时更新两个状态？

Zustand 的状态设计原则：
- **单一数据源（Single Source of Truth）**：`layers` 是主数据
- **派生状态（Derived State）**：`selectedLayer` 是 `layers` 的引用
- **状态一致性**：两者必须保持同步

如果只更新 `layers`：
```tsx
// ❌ 状态不一致
state.layers[0].style.fontSize = 60;      // 新值
state.selectedLayer.style.fontSize = 48;  // 旧值
```

如果同时更新：
```tsx
// ✅ 状态一致
state.layers[0].style.fontSize = 60;      // 新值
state.selectedLayer.style.fontSize = 60;  // 新值（同一个对象）
```

---

## 相关修复

这个修复解决了之前所有编辑器控件的同步问题：

1. ✅ **字号滑块** - [TextEditor.tsx:166-173](apps/web/src/components/TextEditor.tsx#L166-L173)
2. ✅ **字号数字框** - [TextEditor.tsx:174-185](apps/web/src/components/TextEditor.tsx#L174-L185)
3. ✅ **字重选择** - [TextEditor.tsx:188-198](apps/web/src/components/TextEditor.tsx#L188-L198)
4. ✅ **颜色选择器** - [TextEditor.tsx:200-210](apps/web/src/components/TextEditor.tsx#L200-L210)
5. ✅ **文本内容** - [TextEditor.tsx:154-161](apps/web/src/components/TextEditor.tsx#L154-L161)

所有控件都依赖 `currentTextLayer`，而 `currentTextLayer` 来自 `selectedLayer`。修复了 `selectedLayer` 的同步问题后，所有控件都能正常工作。

---

## 总结

### 问题核心

**状态同步失败**：`updateLayer` 只更新了 `layers` 数组，没有同步更新 `selectedLayer` 引用，导致组件无法感知状态变化。

### 修复核心

**同步更新两个状态**：在 `updateLayer` 中创建新的 `selectedLayer` 引用，确保 Zustand 能检测到变化并触发组件重新渲染。

### 影响范围

✅ 所有依赖 `selectedLayer` 的 UI 控件都得到修复
✅ 画布和编辑器的状态完全同步
✅ 实时编辑体验符合预期

### 验证方法

刷新浏览器后，测试所有编辑器控件，确保：
- 值在控件中正确显示
- 修改后立即更新显示
- 切换图层后显示正确的值
