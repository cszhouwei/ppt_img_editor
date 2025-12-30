# 文档目录

本目录包含项目的所有文档,按照功能和用途分类组织。

## 📂 目录结构

```
docs/
├── README.md                      # 本文件 - 文档导航
├── ARCHITECTURE.md                # 系统架构文档
├── MAINTENANCE_SUMMARY.md         # 维护总结
│
├── planning/                      # 项目规划文档
│   ├── PRD-PPT截图文字可编辑化-MVP.md
│   ├── TechSpec-PPT截图文字可编辑化-MVP.md
│   └── Codex执行计划与任务分解-PPT截图文字可编辑化-MVP.md
│
├── guides/                        # 使用指南
│   ├── 开发流程指南.md
│   ├── 验收指引.md
│   ├── OCR-Provider-切换指南.md
│   ├── Google-OCR-配置指南.md
│   └── TextEditor修复验证指南.md
│
├── fixes/                         # Bug 修复说明
│   ├── selectedLayer同步修复说明.md
│   ├── Docker网络访问修复说明.md
│   ├── Patch生成修复说明.md
│   ├── 导出PNG修复说明.md
│   ├── 导出功能完整修复说明.md
│   ├── 输入框Bug修复说明.md
│   └── 文本编辑器最终修复说明.md
│
└── technical/                     # 技术优化说明
    ├── DetectedBreak优化说明.md
    ├── 字体大小估算优化说明.md
    ├── 字号编辑器改进说明.md
    ├── 实时编辑功能说明.md
    ├── 文字颜色估计优化说明.md
    └── 查看颜色估计日志.md
```

---

## 📖 核心文档

### [ARCHITECTURE.md](ARCHITECTURE.md)
**系统架构文档** - 深入了解系统设计

- 总体架构和组件关系
- 前后端技术栈详解
- 数据流和 API 设计
- 关键技术决策说明
- 性能优化和扩展性
- Docker 部署架构

**适合阅读对象**: 技术负责人、新加入的开发者、需要了解系统全貌的人员

### [MAINTENANCE_SUMMARY.md](MAINTENANCE_SUMMARY.md)
**维护总结文档** - 项目当前状态和未来规划

- 项目当前状态评估
- 已完成的功能和优化
- 已知问题和技术债务
- 短中长期维护建议
- 依赖管理和备份策略
- 项目成熟度评分

**适合阅读对象**: 项目经理、维护人员、需要评估项目状态的人员

---

## 📋 规划文档 (planning/)

### [PRD-PPT截图文字可编辑化-MVP.md](planning/PRD-PPT截图文字可编辑化-MVP.md)
**产品需求文档** - 了解产品背景和目标

- 产品背景和问题陈述
- 目标用户和使用场景
- 核心功能需求
- 非功能性需求
- MVP 范围定义

**适合阅读对象**: 产品经理、业务方、新团队成员

### [TechSpec-PPT截图文字可编辑化-MVP.md](planning/TechSpec-PPT截图文字可编辑化-MVP.md)
**技术规格说明** - 技术方案和实现细节

- 技术架构设计
- 数据库模型设计
- API 接口设计
- 核心算法说明
- 技术选型理由

**适合阅读对象**: 架构师、后端开发、前端开发

### [Codex执行计划与任务分解-PPT截图文字可编辑化-MVP.md](planning/Codex执行计划与任务分解-PPT截图文字可编辑化-MVP.md)
**执行计划** - 开发任务分解和时间线

- Milestone 里程碑划分
- 详细任务分解
- 依赖关系分析
- 验收标准 (DoD)

**适合阅读对象**: 项目经理、Scrum Master、开发团队

---

## 📚 使用指南 (guides/)

### [开发流程指南.md](guides/开发流程指南.md)
**日常开发流程** - 开发者必读

- 环境搭建步骤
- 本地开发流程
- 调试技巧
- 常见问题解决
- Git 工作流

**适合阅读对象**: 所有开发者

### [验收指引.md](guides/验收指引.md)
**功能验收清单** - QA 测试指南

- 完整的功能测试步骤
- 预期结果说明
- 边界条件测试
- 性能验收标准

**适合阅读对象**: QA 测试人员、项目验收人员

### [OCR-Provider-切换指南.md](guides/OCR-Provider-切换指南.md)
**OCR 服务切换** - 配置不同的 OCR 提供商

- Mock/Azure/Google 切换方法
- 环境变量配置
- 各提供商特点对比
- 故障排查

**适合阅读对象**: 运维人员、后端开发

### [Google-OCR-配置指南.md](guides/Google-OCR-配置指南.md)
**Google Cloud Vision 配置** - 详细配置步骤

- Google Cloud 项目创建
- Vision API 启用
- 服务账号配置
- 认证方式设置

**适合阅读对象**: 运维人员、需要配置 OCR 的开发者

### [TextEditor修复验证指南.md](guides/TextEditor修复验证指南.md)
**文本编辑器验证** - 测试文本编辑功能

- 编辑器功能测试步骤
- 验证要点
- 回归测试清单

**适合阅读对象**: QA 测试人员、前端开发

---

## 🔧 修复说明 (fixes/)

### [selectedLayer同步修复说明.md](fixes/selectedLayer同步修复说明.md)
**状态管理修复** - Zustand store 同步问题

- **问题**: 编辑控件不显示当前值
- **原因**: selectedLayer 和 layers 不同步
- **解决**: updateLayer 同时更新两个引用

### [Docker网络访问修复说明.md](fixes/Docker网络访问修复说明.md)
**容器网络修复** - Docker 容器间通信问题

- **问题**: 容器内无法访问 MinIO
- **原因**: localhost 指向容器自己
- **解决**: URL 替换为服务名 (minio:9000)

### [Patch生成修复说明.md](fixes/Patch生成修复说明.md)
**Patch 生成问题** - 背景修复失败排查

- Patch 生成失败原因分析
- 图像处理参数调优
- 调试方法和日志

### [导出PNG修复说明.md](fixes/导出PNG修复说明.md)
**导出功能修复 (第一版)** - Docker 网络和异步问题

- Docker 网络 URL 转换
- async/await 嵌套错误修复

### [导出功能完整修复说明.md](fixes/导出功能完整修复说明.md)
**导出功能修复 (完整版)** - CORS 和下载问题

- 添加代理端点避免 CORS
- Blob URL 下载实现
- 自动保存确保数据一致

### [输入框Bug修复说明.md](fixes/输入框Bug修复说明.md)
**输入框焦点问题** - 字号输入框失焦 Bug

- 输入框状态管理
- 焦点事件处理
- 实时同步实现

### [文本编辑器最终修复说明.md](fixes/文本编辑器最终修复说明.md)
**文本编辑器综合修复** - 所有编辑器问题汇总

- 实时编辑实现
- 状态同步修复
- 控件独立工作

**适合阅读对象**: 遇到相同问题的开发者、维护人员

---

## 💡 技术优化 (technical/)

### [DetectedBreak优化说明.md](technical/DetectedBreak优化说明.md)
**中文文本布局优化** - OCR 换行处理

- DetectedBreak 机制说明
- 中文文本特殊处理
- 布局优化算法

### [字体大小估算优化说明.md](technical/字体大小估算优化说明.md)
**字号估算算法** - 提升字号预测准确度

- 基于边界框高度估算
- 系数调优 (0.7)
- 支持 12-500px 范围

### [字号编辑器改进说明.md](technical/字号编辑器改进说明.md)
**字号控件改进** - 滑块和输入框独立工作

- 双控件独立事件处理
- 实时同步机制
- 用户体验优化

### [实时编辑功能说明.md](technical/实时编辑功能说明.md)
**实时编辑实现** - 移除"应用更改"按钮

- 事件驱动更新
- updateLayer 直接调用
- 性能优化考虑

### [文字颜色估计优化说明.md](technical/文字颜色估计优化说明.md)
**颜色估计算法** - 多种颜色提取方法

- kmeans 聚类
- median 中位数
- edge 边缘检测
- mean 平均值

### [查看颜色估计日志.md](technical/查看颜色估计日志.md)
**调试颜色估计** - 查看颜色估计过程

- 日志查看方法
- 调试信息解读
- 参数调优指导

**适合阅读对象**: 需要理解技术实现细节的开发者、算法优化人员

---

## 🚀 快速导航

### 我是新手,从哪里开始?

1. **了解产品**: 阅读 [PRD](planning/PRD-PPT截图文字可编辑化-MVP.md)
2. **搭建环境**: 参考 [开发流程指南](guides/开发流程指南.md)
3. **理解架构**: 阅读 [ARCHITECTURE.md](ARCHITECTURE.md)
4. **开始开发**: 查看 [执行计划](planning/Codex执行计划与任务分解-PPT截图文字可编辑化-MVP.md)

### 我遇到了 Bug,怎么办?

1. 查看 [fixes/](fixes/) 目录下是否有类似问题的修复说明
2. 查阅 [开发流程指南](guides/开发流程指南.md) 的调试章节
3. 查看 [ARCHITECTURE.md](ARCHITECTURE.md) 了解相关组件

### 我需要配置 OCR 服务

1. 阅读 [OCR-Provider-切换指南](guides/OCR-Provider-切换指南.md)
2. 如果使用 Google: [Google-OCR-配置指南](guides/Google-OCR-配置指南.md)

### 我需要了解技术实现

1. 查看 [technical/](technical/) 目录下的技术优化说明
2. 阅读 [ARCHITECTURE.md](ARCHITECTURE.md) 的技术决策章节

### 我需要做项目验收

1. 使用 [验收指引](guides/验收指引.md) 进行功能测试
2. 参考 [TextEditor修复验证指南](guides/TextEditor修复验证指南.md)

### 我需要评估项目状态

1. 阅读 [MAINTENANCE_SUMMARY.md](MAINTENANCE_SUMMARY.md)
2. 查看项目根目录的 [CHANGELOG.md](../CHANGELOG.md)

---

## 📝 文档更新指南

### 何时添加新文档?

- **修复 Bug**: 在 `fixes/` 下添加修复说明
- **技术优化**: 在 `technical/` 下添加优化说明
- **新功能指南**: 在 `guides/` 下添加使用指南
- **架构变更**: 更新 `ARCHITECTURE.md`

### 文档命名规范

- 使用描述性名称
- Bug 修复: `[组件名]修复说明.md`
- 技术优化: `[功能名]优化说明.md`
- 使用指南: `[功能名]指南.md`

### 文档模板

每个技术文档应包含:
1. **问题描述**: 遇到了什么问题
2. **根本原因**: 为什么会出现这个问题
3. **解决方案**: 如何解决的
4. **验证方法**: 如何验证修复有效
5. **相关代码**: 涉及的文件和行号

---

## 🔗 相关链接

- [项目 README](../README.md)
- [变更日志](../CHANGELOG.md)
- [贡献指南](../CONTRIBUTING.md)
- [GitHub Issues](../../issues)

---

**最后更新**: 2024-12-30

**维护者**: Development Team
