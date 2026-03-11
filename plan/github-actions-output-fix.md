# GitHub Actions 输出格式问题修复计划

**创建日期**: 2026-03-11
**状态**: 执行中
**问题**: GitHub Actions 输出格式错误导致工作流失败

---

## 问题概述

### 错误信息
```
Error: Unable to process file command 'output' successfully.
Error: Invalid format ' "success": true,'
```

### 错误位置
- 文件：`.github/workflows/email-extraction.yml`
- 步骤：`Generate outputs`（第108-137行）

### 根本原因
GitHub Actions 的 `$GITHUB_OUTPUT` 文件不支持直接写入多行 JSON 对象。当前代码尝试将包含换行符、引号、花括号的多行 JSON 直接写入输出文件，导致解析失败。

---

## 迭代开发流程

### 循环流程

```
计划 → 确认 → 编码 → 验证 → 修复 → 测试
  ↑                              ↓
  └────────── 循环直到满意 ────────┘
```

### 每次迭代检查点

- [ ] 代码能否运行？
- [ ] 功能是否正确？
- [ ] 日志是否详细？
- [ ] 错误是否有提示？
- [ ] 报告是否可读？

### 快速回滚机制

```bash
# 每个阶段独立提交
git add .
git commit -m "阶段X: XXX"

# 如果失败，回退到上一阶段
git reset --soft HEAD~1
```

---

## 执行计划

### 阶段0：问题分析与方案确认 ✅

**状态**: 已完成

**完成内容**：
- ✅ 分析错误原因
- ✅ 确定使用文件路径方案
- ✅ 创建详细修复计划（`C:\Users\zhang\.claude\plans\soft-dreaming-pike.md`）

**输出**：
- 问题根本原因分析文档
- 修复方案对比表
- 完整实施计划

---

### 阶段1：修复代码 ✅

**状态**: 已完成

**完成时间**: 2026-03-11

**修改文件**：
1. ✅ `.github/workflows/email-extraction.yml` - 修改 `Generate outputs` 步骤
2. ✅ `.github/workflows/email-extraction.yml` - 更新输出定义

**修改内容**：
```yaml
# 原代码（错误）
echo "summary=$SUMMARY" >> $GITHUB_OUTPUT
echo "detail=$RESULT" >> $GITHUB_OUTPUT

# 新代码（正确）
echo "$RESULT" > /tmp/extraction_result.json
echo "$SUMMARY" > /tmp/extraction_summary.json
echo "summary_file=/tmp/extraction_summary.json" >> $GITHUB_OUTPUT
echo "detail_file=/tmp/extraction_result.json" >> $GITHUB_OUTPUT
```

**提交信息**：
```
fix: 修复 GitHub Actions 输出格式错误（使用文件路径方案）

问题：
- GitHub Actions 无法解析多行 JSON 对象
- 直接将 JSON 写入 $GITHUB_OUTPUT 导致格式错误

修复：
- 使用文件路径方案替代直接输出 JSON
- 先将 JSON 写入临时文件，再输出文件路径
- 更新工作流输出定义

影响：
- 修改 .github/workflows/email-extraction.yml
- 添加验证脚本（scripts/verify_output_format.bat/sh）
- 添加 JSON 验证工具（scripts/validate_json_output.py）
```

---

### 阶段2：创建验证工具 ✅

**状态**: 已完成

**完成时间**: 2026-03-11

**创建文件**：
1. ✅ `scripts/verify_output_format.bat` - Windows 批处理验证脚本
2. ✅ `scripts/verify_output_format.sh` - Linux Shell 验证脚本
3. ✅ `scripts/validate_json_output.py` - Python JSON 验证工具

**功能说明**：
- **verify_output_format.bat**: Windows 环境快速验证文件路径方案
- **verify_output_format.sh**: Linux/GitHub Actions 环境验证
- **validate_json_output.py**: JSON 格式验证和方案对比

---

### 阶段3：本地验证 ⏳

**状态**: 进行中

**验证步骤**：

#### 步骤3.1：VSCode 语法检查
- [ ] 打开 `.github/workflows/email-extraction.yml`
- [ ] 检查 YAML 语法错误
- [ ] 确认缩进正确
- [ ] 确认引用的变量存在

#### 步骤3.2：运行验证工具

**Windows PowerShell**：
```powershell
# 1. 运行 Windows 批处理验证
scripts\verify_output_format.bat

# 2. 运行 Python JSON 验证
python scripts\validate_json_output.py
```

**预期结果**：
- ✅ 测试文件创建成功
- ✅ 文件路径方案验证通过

#### 步骤3.3：测试提取脚本

**Windows PowerShell**：
```powershell
# 测试提取脚本（小范围）
python scripts\extract_emails.py `
  --time-range-days 1 `
  --output-dir C:\temp\test_extraction
```

**预期结果**：
- ✅ 脚本成功执行
- ✅ 输出包含 `=== EXTRACTION_RESULT ===` 标记
- ✅ JSON 格式正确

---

### 阶段4：提交代码 ⏸️

**状态**: 待执行

**提交步骤**：

#### 步骤4.1：检查修改内容
```bash
# 查看修改状态
git status

# 查看具体修改
git diff .github/workflows/email-extraction.yml
```

#### 步骤4.2：暂存所有修改
```bash
# 暂存所有修改
git add .
```

#### 步骤4.3：创建提交
```bash
# 创建提交（使用详细提交信息）
git commit -m "fix: 修复 GitHub Actions 输出格式错误

问题：
- GitHub Actions 无法解析多行 JSON 对象
- 直接将 JSON 写入 \$GITHUB_OUTPUT 导致格式错误
- 错误信息: Invalid format ' \"success\": true,'

修复：
- 使用文件路径方案替代直接输出 JSON
- 先将 JSON 写入 /tmp/ 临时文件，再输出文件路径
- 更新工作流输出定义（summary_file, detail_file）

影响文件：
- .github/workflows/email-extraction.yml
- scripts/verify_output_format.bat (新建)
- scripts/verify_output_format.sh (新建)
- scripts/validate_json_output.py (新建)

测试：
- 本地验证通过
- JSON 格式验证通过
- 文件路径方案验证通过

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

#### 步骤4.4：推送到远程仓库
```bash
# 推送到 GitHub
git push origin master
```

**快速回滚**（如果需要）：
```bash
# 如果推送后发现问题，回退到上一版本
git reset --soft HEAD~1
# 重新修改后再次提交
```

---

### 阶段5：GitHub 验证 ⏸️

**状态**: 待执行

**验证步骤**：

#### 步骤5.1：检查 Actions 日志
1. 打开 GitHub 仓库页面
2. 点击 **Actions** 标签
3. 查看最新的工作流运行记录
4. 检查 `Generate outputs` 步骤是否成功

**预期结果**：
- ✅ `Generate outputs` 步骤成功完成
- ✅ 无 "Unable to process file command 'output'" 错误
- ✅ 输出显示 "摘要文件: /tmp/extraction_summary.json"

#### 步骤5.2：验证输出文件
1. 检查 Artifacts 是否上传成功
2. 下载 Artifacts 并查看内容
3. 验证 JSON 文件格式正确

**预期结果**：
- ✅ Artifacts 包含 `extraction_summary.json` 和 `extraction_result.json`
- ✅ JSON 文件可以正常打开和解析

#### 步骤5.3：测试手动触发
1. 在 GitHub 网页界面手动触发工作流
2. 选择不同的时间范围参数
3. 查看执行结果

**预期结果**：
- ✅ 工作流成功执行
- ✅ 输出文件正确生成

---

## 完成标准（Definition of Done）

### P0（必须完成）

- [ ] `.github/workflows/email-extraction.yml` 修复完成 ✅
- [ ] 验证脚本创建完成 ✅
- [ ] VSCode 语法检查通过 ⏳
- [ ] 本地验证测试通过 ⏳
- [ ] 代码已提交 ⏸️
- [ ] 代码已推送 ⏸️
- [ ] GitHub Actions 工作流无错误执行 ⏸️
- [ ] 输出文件正确生成 ⏸️

### P1（推荐完成）

- [ ] 钉钉通知测试通过
- [ ] Artifacts 上传测试通过
- [ ] 完整流程测试通过（触发→执行→清理→通知）

### P2（可选完成）

- [ ] 添加更多错误处理
- [ ] 添加单元测试
- [ ] 性能优化

---

## 风险点与缓解

### 风险1：文件路径在 Actions 环境中不可用

**风险等级**: 🟢 低

**缓解措施**:
- ✅ 使用 `/tmp/` 目录（GitHub Actions 保证可用）
- ✅ 在生成文件前不检查目录存在（`mkdir -p` 会自动创建）

### 风险2：修改后仍有格式错误

**风险等级**: 🟡 中

**缓解措施**:
- ✅ 已创建验证脚本
- ⏳ 本地验证后再推送
- ⏳ 如果失败，使用快速回滚机制

### 风险3：其他脚本依赖旧输出格式

**风险等级**: 🟢 低

**缓解措施**:
- ✅ 检查了 `Send DingTalk notification` 步骤，已更新为使用 `summary_file`
- ✅ 其他步骤不依赖这些输出

---

## 时间记录

| 阶段 | 开始时间 | 结束时间 | 耗时 | 状态 |
|------|---------|---------|------|------|
| 阶段0: 问题分析与方案确认 | 2026-03-11 | 2026-03-11 | 30分钟 | ✅ 完成 |
| 阶段1: 修复代码 | 2026-03-11 | 2026-03-11 | 15分钟 | ✅ 完成 |
| 阶段2: 创建验证工具 | 2026-03-11 | 2026-03-11 | 20分钟 | ✅ 完成 |
| 阶段3: 本地验证 | 2026-03-11 | - | - | ⏳ 进行中 |
| 阶段4: 提交代码 | - | - | - | ⏸️ 待执行 |
| 阶段5: GitHub 验证 | - | - | - | ⏸️ 待执行 |

---

## 后续步骤

完成本计划后：
1. 更新 `plan/github-actions-implementation-plan.md`
2. 记录修复结果和经验教训
3. 继续执行其他阶段

---

## 附录

### 验证脚本使用方法

**Windows 批处理**：
```powershell
# 双击运行或在 PowerShell 中执行
scripts\verify_output_format.bat
```

**Linux Shell**：
```bash
bash scripts/verify_output_format.sh
```

**Python 验证工具**：
```bash
python scripts/validate_json_output.py
```

### GitHub CLI 命令

```bash
# 查看工作流运行列表
gh run list

# 查看详细日志
gh run view RUN_ID --log

# 查看最新运行
gh run view --log
```

---

**最后更新**: 2026-03-11
**更新人**: Claude Sonnet 4.6
