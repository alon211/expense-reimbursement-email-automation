# 本地工作流测试指南

## 概述

`scripts/test_workflow_locally.py` 是一个本地测试脚本，用于模拟GitHub Actions的执行逻辑，方便在本地调试和验证邮件提取功能。

**主要功能**：
- ✅ 完全模拟GitHub Actions的执行流程
- ✅ 支持与Actions相同的参数
- ✅ 生成人类可读的测试报告
- ✅ 详细的日志记录
- ✅ 环境验证和错误诊断

**使用场景**：
1. 本地开发和调试
2. 验证规则配置
3. 测试邮箱连接
4. 在推送到GitHub前进行验证

---

## 快速开始

### 1. 环境准备

确保已配置好环境变量（`.env` 文件）：

```bash
# 必需配置
IMAP_HOST=imap.qq.com
IMAP_USER=your_email@qq.com
IMAP_PASS=your_authorization_code

# 可选配置
LOG_LEVEL=DEBUG
LOG_DIR=./logs
```

### 2. 基本用法

```bash
# 使用默认配置（3天时间范围）
python scripts/test_workflow_locally.py

# 指定时间范围（1/3/7/20/30天）
python scripts/test_workflow_locally.py --time-range-days 1

# 只验证配置，不实际提取
python scripts/test_workflow_locally.py --dry-run
```

---

## 命令行参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--time-range-days` | int | 3 | 搜索时间范围（天） |
| `--rule-filter` | string | None | 规则ID过滤器（逗号分隔） |
| `--output-dir` | string | None | 输出目录（默认使用临时目录） |
| `--verbose` | flag | False | 详细输出模式 |
| `--dry-run` | flag | False | 只验证配置，不实际提取 |

### 参数示例

```bash
# 1. 测试最近1天的邮件
python scripts/test_workflow_locally.py --time-range-days 1

# 2. 只测试rule_003规则
python scripts/test_workflow_locally.py --rule-filter rule_003

# 3. 测试多个规则
python scripts/test_workflow_locally.py --rule-filter rule_002,rule_003

# 4. 指定输出目录
python scripts/test_workflow_locally.py --output-dir ./my_test

# 5. 详细输出模式
python scripts/test_workflow_locally.py --verbose

# 6. 组合使用
python scripts/test_workflow_locally.py \
  --time-range-days 7 \
  --rule-filter rule_003 \
  --output-dir ./test_output \
  --verbose
```

---

## 输出说明

### 1. 控制台输出

实时显示执行进度和结果摘要：

```
🔧 本地工作流测试脚本
==================================================
📋 配置信息
  时间范围: 3天
  规则过滤: 全部
  详细模式: 否
  干运行: 否

📁 日志文件: ./logs/20260311220000_DEBUG.log

🔍 验证环境配置...
  ✅ IMAP_HOST: imap.qq.com
  ✅ IMAP_USER: your@qq.com
  ✅ IMAP_PASS: ****************
  ✅ 规则配置: ./rules/parse_rules.json
  ✅ 规则文件格式正确（包含3条规则）
  ✅ 输出目录: /tmp/test_workflow_20260311_220000
  ✅ 日志目录: ./logs

⏳ 开始执行提取...
==================================================
✅ 数据库初始化成功
✅ 规则加载完成（2条启用）

==================================================
📊 测试报告
==================================================
执行状态: ✅ 成功
执行时间: 2026-03-11T22:00:00
总耗时: 15.3秒
匹配邮件: 2封

📧 匹配邮件列表:

  1. 12306发票通知 - 诺诺网
     发件人: 诺诺网 <noreply@nuonuo.com>
     规则: rule_003 (诺诺网发票提取)
     日期: 2026-03-10 14:30:00

  2. 高德打车电子发票
     发件人: reservation@12306.com
     规则: rule_002 (12306提取)
     日期: 2026-03-09 09:15:00

💾 数据库统计:
  已提取邮件: 2条
  提取历史: 2条

✅ 测试完成
📁 详细报告: /tmp/test_workflow_20260311_220000/test_report.json
📁 输出目录: /tmp/test_workflow_20260311_220000
```

### 2. 日志文件

**位置**：`logs/YYYYMMDDHHMMSS_DEBUG.log`

**内容**：详细的执行日志，包括：
- 环境初始化过程
- IMAP连接详情
- 邮件搜索和提取过程
- 规则匹配详情
- 错误堆栈信息（如有）

**示例**：
```
2026-03-11 22:00:00 - ReimbursementMailFetcher - INFO - 本地工作流测试脚本启动
2026-03-11 22:00:00 - ReimbursementMailFetcher - INFO - 时间范围: 3天
2026-03-11 22:00:00 - ReimbursementMailFetcher - INFO - 规则过滤: 全部
2026-03-11 22:00:01 - ReimbursementMailFetcher - DEBUG - 正在连接IMAP服务器...
2026-03-11 22:00:02 - ReimbursementMailFetcher - INFO - ✅ 成功登录到邮箱
2026-03-11 22:00:02 - ReimbursementMailFetcher - INFO - 搜索邮件: SINCE 08-Mar-2026
2026-03-11 22:00:05 - ReimbursementMailFetcher - INFO - 找到15封邮件
...
```

### 3. JSON报告

**位置**：`{output_dir}/test_report.json`

**内容**：结构化的测试结果，便于程序解析

**示例**：
```json
{
  "success": true,
  "executed_at": "2026-03-11T22:00:00",
  "duration_seconds": 15.3,
  "time_range_days": 3,
  "matched_count": 2,
  "mails": [
    {
      "message_id": "abc123",
      "subject": "12306发票通知",
      "sender": "诺诺网 <noreply@nuonuo.com>",
      "date": "2026-03-10 14:30:00",
      "rule_id": "rule_003",
      "rule_name": "诺诺网发票提取"
    }
  ],
  "statistics": {
    "total_extracted": 2,
    "total_history": 2
  },
  "errors": []
}
```

---

## 典型使用场景

### 场景1：验证GitHub Actions配置

在推送到GitHub前，先本地验证：

```bash
# 1. 本地测试
python scripts/test_workflow_locally.py --time-range-days 3

# 2. 检查结果
# - 查看控制台输出
# - 查看日志文件
# - 查看JSON报告

# 3. 如果通过，推送到GitHub
git add .
git commit -m "xxx"
git push origin master

# 4. 在GitHub Actions页面手动触发workflow
# 5. 对比本地和GitHub结果
```

### 场景2：调试规则配置

```bash
# 1. 修改规则文件 rules/parse_rules.json
vim rules/parse_rules.json

# 2. 测试特定规则
python scripts/test_workflow_locally.py --rule-filter rule_003

# 3. 查看日志，确认规则匹配正确
cat logs/20260311220000_DEBUG.log | grep "规则匹配"
```

### 场景3：测试邮箱连接

```bash
# 使用干运行模式快速验证
python scripts/test_workflow_locally.py --dry-run

# 检查环境验证部分
# ✅ IMAP_HOST: imap.qq.com
# ✅ IMAP_USER: your@qq.com
# ✅ IMAP_PASS: ****************
```

### 场景4：性能测试

```bash
# 测试不同时间范围的性能
for days in 1 3 7 20; do
  echo "测试 $days 天..."
  python scripts/test_workflow_locally.py --time-range-days $days
done

# 查看各次运行的耗时
# 在输出中查找 "总耗时: XX.X秒"
```

---

## 故障排查

### 问题1：IMAP连接失败

**错误信息**：
```
❌ 执行失败: Failed to connect to imap.example.com:993
```

**可能原因**：
1. IMAP_HOST配置错误
2. 网络连接问题
3. 防火墙阻止
4. IMAP服务未启用

**解决方法**：
```bash
# 1. 检查.env文件中的IMAP_HOST
cat .env | grep IMAP_HOST

# 2. 测试网络连接
ping imap.qq.com

# 3. 测试IMAP端口
telnet imap.qq.com 993

# 4. 检查邮箱是否开启了IMAP服务
# QQ邮箱：设置 -> 账户 -> POP3/IMAP/SMTP/IMAP
```

### 问题2：邮箱认证失败

**错误信息**：
```
❌ 执行失败: Authentication failed
```

**可能原因**：
1. IMAP_USER或IMAP_PASS错误
2. 使用了登录密码而非授权码
3. 授权码已过期

**解决方法**：
```bash
# 1. 检查.env文件中的邮箱配置
cat .env | grep IMAP

# 2. 重新生成授权码
# QQ邮箱：设置 -> 账户 -> 生成授权码

# 3. 更新.env文件
vim .env

# 4. 重新测试
python scripts/test_workflow_locally.py --dry-run
```

### 问题3：规则文件格式错误

**错误信息**：
```
❌ 环境验证失败:
  - 规则配置文件JSON格式错误: Expecting property name enclosed in double quotes
```

**可能原因**：
1. JSON语法错误
2. 中文逗号使用了全角
3. 缺少逗号或括号

**解决方法**：
```bash
# 1. 使用JSON验证工具
python -m json.tool rules/parse_rules.json

# 2. 检查常见错误
# - 是否使用了全角逗号（，）而非半角（,）
# - 是否缺少逗号
# - 括号是否匹配

# 3. 修复后重新测试
python scripts/test_workflow_locally.py --dry-run
```

### 问题4：没有匹配的邮件

**输出信息**：
```
匹配邮件: 0封
📧 没有匹配的邮件
```

**可能原因**：
1. 时间范围内没有邮件
2. 规则配置不正确
3. 邮件不满足匹配条件

**解决方法**：
```bash
# 1. 增大时间范围
python scripts/test_workflow_locally.py --time-range-days 30

# 2. 检查规则配置
cat rules/parse_rules.json | grep enabled

# 3. 查看详细日志
cat logs/20260311220000_DEBUG.log | grep "匹配规则"

# 4. 发送测试邮件到邮箱
# 确保邮件满足规则条件
```

---

## 高级用法

### 1. 批量测试

```bash
# 创建测试脚本
cat > run_tests.sh << 'EOF'
#!/bin/bash
for days in 1 3 7; do
  echo "===== 测试 $days 天 ====="
  python scripts/test_workflow_locally.py \
    --time-range-days $days \
    --output-dir ./test_output_$days
  echo ""
done
EOF

# 运行测试
bash run_tests.sh
```

### 2. 对比测试

```bash
# 测试不同规则配置
python scripts/test_workflow_locally.py \
  --rule-filter rule_002 \
  --output-dir ./test_rule_002

python scripts/test_workflow_locally.py \
  --rule-filter rule_003 \
  --output-dir ./test_rule_003

# 对比结果
diff test_rule_002/test_report.json test_rule_003/test_report.json
```

### 3. 集成到CI/CD

```yaml
# .github/workflows/test.yml
name: Local Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run local test
        env:
          IMAP_HOST: ${{ secrets.IMAP_HOST }}
          IMAP_USER: ${{ secrets.IMAP_USER }}
          IMAP_PASS: ${{ secrets.IMAP_PASS }}
        run: |
          python scripts/test_workflow_locally.py --dry-run
```

---

## 与GitHub Actions的对应关系

| 本地测试 | GitHub Actions |
|---------|---------------|
| `--time-range-days` | 工作流参数 `time_range_days` |
| `--rule-filter` | 工作流参数 `rule_filter` |
| `.env` 文件 | GitHub Secrets |
| `./logs/` | Actions日志界面 |
| `test_report.json` | Artifacts上传 |

---

## 最佳实践

1. **先本地测试，再推送到GitHub**
   ```bash
   python scripts/test_workflow_locally.py
   # 如果通过，再推送
   git push origin master
   ```

2. **使用干运行模式快速验证**
   ```bash
   python scripts/test_workflow_locally.py --dry-run
   ```

3. **查看详细日志**
   ```bash
   python scripts/test_workflow_locally.py --verbose
   cat logs/$(ls -t logs/ | head -1)
   ```

4. **定期清理临时文件**
   ```bash
   # Windows
   del /q %TEMP%\test_workflow_*

   # Linux/Mac
   rm -rf /tmp/test_workflow_*
   ```

---

## 常见问题

**Q: 本地测试和GitHub Actions结果不一致？**

A: 可能原因：
- GitHub Actions使用不同的时区（UTC）
- 环境变量配置不同
- 检查 `.env` 文件和 GitHub Secrets 是否一致

**Q: 如何只测试不实际提取邮件？**

A: 使用 `--dry-run` 参数：
```bash
python scripts/test_workflow_locally.py --dry-run
```

**Q: 如何查看更详细的日志？**

A: 使用 `--verbose` 参数或查看日志文件：
```bash
python scripts/test_workflow_locally.py --verbose
cat logs/20260311220000_DEBUG.log
```

**Q: 临时文件在哪里？**

A:
- Windows: `C:\Users\<用户名>\AppData\Local\Temp\test_workflow_*`
- Linux/Mac: `/tmp/test_workflow_*`

---

## 相关文档

- [GitHub Actions 使用指南](GITHUB_ACTIONS_USAGE.md)
- [GitHub Secrets 配置指南](GITHUB_SECRETS_GUIDE.md)
- [系统架构总览](../architecture/system-overview.md)
