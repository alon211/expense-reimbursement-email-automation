# GitHub Actions 集成使用说明

**最后更新**: 2026-03-11

---

## 📋 目录

1. [快速开始](#快速开始)
2. [配置GitHub Secrets](#配置github-secrets)
3. [使用方法](#使用方法)
4. [下载提取结果](#下载提取结果)
5. [常见问题](#常见问题)

---

## 快速开始

### 步骤1：推送代码到GitHub

```bash
# 添加远程仓库
git remote add origin https://github.com/your-username/expense-reimbursement-email-automation.git

# 推送代码
git push -u origin master
```

### 步骤2：配置GitHub Secrets

详见下方 [配置GitHub Secrets](#配置github-secrets)

### 步骤3：测试触发

**方法1：GitHub网页界面**
1. 打开仓库 → **Actions** 标签
2. 选择 **Email Extraction** 工作流
3. 点击 **Run workflow**
4. 选择时间范围并运行

**方法2：命令行触发**

```bash
python scripts/trigger_workflow.py \
  --repo your-username/expense-reimbursement-email-automation \
  --time-range-days 20 \
  --wait
```

---

## 配置GitHub Secrets

### 操作步骤

1. 打开GitHub仓库页面
2. 点击 **Settings**（设置）
3. 左侧菜单点击 **Secrets and variables** → **Actions**
4. 点击 **New repository secret** 按钮添加Secret

### 必需Secrets

| Secret名称 | 说明 | 示例 |
|-----------|------|------|
| `IMAP_HOST` | IMAP服务器地址 | `imap.qq.com` |
| `IMAP_USER` | 邮箱账号 | `user@qq.com` |
| `IMAP_PASS` | 邮箱密码或授权码 | `authorization_code` |

### 可选Secrets

| Secret名称 | 说明 | 示例 |
|-----------|------|------|
| `DINGTALK_WEBHOOK` | 钉钉Webhook URL | `https://oapi.dingtalk.com/robot/send?access_token=xxx` |
| `DINGTALK_SECRET` | 钉钉签名密钥 | `SECxxxxxxxxxxx` |

### 🔒 安全注意事项

**重要**：根据 [sensitive-data.md](../architecture/config/sensitive-data.md) 的安全规范：

- ✅ **必须**：这些Secrets只存储在GitHub
- ✅ **必须**：使用授权码/应用专用密码，不要使用邮箱登录密码
- ❌ **禁止**：在本地 `.env` 文件中存储这些Secrets
- ❌ **禁止**：在代码中硬编码密码
- ❌ **禁止**：在日志中打印密码

---

## 使用方法

### 方法1：GitHub网页界面触发

1. 打开仓库的 **Actions** 标签
2. 选择 **Email Extraction** 工作流
3. 点击 **Run workflow**
4. 选择参数：
   - **搜索时间范围**：7天 / 20天 / 30天
   - **规则ID过滤器**（可选）：逗号分隔，留空表示全部
5. 点击 **Run workflow** 按钮
6. 查看执行日志

### 方法2：GitHub CLI触发

```bash
# 安装GitHub CLI
# macOS: brew install gh
# Linux: https://github.com/cli/cli/releases

# 登录
gh auth login

# 触发workflow
gh workflow run email-extraction.yml -f time_range_days=20

# 查看运行状态
gh run list

# 查看详细日志
gh run view <run-id> --log
```

### 方法3：自动化脚本触发（推荐）⭐

**一键完成：触发→等待→下载→解压→显示摘要**

```bash
# 设置环境变量
export GITHUB_TOKEN=your_github_token
export GITHUB_REPO=your-username/expense-reimbursement-email-automation

# 运行自动化脚本
python scripts/automated_extraction.py --time-range-days 20
```

**输出示例**：
```
🚀 触发邮件提取...
📂 仓库: your-username/expense-reimbursement-email-automation
⏱️  时间范围: 20 天

✅ Workflow已触发
📌 Run ID: 1234567890
🔗 查看详情: https://github.com/.../actions/runs/1234567890

⏳ 等待执行完成（最长10分钟）...

📊 提取完成：
   - 匹配邮件: 5 封
   - 执行时间: 2026-03-11T12:34:56

📥 下载结果...
✅ 已下载: ./downloads/extraction-results-1234567890.zip

📂 解压到: ./downloads/extraction-results-1234567890
✅ 解压完成

📋 提取摘要:
   - 时间戳: 2026-03-11_123456
   - 总文件数: 15
   - 类别数: 4

📎 文件清单:
   bodies/ (3 个文件)
      - email_001.html
      ...

   attachments/ (8 个文件)
      - invoice.pdf
      ...

✅ 流程完成！
```

**高级选项**：
```bash
# 不解压ZIP文件
python scripts/automated_extraction.py --no-extract

# 不列出文件清单
python scripts/automated_extraction.py --no-list

# 指定下载目录
python scripts/automated_extraction.py --download-dir ./my_downloads

# 使用命令行参数（不使用环境变量）
python scripts/automated_extraction.py \
  --repo your-username/repo \
  --token your_token \
  --time-range-days 30
```

**在代码中使用**：
```python
from scripts.automated_extraction import automated_extraction

result = automated_extraction(
    repo="your-username/repo",
    token="your_token",
    time_range_days=20,
    download_dir="./downloads",
    extract=True,
    list_files=True
)

if result["success"]:
    print(f"✅ 成功！提取了 {result['matched_count']} 封邮件")
    print(f"📁 下载路径: {result['download_path']}")
else:
    print(f"❌ 失败: {result['error']}")
```

---

### 方法4：基础Python脚本触发

```bash
# 设置环境变量（推荐）
export GITHUB_TOKEN=your_github_token
export GITHUB_REPO=your-username/expense-reimbursement-email-automation

# 触发workflow（不等待结果）
python scripts/trigger_workflow.py \
  --time-range-days 20

# 触发workflow（等待完成）
python scripts/trigger_workflow.py \
  --time-range-days 20 \
  --wait

# 触发workflow（等待并下载Artifacts）
python scripts/trigger_workflow.py \
  --time-range-days 20 \
  --wait \
  --download-artifacts
```

---

### 方法5：代码中调用API

```python
from core.github_client import GitHubWorkflowClient

# 创建客户端
client = GitHubWorkflowClient(
    token="your_github_token",
    repo="your-username/expense-reimbursement-email-automation"
)

# 触发workflow
run_id = client.trigger_workflow(
    workflow_file="email-extraction.yml",
    inputs={"time_range_days": "20"}
)

print(f"✅ Workflow已触发，run_id: {run_id}")

# 等待并获取结果
outputs = client.get_workflow_outputs(run_id)
print(f"📊 提取结果: {outputs.get('summary')}")
```

---

## 📂 数据存储流程详解

### 存储生命周期

GitHub Actions环境中的数据存储分为三个阶段，每个阶段有不同的位置和生命周期：

#### 阶段1：执行期间（临时存储）

**位置**：GitHub Actions运行环境的 `/tmp/extraction_temp/`

**目录结构**：
```
/tmp/extraction_temp/
├── bodies/rule_001/          # 邮件正文HTML
├── attachments/rule_001/     # 邮件附件（PDF、图片等）
├── extracted/rule_001/       # 结构化数据（JSON）
├── nuonuo_invoices/rule_001/ # 诺诺网发票PDF
└── data.db                    # SQLite数据库
```

**生命周期**：
- ⏰ **创建时机**：每次workflow执行开始时
- 🗑️ **删除时机**：workflow执行结束后自动清理
- 🔒 **访问权限**：仅workflow执行期间可访问
- ❌ **无法从外部访问**

**相关代码**：
```yaml
# .github/workflows/email-extraction.yml
- name: Clean temporary directories
  run: |
    rm -rf /tmp/extraction_temp
    mkdir -p /tmp/extraction_temp
```

---

#### 阶段2：执行完成后（打包输出）

**位置**：`/tmp/extraction_output/`

**目录结构**：
```
/tmp/extraction_output/
└── 2026-03-11_123456/         # 时间戳目录（如：2026-03-11_123456）
    ├── bodies/                 # 从临时目录复制
    ├── attachments/
    ├── extracted/
    ├── nuonuo_invoices/
    └── summary.json            # 提取摘要（包含文件数量、时间等）
```

**生命周期**：
- ⏰ **创建时机**：workflow执行成功后
- 📦 **用途**：准备上传到GitHub Artifacts
- 🗑️ **删除时机**：上传到Artifacts后立即删除
- ❌ **无法从外部访问**

**相关代码**：
```yaml
# .github/workflows/email-extraction.yml
- name: Package extraction results
  run: |
    python scripts/package_results.py \
      --source-dir /tmp/extraction_temp \
      --output-dir /tmp/extraction_output
```

**summary.json 示例**：
```json
{
  "timestamp": "2026-03-11_123456",
  "total_files": 15,
  "categories_copied": 4,
  "categories": [
    {
      "name": "bodies",
      "file_count": 3
    },
    {
      "name": "attachments",
      "file_count": 8
    },
    {
      "name": "extracted",
      "file_count": 3
    },
    {
      "name": "nuonuo_invoices",
      "file_count": 1
    }
  ]
}
```

---

#### 阶段3：长期存储（GitHub Artifacts）⭐

**位置**：**GitHub服务器**

**Artifact名称**：`extraction-results-<run-id>`

**内容**：包含阶段2的所有文件，打包为ZIP格式

**生命周期**：
- ⏰ **创建时机**：workflow执行成功后自动上传
- 💾 **保留期限**：默认7天（可配置为1-90天）
- 📊 **大小限制**：单次运行最大2GB
- ✅ **可从外部访问**：网页/CLI/API

**相关代码**：
```yaml
# .github/workflows/email-extraction.yml
- name: Upload extraction results as artifacts
  uses: actions/upload-artifact@v4
  if: always()  # 即使失败也上传日志
  with:
    name: extraction-results-${{ github.run_id }}
    path: /tmp/extraction_output/
    retention-days: 7  # 保留7天
```

**修改保留期**：
```yaml
# 改为保留30天
retention-days: 30

# 改为保留90天（最大值）
retention-days: 90
```

---

### 存储流程对比表

| 阶段 | 位置 | 创建时机 | 删除时机 | 访问方式 | 保留期限 |
|------|------|---------|---------|---------|---------|
| **执行期间** | `/tmp/extraction_temp/` | 执行开始 | 执行结束 | ❌ 无法访问 | 仅执行期间 |
| **打包输出** | `/tmp/extraction_output/` | 执行成功后 | 上传后删除 | ❌ 无法访问 | 仅上传前 |
| **GitHub Artifacts** | GitHub服务器 | 上传后 | 自动过期 | ✅ 可下载 | 7天（可配置） |

---

### 关键要点

⚠️ **重要提示**：
1. **临时文件会自动清空**：GitHub Actions运行结束后，`/tmp/` 目录的文件会被删除
2. **唯一可访问的方式**：通过GitHub Artifacts下载提取的文件
3. **过期自动删除**：Artifacts超过保留期后会自动删除，请及时下载
4. **失败时也会上传日志**：如果workflow失败，会自动上传日志Artifact（保留3天）

✅ **最佳实践**：
1. 定期检查并下载重要的提取结果
2. 根据需要调整保留期限（`retention-days`）
3. 失败时查看日志Artifact获取错误信息
4. 对于重要数据，下载后备份到其他存储位置

---

## 下载提取结果

### 方法1：GitHub网页界面

1. 打开仓库的 **Actions** 标签
2. 点击具体的运行记录
3. 滚动到页面底部的 **Artifacts** 区域
4. 点击 **extraction-results-xxx** 下载

### 方法2：GitHub CLI

```bash
# 下载最新的Artifact
gh run download <run-id> -n extraction-results-<run-id>
```

### 方法3：Python API

```python
from core.github_client import GitHubWorkflowClient

client = GitHubWorkflowClient(
    token="your_token",
    repo="your-username/repo"
)

# 下载Artifact
filepath = client.download_artifact(
    run_id="1234567890",
    artifact_name="extraction-results-1234567890",
    download_path="."
)

print(f"✅ 已下载: {filepath}")
```

### Artifact内容结构

```
extraction-results-<run-id>.zip
└── YYYY-MM-DD_HHMMSS/
    ├── bodies/              # 邮件正文HTML
    ├── attachments/         # 邮件附件
    ├── extracted/           # 结构化数据（JSON）
    ├── nuonuo_invoices/     # 诺诺网发票PDF
    └── summary.json         # 提取摘要
```

---

### 实际使用场景

#### 场景1：手动下载（适合偶尔使用）

**需求**：偶尔需要提取邮件，手动下载结果

**步骤**：

```bash
# 1. 触发workflow（GitHub网页或CLI）
gh workflow run email-extraction.yml -f time_range_days=20

# 2. 查看运行状态
gh run list

# 输出示例：
# STATUS  NAME                 RUN ID         CREATED AT
# success  Email Extraction     1234567890     2 minutes ago

# 3. 等待完成（状态变为 success 或 failure）
gh run view 1234567890 --log

# 4. 下载Artifact
gh run download 1234567890 -n extraction-results-1234567890

# 5. 解压并查看
unzip extraction-results-1234567890.zip
cd 2026-03-11_123456/
ls -la

# 输出示例：
# bodies/
# attachments/
# extracted/
# nuonuo_invoices/
# summary.json

# 6. 查看摘要
cat summary.json
```

---

#### 场景2：自动化集成（适合程序调用）

**需求**：在自动化脚本或定时任务中调用，自动处理结果

**示例脚本**：

```python
#!/usr/bin/env python3
"""
自动化邮件提取并处理结果
"""
import os
import sys
import zipfile
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.github_client import GitHubWorkflowClient


def automated_extraction():
    """自动化提取流程"""

    # 1. 创建客户端
    client = GitHubWorkflowClient(
        token=os.environ.get("GITHUB_TOKEN"),
        repo=os.environ.get("GITHUB_REPO")
    )

    print("🚀 触发邮件提取...")

    # 2. 触发workflow
    run_id = client.trigger_workflow(
        workflow_file="email-extraction.yml",
        inputs={"time_range_days": "20"}
    )

    print(f"✅ Workflow已触发，run_id: {run_id}")
    print(f"🔗 查看详情: https://github.com/{client.repo}/actions/runs/{run_id}")

    # 3. 等待完成
    print("⏳ 等待执行完成...")
    try:
        outputs = client.get_workflow_outputs(run_id, timeout=600)

        # 4. 解析结果
        import json
        summary = json.loads(outputs.get("summary", "{}"))
        matched_count = summary.get("matched_count", 0)

        print(f"📊 提取完成：匹配 {matched_count} 封邮件")

        # 5. 下载Artifact
        artifact_name = f"extraction-results-{run_id}"
        print(f"📥 下载结果...")

        zip_file = client.download_artifact(
            run_id=run_id,
            artifact_name=artifact_name,
            download_path="./downloads"
        )

        print(f"✅ 已下载: {zip_file}")

        # 6. 解压
        extract_dir = Path("./downloads") / artifact_name
        extract_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        print(f"📂 已解压到: {extract_dir}")

        # 7. 查看摘要
        summary_file = list(extract_dir.glob("*/summary.json"))[0]
        with open(summary_file, 'r', encoding='utf-8') as f:
            summary_data = json.load(f)

        print(f"\n📋 提取摘要:")
        print(f"   - 总文件数: {summary_data.get('total_files')}")
        print(f"   - 类别数: {summary_data.get('categories_copied')}")

        # 8. 处理文件（示例：列出所有附件）
        attachments_dir = list(extract_dir.glob("*/attachments"))[0]
        attachments = list(attachments_dir.rglob("*"))
        attachments = [f for f in attachments if f.is_file()]

        print(f"\n📎 附件列表:")
        for att in attachments:
            print(f"   - {att.name}")

        return 0

    except Exception as e:
        print(f"❌ 错误: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(automated_extraction())
```

**使用方法**：

```bash
# 设置环境变量
export GITHUB_TOKEN=your_token
export GITHUB_REPO=your-username/repo

# 运行脚本
python scripts/automated_extraction.py
```

---

#### 场景3：定时任务（Cron集成）

**需求**：每天定时提取邮件，自动备份结果

**Crontab配置**：

```bash
# 编辑crontab
crontab -e

# 添加定时任务（每天凌晨2点执行）
0 2 * * * cd /path/to/expense-reimbursement-email-automation && /usr/bin/python3 scripts/automated_extraction.py >> /var/log/email_extraction.log 2>&1
```

**Systemd Timer配置**（Linux推荐）：

```ini
# /etc/systemd/system/email-extraction.service
[Unit]
Description=Email Extraction Automation
After=network.target

[Service]
Type=oneshot
User=your-user
WorkingDirectory=/path/to/expense-reimbursement-email-automation
Environment="GITHUB_TOKEN=your_token"
Environment="GITHUB_REPO=your-username/repo"
ExecStart=/usr/bin/python3 scripts/automated_extraction.py

[Install]
WantedBy=multi-user.target
```

```ini
# /etc/systemd/system/email-extraction.timer
[Unit]
Description=Run Email Extraction Daily
Requires=email-extraction.service

[Timer]
OnCalendar=*-*-* 02:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

**启用定时器**：

```bash
# 重载systemd配置
sudo systemctl daemon-reload

# 启动定时器
sudo systemctl enable email-extraction.timer

# 启动服务
sudo systemctl start email-extraction.timer

# 查看状态
sudo systemctl status email-extraction.timer
```

---

#### 场景4：多仓库管理（适合企业级）

**需求**：管理多个项目的邮件提取

**配置文件**：

```yaml
# config/repositories.yaml
repositories:
  - name: "报销项目A"
    repo: "company/expense-reimbursement-a"
    time_range_days: 7
    auto_download: true

  - name: "报销项目B"
    repo: "company/expense-reimbursement-b"
    time_range_days: 20
    auto_download: false
```

**批量处理脚本**：

```python
#!/usr/bin/env python3
"""
批量处理多个仓库的邮件提取
"""
import yaml
from pathlib import Path
from core.github_client import GitHubWorkflowClient

# 加载配置
with open("config/repositories.yaml") as f:
    config = yaml.safe_load(f)

token = os.environ.get("GITHUB_TOKEN")

# 遍历所有仓库
for repo_config in config["repositories"]:
    name = repo_config["name"]
    repo = repo_config["repo"]
    days = repo_config["time_range_days"]

    print(f"\n🔄 处理仓库: {name} ({repo})")

    # 创建客户端
    client = GitHubWorkflowClient(token=token, repo=repo)

    # 触发workflow
    run_id = client.trigger_workflow(
        workflow_file="email-extraction.yml",
        inputs={"time_range_days": str(days)}
    )

    print(f"✅ 已触发，run_id: {run_id}")

    # 如果配置了自动下载
    if repo_config.get("auto_download"):
        print(f"⏳ 等待完成并下载...")
        outputs = client.get_workflow_outputs(run_id)

        artifact_name = f"extraction-results-{run_id}"
        zip_file = client.download_artifact(
            run_id=run_id,
            artifact_name=artifact_name,
            download_path=f"./downloads/{name}"
        )

        print(f"✅ 已下载: {zip_file}")
```

---

## 常见问题

### Q1: GitHub Secrets在哪里配置？

**A**: 仓库 → Settings → Secrets and variables → Actions → New repository secret

### Q2: 如何获取GitHub Personal Access Token？

**A**:
1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. 点击 **Generate new token (classic)**
3. 勾选权限：`repo`（完整仓库访问）和 `workflow`（触发workflow）
4. 生成并复制Token

### Q3: 如何获取邮箱授权码？

**A**:
- **QQ邮箱**：设置 → 账户 → POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务 → 生成授权码
- **163邮箱**：设置 → POP3/SMTP/IMAP → 开启服务并设置授权码
- **Gmail**：Google账户 → 安全性 → 应用专用密码

### Q4: 提取的文件会保存多久？

**A**:
- GitHub Artifacts默认保留7天（可配置为1-90天）
- 临时文件在每次执行后自动清空
- 超期后自动删除，请及时下载

**修改保留期**：在 `.github/workflows/email-extraction.yml` 中修改：
```yaml
retention-days: 30  # 改为30天
```

### Q4.1: 临时文件存储在哪里？

**A**:
GitHub Actions环境的 `/tmp/extraction_temp/` 目录：
- **执行期间**：用于存储提取的文件
- **执行结束**：自动清空，无法访问
- **唯一可访问方式**：下载GitHub Artifacts

详见上方 [数据存储流程详解](#-数据存储流程详解)

### Q4.2: 如何自动下载提取结果？

**A**:
使用 `--download-artifacts` 参数：
```bash
python scripts/trigger_workflow.py \
  --repo your-username/repo \
  --time-range-days 20 \
  --wait \
  --download-artifacts  # 自动下载到当前目录
```

或使用Python API：
```python
client = GitHubWorkflowClient(token="xxx", repo="xxx")
run_id = client.trigger_workflow(...)
outputs = client.get_workflow_outputs(run_id)
zip_file = client.download_artifact(run_id, f"extraction-results-{run_id}")
```

### Q5: 如何查看执行日志？

**A**:
1. GitHub网页：Actions → 点击运行记录 → 查看步骤日志
2. GitHub CLI：`gh run view <run-id> --log`
3. 失败时会自动上传日志Artifact

### Q6: 为什么workflow执行失败？

**A**: 常见原因：
1. GitHub Secrets未配置或配置错误
2. 邮箱授权码错误或已过期
3. IMAP服务未开启
4. 网络连接问题

查看日志获取详细错误信息。

### Q7: 如何配置定时任务？

**A**: 参考上方 [实际使用场景](#实际使用场景) 中的场景3和场景4

---

## 文件说明

### 新创建的脚本

| 文件路径 | 用途 | 推荐度 |
|---------|------|--------|
| `scripts/automated_extraction.py` | **自动化提取脚本**（一键完成）⭐ | ⭐⭐⭐⭐ |
| `scripts/extract_emails.py` | 独立提取脚本 | ⭐⭐⭐ |
| `scripts/github_action_adapter.py` | GitHub Actions环境适配器 | ⭐⭐ |
| `scripts/cleanup_temp_files.py` | 清理临时文件 | ⭐⭐ |
| `scripts/package_results.py` | 打包提取结果 | ⭐⭐ |
| `core/github_client.py` | GitHub API客户端 | ⭐⭐⭐⭐ |
| `scripts/trigger_workflow.py` | 命令行触发工具 | ⭐⭐⭐ |
| `scripts/send_dingtalk_notification.py` | 钉钉通知脚本 | ⭐⭐ |
| `.github/workflows/email-extraction.yml` | GitHub Actions工作流 | ⭐⭐⭐⭐⭐ |

### 临时文件存储

- **临时工作目录**：`/tmp/extraction_temp`（每次清空）
- **输出目录**：`/tmp/extraction_output`（上传到Artifacts后删除）

---

## 后续步骤

完成GitHub Actions集成后，可以进入：
- **子计划3**：本地Docker Web UI控制端（可视化界面）

---

## 参考资料

- [实施计划](../plan/github-actions-implementation-plan.md)
- [子计划2详细文档](../plan/subplan-2-github-actions.md)
- [敏感信息安全管控](../architecture/config/sensitive-data.md)
- [部署架构文档](../architecture/deployment.md)
