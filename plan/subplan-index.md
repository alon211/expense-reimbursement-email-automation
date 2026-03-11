# 报销邮件自动化服务 - 混合架构改造计划索引

**最后更新**: 2026-03-11

本文档提供三个独立子计划的导航和执行顺序说明。

---

## 📑 子计划列表

### 1. [子计划1：本地Docker化与邮箱提取验证](./subplan-1-local-docker.md)

**目标**: 实现本地Docker容器化部署，验证核心提取功能

**预计工期**: 3-4天

**主要交付物**:
- Dockerfile
- docker-compose.yml
- .dockerignore
- .entrypoint.sh
- 部署文档

**状态**: ✅ 阶段1已完成（文件创建），待测试验证

---

### 2. [子计划2：GitHub Actions自动化执行（主要模式）](./subplan-2-github-actions.md)

**目标**: 将核心提取逻辑改造为GitHub Actions工作流，实现远程触发执行

**预计工期**: 5-7天

**主要交付物**:
- scripts/extract_emails.py（独立提取脚本）
- .github/workflows/email-extraction.yml（工作流文件）
- core/github_client.py（GitHub API客户端）
- scripts/trigger_workflow.py（触发脚本）
- 钉钉通知集成

**状态**: ❌ 未开始

---

### 3. [子计划3：本地Docker Web UI控制端](./subplan-3-web-ui.md)

**目标**: 创建可视化的Web管理界面，支持配置管理、远程触发、结果查看

**预计工期**: 7-10天

**主要交付物**:
- web_backend/（FastAPI后端）
- web_frontend/（Vue.js前端）
- Dockerfile.backend 和 Dockerfile.frontend
- nginx.conf（反向代理）
- docker-compose.yml（多容器编排）

**状态**: ❌ 未开始

---

## 🚀 执行顺序（已更新）

根据用户需求，跳过本地Docker部署，直接执行GitHub Actions：

```
阶段1: 本地功能测试与验证（优先）⚡
  ├─ 步骤1: ⏳ 本地环境准备
  ├─ 步骤2: ⏳ 附件重命名功能测试
  ├─ 步骤3: ⏳ 本地提取功能验证
  └─ 步骤4: ⏳ 提取结果验证

阶段2: GitHub Actions集成
  ├─ 步骤1: ⏳ 核心逻辑提取（独立脚本）
  ├─ 步骤2: ⏳ GitHub Actions工作流配置
  └─ 步骤3: ⏳ API触发和结果返回

阶段3: 本地Web UI开发（可选）
  ├─ 步骤1: ⏳ 后端API开发（FastAPI）
  ├─ 步骤2: ⏳ 前端界面开发（Vue.js）
  └─ 步骤3: ⏳ 本地服务部署
```

---

## 📊 进度追踪（已更新）

| 子计划 | 进度 | 完成度 | 状态 | 说明 |
|--------|------|--------|------|------|
| **计划1: 本地功能测试** | **0/4** | **0%** | 🔴 **下一步** | **为GitHub Actions做准备** |
| 计划2: GitHub Actions | 0/3 | 0% | ⚪ 待执行 | 核心功能 |
| 计划3: Web UI控制端 | 0/4 | 0% | ⚪ 待执行 | 可选功能 |
| **总体进度** | **0/11** | **0%** | 🔴 **开始** | 从本地测试开始 |

---

## 🎯 里程碑（已调整）

### 里程碑1：GitHub Actions集成完成 ⚡

**目标**: 可通过API触发远程提取，直接在GitHub运行

**验收标准**:
- [ ] 独立提取脚本可用
- [ ] GitHub Actions工作流可触发
- [ ] API返回JSON结果
- [ ] 钉钉通知正常发送
- [ ] 完整流程测试通过

**预计完成时间**: 第1-2周

**优先级**: 🔴 **最高（核心功能）**

---

### 里程碑2：本地Web UI（可选）

**目标**: 可视化界面，配置管理和触发

**验收标准**:
- [ ] FastAPI后端启动
- [ ] Vue.js前端可访问
- [ ] 配置管理功能可用
- [ ] 远程触发功能可用

**预计完成时间**: 第3-4周

**优先级**: 🟡 中等（提升用户体验）

---

### ~~里程碑3：本地Docker化~~

**状态**: ❌ **已跳过**

**原因**: 用户选择直接上传GitHub运行，不需要本地容器化

---

## 📝 快速开始（已调整）

### 立即开始：GitHub Actions集成 ⚡

**阶段0: 附件重命名功能** 🆕
```bash
# 1. 修改 core/email_extractor.py 添加文件重命名逻辑
# 2. 创建 tests/test_attachment_rename.py 测试文件重命名
# 3. 运行测试验证重命名功能
```

**阶段1: GitHub Actions集成**
```bash
# 步骤1: 配置GitHub Secrets
# 在GitHub仓库设置中添加：
# - IMAP_HOST
# - IMAP_USER
# - IMAP_PASS
# - DINGTALK_WEBHOOK（可选）
# - DINGTALK_SECRET（可选）

# 步骤2: 创建独立提取脚本
# 创建 scripts/extract_emails.py

# 步骤3: 创建GitHub Actions工作流
# 创建 .github/workflows/email-extraction.yml

# 步骤4: 测试触发
# gh workflow run email-extraction.yml
```

详细步骤请参考：[子计划2：GitHub Actions](./subplan-2-github-actions.md)

---

## 🆕 重要功能：附件重命名

### 需求背景
当多个邮件的附件文件名相同时（如多个邮件都有 `invoice.pdf`），后面的会覆盖前面的，导致数据丢失。

### 解决方案
**重命名策略**: 序号递增
- `invoice.pdf` → `invoice_1.pdf`（第2个）
- `invoice.pdf` → `invoice_2.pdf`（第3个）

**重命名时机**: 仅冲突时重命名
- 保留原始文件名（如果无冲突）
- 仅在检测到文件已存在时才添加序号

**应用范围**:
- ✅ 附件文件（PDF、图片等）
- ✅ 压缩包文件（zip、rar等）
- ❌ 压缩包内的文件（保持原样）

### 实现位置
- **代码文件**: [core/email_extractor.py](../core/email_extractor.py)
- **测试文件**: [tests/test_attachment_rename.py](../tests/test_attachment_rename.py)
- **详细说明**: [子计划2 - 阶段0](./subplan-2-github-actions.md#阶段0附件重命名功能05天)

---

## ⏸️ 暂停说明

当前状态：**等待用户确认后再继续执行**

**已完成**:
- ✅ 子计划1的文件创建（Dockerfile、docker-compose.yml等）
- ✅ 三个子计划文档编写完成

**待执行**:
- ⏳ 子计划1的阶段2：本地容器化测试
- ⏳ 子计划2：GitHub Actions集成
- ⏳ 子计划3：Web UI开发

**下一步**:
请您确认：
1. 是否继续执行子计划1的测试阶段？
2. 是否需要调整计划内容？
3. 还是有其他优先级更高的任务？

---

## 📞 联系方式

如有疑问或需要调整计划，请随时告知。

---

**相关文档**:
- [主计划文件](./bubbly-booping-rossum.md)
- [功能完成状态](./feature-status.md)
- [开发路线图](./development-roadmap.md)
