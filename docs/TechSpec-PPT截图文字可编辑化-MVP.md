# 《PPT 截图文字可编辑化 MVP 技术方案（Tech Spec）》

## 1. 总体架构
### 1.1 组件划分
- **Web Editor（前端）**
  - 画布渲染：背景图层、patch 图层、文本图层
  - 候选框 overlay 与交互（hover/click）
  - 文本编辑 UI（输入、样式面板）
  - 导出合成（可选）
- **Doc Process Service（后端）**
  - OCR 调用适配层（Azure Read / Google Vision 二选一，封装统一输出）
  - OCR 结果归一化与候选框生成
  - patch 生成（纯色/渐变拟合 + OpenCV inpaint）
  - 资源存储与缓存
- **Storage**
  - 对象存储：原图、patch PNG、导出结果
  - KV/Cache：Redis（缓存 OCR/patch 结果）
  - DB：Postgres（项目元数据、任务状态）

### 1.2 数据流
1) upload → store original  
2) analyze → OCR → candidates JSON  
3) convert → generate patch → store patch → return patch URL + bbox  
4) editor renders layers → save project JSON → export  

## 2. 统一中间表示（IR）与数据结构
### 2.1 Candidate（OCR 候选）
```json
{
  "id": "c_001",
  "text": "Revenue +12%",
  "confidence": 0.93,
  "quad": [[120,80],[540,80],[540,144],[120,144]],
  "bbox": {"x":120,"y":80,"w":420,"h":64},
  "words": [
    {"text":"Revenue","conf":0.95,"quad":[...]}
  ],
  "angle_deg": -0.3
}
```

### 2.2 Layer（编辑器图层）
**TextLayer**
```json
{
  "id": "t_001",
  "kind": "text",
  "quad": [[...]],
  "text": "Revenue +12%",
  "style": {
    "fontFamily": "System",
    "fontSize": 32,
    "fontWeight": 600,
    "fill": "rgba(30,30,30,1)",
    "letterSpacing": 0,
    "lineHeight": 1.2
  },
  "source": {"candidate_id": "c_001"}
}
```

**PatchLayer**
```json
{
  "id": "p_001",
  "kind": "patch",
  "bbox": {"x":110,"y":72,"w":440,"h":84},
  "image_url": "https://.../patch_p_001.png",
  "source": {"candidate_id": "c_001"}
}
```

### 2.3 Project
```json
{
  "project_id": "proj_123",
  "page": {"image_url":"...","width":1920,"height":1080},
  "candidates_version": "v1",
  "layers": [ ... ]
}
```

## 3. OCR 方案（云 API + 统一适配）
### 3.1 Provider 抽象
统一接口：
- 输入：image_url / binary、lang_hints（可选）
- 输出：lines（含 words）、polygon/quad、confidence

实现两个 provider adapter：
- AzureReadAdapter
- GoogleVisionAdapter

> MVP 建议先只落一个 provider，另一个留 feature flag，避免双倍联调成本。

### 3.2 归一化与候选聚合
- 优先使用 provider 的 line 结构（若无则由 word 自行聚类成行）。
- 对每个 line：
  - text = words join（按 x 排序）
  - quad = line polygon；若只有 bbox 则构造 axis-aligned quad
  - angle_deg = quad 边方向估计
- 过滤规则：
  - 字符数太短（如 1 个字符）可仍保留，但默认不显示（可配置）
  - confidence < 0.3 直接丢弃（可配置）

## 4. patch 生成算法（核心）
目标：输出 ROI 级透明 PNG patch，用于覆盖原图文字区域并补齐背景。

### 4.1 ROI 与 mask 生成
- 输入：candidate.quad 或 bbox
- 计算 axis-aligned bbox（ROI），并做 padding（默认 8px，可配置）
- 将 quad rasterize 为二值 mask（文字区域=1）
- mask 膨胀（解决抗锯齿/描边/阴影）：
  - r_in = clamp(round(font_est/24), 1, 2)  （内吃边）
  - r_out = clamp(round(font_est/10), 3, 10)（外扩过渡带）
  - font_est：可用 bbox 高度近似
- 生成 ring 采样带：
  - ring = dilate(mask, r_out) - dilate(mask, r_in)

### 4.2 背景判定与拟合（优先纯色/渐变）
在 ROI 内，取 ring 像素作为背景样本：
- **纯色判定**：
  - 对 RGB 每通道方差/或整体方差 < 阈值（例如 12^2）→ 纯色
  - 背景色 = ring 像素中位数（鲁棒）
- **线性渐变（平面）拟合**：
  - 对每个通道拟合：I(x,y)=a·x+b·y+c（最小二乘）
  - 用残差（MAE）判断是否可接受（例如 MAE < 8）
- 若两者均不满足：进入降级模式（仅 inpaint）

生成一个 background_init 图：
- 若纯色/渐变成功：用模型填充 mask 区域
- 否则：用 ring 均值填充 mask 区域（给 inpaint 初值）

### 4.3 OpenCV inpaint（只修“边缘过渡带”）
为避免大面积 inpaint 造成糊块：
- edge_mask = dilate(mask, r_edge) - erode(mask, r_edge)
- r_edge 建议 3~6px（随字号变化）
- 对 edge_mask 调用 OpenCV inpaint：
  - 默认 Telea
  - 若 ROI 内梯度强（存在明显线条/边界），可切 NS
- 输出修复后的 ROI 图

### 4.4 生成透明 patch PNG
- patch 图尺寸 = ROI 尺寸
- RGB = 修复后的 ROI
- Alpha：
  - alpha = dilate(mask, r_out) 做基础不透明区域
  - 再对 alpha 做轻微高斯模糊（feather），边缘更自然
- ROI 外保持透明
- 上传 patch 到对象存储，返回 patch_url + ROI bbox

### 4.5 失败处理
- 任一阶段失败（解码、ROI 越界、inpaint 异常）：
  - 返回 error code
  - 前端仍可创建 text layer，但不创建 patch layer

## 5. 文本样式估计（MVP 最小）
MVP 不追求字体匹配，但建议做两项让体验明显提升：

1) **颜色估计（fill）**  
在原图 ROI 内取“文字像素”样本（mask 区域），做聚类/或取中位数（注意排除阴影：可用亮度阈值或仅取高饱和/高对比像素）。输出 rgba。

2) **字号估计（fontSize）**  
以 bbox 高度近似字号：fontSize ≈ bbox_h * 0.75（经验值，后续用数据校准）。  
同时允许用户在右侧面板手调。

## 6. API 设计（MVP）
### 6.1 Analyze
`POST /v1/pages/analyze`
- 请求
```json
{"image_url":"...","provider":"azure_read","lang_hints":["zh-Hans","en"]}
```
- 响应
```json
{"page_id":"page_123","width":1920,"height":1080,"candidates":[...]}
```

### 6.2 Generate Patch
`POST /v1/pages/{page_id}/patch`
- 请求
```json
{"candidate_id":"c_001","padding_px":8,"mode":"auto"}
```
- 响应
```json
{"patch":{"id":"p_001","bbox":{"x":110,"y":72,"w":440,"h":84},"image_url":"..."}}
```

### 6.3 Save Project / Load Project
- `PUT /v1/projects/{project_id}`：保存项目 JSON
- `GET /v1/projects/{project_id}`：加载项目 JSON

### 6.4 Export PNG（可选）
`POST /v1/projects/{project_id}/export/png`
- 返回导出文件 URL

## 7. 前端实现要点（与后端契约对齐）
1) **Overlay 渲染**
   - candidates 以 quad 多边形渲染（可用 SVG overlay 或 canvas overlay）
2) **Convert to Editable**
   - 选中 candidate → 调 patch 接口 → 成功后插入 patch layer + text layer
3) **图层渲染顺序**
   - 背景图（原图）
   - patch layers（按创建顺序）
   - text layers
4) **坐标系统**
   - 统一用原图像素坐标作为世界坐标；缩放只在视口变换层处理
5) **Undo/Redo**
   - Convert 操作需要原子化：一次操作同时新增 patch 与 text 两个 layer

## 8. 性能、缓存与幂等
- OCR 缓存 Key：`hash(image_bytes) + provider + lang_hints`
- patch 缓存 Key：`page_id + candidate_id + padding_px + mode + algo_version`
- patch 生成必须幂等：同 key 命中直接返回已生成 patch URL
- ROI 级处理避免全图计算；并发限制避免 CPU 打满

## 9. 观测与告警（MVP）
- 指标：ocr_latency、ocr_error_rate、patch_latency、patch_error_rate、export_latency
- 日志：按 request_id 串联 analyze/patch/save/export
- 采样保存少量失败样本（脱敏/仅内部）用于回归

## 10. 测试计划（MVP 必做）
1) 单元测试
- quad→mask rasterize
- ring/edge_mask 生成
- 纯色判定与渐变拟合残差计算
2) Golden Set 回归
- 20 张典型 PPT 截图（纯色/渐变/轻纹理/中英混排）
- 对每张预置 10 个 candidate，验证 patch 生成不崩溃且导出一致
3) E2E
- 导入→分析→点选→编辑→保存→加载→导出
