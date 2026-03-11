# 修复 extract_emails.py 参数和错误问题

**创建日期**: 2026-03-11
**状态**: 待执行
**优先级**: P0（紧急）

---

## 问题概述

### 问题1：Workflow 参数不生效 ❌

**现象**：
```
命令行: --time-range-days 1
实际执行: 解析时间范围：3 天（使用 JSON 配置）
```

**根本原因**：
`scripts/extract_emails.py` 脚本没有将命令行参数传递给核心逻辑

### 问题2：代码错误 ❌

**错误信息**：
```
AttributeError: 'Rule' object has no attribute 'get'
```

**错误位置**：
```python
# scripts/extract_emails.py 第 77 行
"rule_id": m.get("matched_rules", [{}])[0].get("rule_id")
```

**原因**：
- `m["matched_rules"]` 是 `Rule` 对象列表
- 不是字典列表，不能调用 `.get()` 方法

### 好消息 ✅
成功找到了 2 封匹配的邮件！说明规则配置和邮件匹配逻辑都是正常的。

---

## 修复方案

### 修复1：删除 Workflow 参数，完全使用 JSON 配置

**用户需求**：
> "把workflow启动的参数删除了，还是按json文件配置的来"

**修改文件**：`.github/workflows/email-extraction.yml`

**修改内容**：
```yaml
# 删除 inputs 配置
on:
  workflow_dispatch:
    # 删除 inputs 部分

  repository_dispatch:
    types: [trigger-extraction]
```

### 修复2：修复 extract_emails.py 的代码错误

**修改文件**：`scripts/extract_emails.py`

**修改内容**：
```python
# 第 71-81 行
"mails": [
    {
        "message_id": m.get("message_id"),
        "subject": m.get("subject"),
        "sender": m.get("sender"),
        "mail_date": m.get("date"),
        # 修复：Rule 对象使用 .rule_id 属性，不是 .get() 方法
        "rule_id": m.get("matched_rules", [None])[0].rule_id if m.get("matched_rules") else None,
        "rule_name": m.get("matched_rules", [None])[0].rule_name if m.get("matched_rules") else None
    }
    for m in matched_mails
],
```

### 修复3：移除无用的命令行参数

**修改文件**：`scripts/extract_emails.py`

**修改内容**：
```python
# 移除 --time-range-days 参数
# 移除 --rules-path 参数
# 只保留 --output-dir 参数

def main():
    parser = argparse.ArgumentParser(description='邮件提取脚本')
    parser.add_argument('--output-dir', default=None, help='输出目录（默认使用EXTRACT_ROOT_DIR）')
    args = parser.parse_args()

    # 设置输出目录
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = Path(EXTRACT_ROOT_DIR)

    # 时间范围从 JSON 配置读取，不再从命令行传入
```

---

## 执行步骤

### 阶段1：修复代码错误 ⏳

**文件**：`scripts/extract_emails.py`

**步骤1.1**：修复 Rule 对象访问
```python
# 修改第 76-77 行
# 原代码（错误）：
"rule_id": m.get("matched_rules", [{}])[0].get("rule_id") if m.get("matched_rules") else None,

# 新代码（正确）：
"rule_id": m.get("matched_rules", [None])[0].rule_id if m.get("matched_rules") else None,
```

**步骤1.2**：移除无用的命令行参数
```python
# 删除 --time-range-days 和 --rules-path 参数
# 这些参数实际上没有被使用
```

### 阶段2：简化 Workflow 配置 ⏸️

**文件**：`.github/workflows/email-extraction.yml`

**步骤2.1**：删除 inputs
```yaml
on:
  workflow_dispatch:
    # 完全删除 inputs 部分
  repository_dispatch:
    types: [trigger-extraction]
```

**步骤2.2**：删除步骤中的参数引用
```yaml
- name: Execute email extraction
  run: |
    python scripts/extract_emails.py \
      --output-dir /tmp/extraction_temp \
      2>&1 | tee /tmp/extraction_log.txt
```

### 阶段3：本地验证 ⏸️

**步骤3.1**：验证 Python 语法
```bash
python -m py_compile scripts/extract_emails.py
```

**步骤3.2**：验证 YAML 语法
```bash
python -c "import yaml; yaml.safe_load(open('.github/workflows/email-extraction.yml'))"
```

### 阶段4：提交并测试 ⏸️

**步骤4.1**：提交代码
```bash
git add scripts/extract_emails.py .github/workflows/email-extraction.yml
git commit -m "fix: 修复 extract_emails.py 参数和错误问题

- 修复 Rule 对象访问错误（AttributeError）
- 删除无用的命令行参数
- 简化 workflow 配置，完全使用 JSON 配置"
```

**步骤4.2**：推送到 GitHub
```bash
git push origin master
```

**步骤4.3**：手动触发工作流
```bash
gh workflow run email-extraction.yml
```

**步骤4.4**：等待执行完成并验证
```bash
sleep 60
gh run list --limit 1
gh run view RUN_ID --log | grep "matched_count"
```

---

## 验证标准

### 成功标准 ✅

1. **代码无错误**
   - 不再出现 `AttributeError: 'Rule' object has no attribute 'get'`
   - 工作流完整执行成功

2. **正确提取邮件**
   - `matched_count > 0`
   - 邮件信息正确显示

3. **参数简化**
   - Workflow 无输入参数
   - 完全依赖 JSON 配置

### 预期结果

```json
{
  "success": true,
  "matched_count": 2,
  "mails": [
    {
      "message_id": "...",
      "subject": "滴滴出行电子发票及行程报销单",
      "sender": "didifapiao@mailgate.xiaojukeji.com",
      "rule_id": "rule_001",
      "rule_name": "报销邮件提取"
    },
    {
      "message_id": "...",
      "subject": "网上购票系统-用户支付通知",
      "sender": "12306@rails.com.cn",
      "rule_id": "rule_002",
      "rule_name": "12306提取"
    }
  ]
}
```

---

## 快速回滚

如果修复后仍有问题，使用快速回滚：

```bash
# 回退到上一版本
git reset --soft HEAD~1

# 重新修改后再次提交
```

---

## 相关文件

| 文件 | 操作 | 原因 |
|------|------|------|
| `scripts/extract_emails.py` | 修改 | 修复代码错误 |
| `.github/workflows/email-extraction.yml` | 修改 | 简化配置 |
| `rules/parse_rules.json` | 不变 | 保持当前配置 |

---

**最后更新**: 2026-03-11
**状态**: 🟡 待执行
