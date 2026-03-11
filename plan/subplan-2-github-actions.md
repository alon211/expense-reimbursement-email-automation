# 子计划2：GitHub Actions自动化执行（主要模式）

**目标**: 将核心提取逻辑改造为GitHub Actions工作流，实现远程触发执行，API直接返回JSON结果

**预计工期**: 5-7天

**依赖**: 需要GitHub仓库和GitHub Personal Access Token

---

## 📋 执行步骤

### 阶段0：附件重命名功能（0.5天）🆕

**重要**: 在提取邮件时，如果多个邮件的附件文件名相同，需要自动重命名避免覆盖。

**重命名策略**:
- **策略**: 序号递增（如 `invoice.pdf` → `invoice_1.pdf`, `invoice_2.pdf`）
- **时机**: 仅在冲突时重命名（保留原始文件名）
- **范围**: 仅重命名附件文件，压缩包内的文件保持原样

#### 步骤0.1：修改附件提取逻辑

在 [core/email_extractor.py](../core/email_extractor.py) 中添加文件冲突检测和重命名：

```python
def extract_attachments(self, msg: email.message.Message, rule_id: str, extraction_dir: Path, message_id: str) -> Tuple[int, List[str]]:
    """
    提取并保存邮件附件（支持文件重命名）
    """
    rule_dir = extraction_dir / "attachments" / rule_id
    rule_dir.mkdir(parents=True, exist_ok=True)

    attachments = []
    attachment_count = 0

    for part in msg.walk():
        # ... 前面代码保持不变 ...

        if filename:
            filename = self._decode_filename(filename)

            # 🆕 检查文件名冲突并重命名
            filepath = self._get_unique_filename(rule_dir, filename)

            try:
                with open(filepath, 'wb') as f:
                    f.write(part.get_payload(decode=True))
                attachments.append(str(filepath))
                attachment_count += 1
                logger.info(f"【提取器】保存附件：{filepath}")
            except Exception as e:
                logger.error(f"【提取器】保存附件失败：{filename}，错误：{e}")

    return attachment_count, attachments

def _get_unique_filename(self, directory: Path, filename: str) -> Path:
    """
    生成唯一的文件名（避免冲突）

    策略：序号递增
    - invoice.pdf → invoice_1.pdf → invoice_2.pdf
    """
    filepath = directory / filename

    # 如果文件不存在，直接返回原路径
    if not filepath.exists():
        return filepath

    # 文件已存在，添加序号
    name = filepath.stem  # 文件名不含扩展名
    ext = filepath.suffix  # 扩展名（含点）

    counter = 1
    while True:
        new_filename = f"{name}_{counter}{ext}"
        new_filepath = directory / new_filename

        if not new_filepath.exists():
            logger.info(f"【提取器】文件重命名：{filename} → {new_filename}")
            return new_filepath

        counter += 1

        # 防止无限循环（最多尝试1000次）
        if counter > 1000:
            raise Exception(f"无法生成唯一文件名：{filename}")
```

#### 步骤0.2：添加单元测试

创建 [tests/test_attachment_rename.py](../tests/test_attachment_rename.py)：

```python
"""
测试附件重命名功能
"""
import pytest
from pathlib import Path
from core.email_extractor import EmailExtractor

def test_unique_filename_generation():
    """测试唯一文件名生成"""
    extractor = EmailExtractor()

    # 创建临时目录
    test_dir = Path("/tmp/test_attachments")
    test_dir.mkdir(parents=True, exist_ok=True)

    try:
        # 创建测试文件
        (test_dir / "invoice.pdf").touch()

        # 测试重命名
        result1 = extractor._get_unique_filename(test_dir, "invoice.pdf")
        assert result1 == test_dir / "invoice_1.pdf"

        # 再次测试
        result2 = extractor._get_unique_filename(test_dir, "invoice.pdf")
        assert result2 == test_dir / "invoice_2.pdf"

        print("✅ 文件重命名测试通过")
    finally:
        # 清理
        import shutil
        shutil.rmtree(test_dir)

if __name__ == "__main__":
    test_unique_filename_generation()
```

---

### 阶段1：核心逻辑提取（2-3天）

#### 步骤1.1：创建独立提取脚本

创建 [scripts/extract_emails.py](../scripts/extract_emails.py)：

```python
#!/usr/bin/env python3
"""
独立的邮件提取脚本（用于GitHub Actions）
不依赖main.py的循环逻辑，单次执行
"""
import sys
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.rule_loader import RuleLoader
from core.email_fetcher import fetch_reimbursement_mails
from core.email_extractor import extract_email_full
from core.database import DatabaseManager
from config.settings import EXTRACT_ROOT_DIR, PARSE_RULES_JSON_PATH

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='邮件提取脚本')
    parser.add_argument('--rules-path', default=PARSE_RULES_JSON_PATH)
    parser.add_argument('--time-range-days', type=int, default=20)
    parser.add_argument('--output-format', default='json', choices=['json', 'text'])
    parser.add_argument('--output-dir', default='/tmp/extraction_result')

    args = parser.parse_args()

    logger.info(f"📧 开始提取邮件（时间范围: {args.time_range_days}天）...")

    try:
        # 创建输出目录
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # 初始化数据库
        db_path = output_dir / "data.db"
        db = DatabaseManager(str(db_path))

        # 执行提取
        matched_mails = fetch_reimbursement_mails(
            logger_instance=logger,
            db_manager=db
        )

        # 处理匹配的邮件
        extraction_results = []
        for mail_data in matched_mails:
            logger.info(f"处理邮件: {mail_data['subject']}")

            # 提取内容
            extraction_result = extract_email_full(
                msg=None,  # 需要适配
                mail_data=mail_data,
                extraction_dir=output_dir
            )
            extraction_results.append(extraction_result)

        # 生成结果
        result = {
            "success": True,
            "executed_at": datetime.now().isoformat(),
            "time_range_days": args.time_range_days,
            "matched_count": len(matched_mails),
            "mails": [
                {
                    "message_id": m.get("message_id"),
                    "subject": m.get("subject"),
                    "sender": m.get("sender"),
                    "mail_date": m.get("date"),
                    "rule_id": m.get("matched_rules", [{}])[0].get("rule_id") if m.get("matched_rules") else None
                }
                for m in matched_mails
            ],
            "db_stats": db.get_statistics(),
            "errors": []
        }

        # 输出结果
        print("=== EXTRACTION_RESULT ===")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print("=== EXTRACTION_RESULT_END ===")

        return 0 if result["success"] else 1

    except Exception as e:
        logger.error(f"❌ 提取失败: {e}", exc_info=True)
        result = {
            "success": False,
            "error": str(e),
            "executed_at": datetime.now().isoformat()
        }
        print("=== EXTRACTION_RESULT ===")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print("=== EXTRACTION_RESULT_END ===")
        return 1


if __name__ == "__main__":
    sys.exit(main())
```

**要点**:
- 独立于main.py，单次执行
- 接受命令行参数
- 输出JSON格式结果
- 使用特殊标记包围结果（便于GitHub Actions解析）

#### 步骤1.2：创建输出格式模板

创建 [outputs/results.json.template](../outputs/results.json.template)：

```json
{
  "success": true,
  "executed_at": "2026-03-11T12:00:00Z",
  "time_range_days": 20,
  "matched_count": 0,
  "mails": [
    {
      "message_id": "...",
      "subject": "邮件主题",
      "sender": "sender@example.com",
      "mail_date": "2026-03-11 10:00:00",
      "rule_id": "rule_002",
      "attachments": ["file1.pdf"],
      "body_preview": "正文预览..."
    }
  ],
  "db_stats": {
    "total_emails": 100,
    "new_emails": 5
  },
  "errors": []
}
```

#### 步骤1.3：创建GitHub Actions适配器

创建 [scripts/github_action_adapter.py](../scripts/github_action_adapter.py)：

```python
#!/usr/bin/env python3
"""
GitHub Actions环境适配器
处理GitHub Secrets和环境变量
"""
import os
import sys
from pathlib import Path

def setup_github_environment():
    """设置GitHub Actions环境"""

    # 从GitHub Secrets读取配置
    required_secrets = [
        'IMAP_HOST',
        'IMAP_USER',
        'IMAP_PASS'
    ]

    optional_secrets = [
        'DINGTALK_WEBHOOK',
        'DINGTALK_SECRET'
    ]

    # 验证必需配置
    missing = []
    for secret in required_secrets:
        if not os.environ.get(secret):
            missing.append(secret)

    if missing:
        print(f"❌ 缺少必需的Secrets: {', '.join(missing)}")
        sys.exit(1)

    print(f"✅ GitHub Secrets配置验证通过")
    print(f"IMAP_HOST: {os.environ.get('IMAP_HOST', '')[:8]}...")

    return True

if __name__ == "__main__":
    setup_github_environment()
```

---

### 阶段2：GitHub Actions工作流（2-3天）

#### 步骤2.1：创建工作流文件

创建 [.github/workflows/email-extraction.yml](../.github/workflows/email-extraction.yml)：

```yaml
name: Email Extraction

on:
  workflow_dispatch:
    inputs:
      time_range_days:
        description: '搜索时间范围（天）'
        required: false
        default: '20'
        type: choice
        options:
          - 7
          - 20
          - 30
      rule_filter:
        description: '规则ID过滤器（逗号分隔，留空表示全部）'
        required: false
        type: string

  repository_dispatch:
    types: [trigger-extraction]

# 配置环境变量（从GitHub Secrets）
env:
  IMAP_HOST: ${{ secrets.IMAP_HOST }}
  IMAP_USER: ${{ secrets.IMAP_USER }}
  IMAP_PASS: ${{ secrets.IMAP_PASS }}
  DINGTALK_WEBHOOK: ${{ secrets.DINGTALK_WEBHOOK }}
  DINGTALK_SECRET: ${{ secrets.DINGTALK_SECRET }}

jobs:
  extract-emails:
    runs-on: ubuntu-latest

    # 定义输出（供API返回）
    outputs:
      summary: ${{ steps.generate-output.outputs.summary }}
      detail: ${{ steps.generate-output.outputs.detail }}
      status: ${{ steps.generate-output.outputs.status }}
      executed_at: ${{ steps.generate-output.outputs.executed_at }}

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.9'
          cache: 'pip'

      - name: Install system dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y p7zip-full unrar-free

      - name: Install Python dependencies
        run: |
          pip install -r requirements.txt

      - name: Load configuration
        run: |
          echo "✅ 配置加载完成"
          echo "IMAP_HOST: ${IMAP_HOST:0:8}..."
          echo "时间范围: ${{ github.event.inputs.time_range_days || 20 }} 天"

      - name: Execute email extraction
        id: extract
        run: |
          python scripts/extract_emails.py \
            --time-range-days ${{ github.event.inputs.time_range_days || 20 }} \
            --output-dir /tmp/extraction_result \
            2>&1 | tee /tmp/extraction_log.txt

      - name: Generate outputs
        id: generate-output
        run: |
          # 从日志中提取结果
          RESULT=$(sed -n '/=== EXTRACTION_RESULT ===/,/=== EXTRACTION_RESULT_END ===/p' /tmp/extraction_log.txt | sed '1d;$d')

          if [ -z "$RESULT" ]; then
            echo "⚠️  未找到提取结果"
            exit 1
          fi

          # 生成摘要
          SUMMARY=$(echo "$RESULT" | jq '{
            success,
            matched_count,
            executed_at,
            time_range_days
          }')

          # 获取执行时间
          EXECUTED_AT=$(echo "$RESULT" | jq -r '.executed_at')
          STATUS=$(echo "$RESULT" | jq -r '.success')

          # 设置输出
          echo "summary=$SUMMARY" >> $GITHUB_OUTPUT
          echo "detail=$RESULT" >> $GITHUB_OUTPUT
          echo "status=$STATUS" >> $GITHUB_OUTPUT
          echo "executed_at=$EXECUTED_AT" >> $GITHUB_OUTPUT

          echo "✅ 结果生成完成"

      - name: Send DingTalk notification
        if: success()
        env:
          WEBHOOK_URL: ${{ secrets.DINGTALK_WEBHOOK }}
          SECRET: ${{ secrets.DINGTALK_SECRET }}
        run: |
          if [ -z "$WEBHOOK_URL" ]; then
            echo "未配置钉钉Webhook，跳过通知"
            exit 0
          fi

          python scripts/send_dingtalk_notification.py \
            --webhook "$WEBHOOK_URL" \
            --secret "$SECRET" \
            --summary "${{ steps.generate-output.outputs.summary }}"

      - name: Handle failure
        if: failure()
        run: |
          echo "❌ 提取失败，请检查日志"
          # 发送失败通知到钉钉

      - name: Upload logs (if failed)
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: extraction-logs-${{ github.run_id }}
          path: |
            /tmp/extraction_log.txt
            /tmp/extraction_result/
          retention-days: 7
```

#### 步骤2.2：配置GitHub Secrets

在GitHub仓库中配置Secrets：

1. 进入仓库设置页面
2. 点击 "Secrets and variables" -> "Actions"
3. 添加以下Secrets：

| Secret名称 | 说明 | 示例 |
|-----------|------|------|
| `IMAP_HOST` | IMAP服务器地址 | imap.qq.com |
| `IMAP_USER` | 邮箱账号 | user@qq.com |
| `IMAP_PASS` | 邮箱密码或授权码 | authorization_code |
| `DINGTALK_WEBHOOK` | 钉钉Webhook URL | https://oapi.dingtalk.com/... |
| `DINGTALK_SECRET` | 钉钉签名密钥 | SEC... |

#### 步骤2.3：测试手动触发

使用GitHub CLI或网页界面测试：

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

---

### 阶段3：结果返回和集成（2天）

#### 步骤3.1：创建GitHub API客户端

创建 [core/github_client.py](../core/github_client.py)：

```python
"""
GitHub API客户端
用于触发workflow和获取结果
"""
import requests
import time
from typing import Dict, Optional


class GitHubWorkflowClient:
    """GitHub Workflow API客户端"""

    def __init__(self, token: str, repo: str):
        """
        Args:
            token: GitHub Personal Access Token
            repo: 仓库格式 "username/repo"
        """
        self.token = token
        self.repo = repo
        self.api_base = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }

    def trigger_workflow(self, workflow_file: str, inputs: Dict = None) -> str:
        """
        触发workflow_dispatch事件

        Args:
            workflow_file: 工作流文件名（如 "email-extraction.yml"）
            inputs: 输入参数字典

        Returns:
            run_id: 工作流运行ID
        """
        url = f"{self.api_base}/repos/{self.repo}/actions/workflows/{workflow_file}/dispatches"

        payload = {"ref": "main"}  # 或 "master"
        if inputs:
            payload["inputs"] = inputs

        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()

        # 获取最新的run_id
        time.sleep(2)  # 等待workflow创建
        run_id = self._get_latest_run_id()

        return run_id

    def get_workflow_status(self, run_id: str) -> Dict:
        """
        查询工作流状态

        Args:
            run_id: 工作流运行ID

        Returns:
            包含status、conclusion等信息的字典
        """
        url = f"{self.api_base}/repos/{self.repo}/actions/runs/{run_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_workflow_outputs(self, run_id: str) -> Dict:
        """
        获取工作流输出结果

        注意：需要在workflow完成后才能获取

        Args:
            run_id: 工作流运行ID

        Returns:
            包含summary、detail、status等输出的字典
        """
        # 等待workflow完成
        while True:
            status = self.get_workflow_status(run_id)
            workflow_status = status.get("status")

            if workflow_status == "completed":
                break
            elif workflow_status in ["queued", "in_progress"]:
                time.sleep(10)
            else:
                raise Exception(f"Workflow failed with status: {workflow_status}")

        # 获取outputs
        return status.get("outputs", {})

    def _get_latest_run_id(self) -> str:
        """获取最新的工作流运行ID"""
        url = f"{self.api_base}/repos/{self.repo}/actions/runs?per_page=1"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()["workflow_runs"][0]["id"]


# 使用示例
if __name__ == "__main__":
    client = GitHubWorkflowClient(
        token="ghp_xxx",
        repo="username/expense-reimbursement-email-automation"
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

#### 步骤3.2：创建触发脚本

创建 [scripts/trigger_workflow.py](../scripts/trigger_workflow.py)：

```python
#!/usr/bin/env python3
"""
命令行工具：触发GitHub Actions workflow
"""
import sys
import argparse
import json
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.github_client import GitHubWorkflowClient


def main():
    parser = argparse.ArgumentParser(description='触发GitHub Actions工作流')
    parser.add_argument('--token', required=True, help='GitHub Personal Access Token')
    parser.add_argument('--repo', required=True, help='GitHub仓库 (username/repo)')
    parser.add_argument('--workflow', default='email-extraction.yml', help='工作流文件名')
    parser.add_argument('--time-range-days', type=int, default=20, help='搜索时间范围（天）')
    parser.add_argument('--wait', action='store_true', help='等待执行完成并获取结果')

    args = parser.parse_args()

    # 创建客户端
    client = GitHubWorkflowClient(token=args.token, repo=args.repo)

    # 触发workflow
    print(f"🚀 触发workflow: {args.workflow}")
    run_id = client.trigger_workflow(
        workflow_file=args.workflow,
        inputs={"time_range_days": str(args.time_range_days)}
    )

    print(f"✅ Workflow已触发")
    print(f"📌 Run ID: {run_id}")
    print(f"🔗 查看详情: https://github.com/{args.repo}/actions/runs/{run_id}")

    # 等待完成
    if args.wait:
        print("⏳ 等待执行完成...")
        outputs = client.get_workflow_outputs(run_id)

        print("\n📊 执行结果:")
        print(json.dumps(outputs, indent=2, ensure_ascii=False))

        return 0 if outputs.get("status") == "true" else 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
```

#### 步骤3.3：创建钉钉通知脚本

创建 [scripts/send_dingtalk_notification.py](../scripts/send_dingtalk_notification.py)：

```python
#!/usr/bin/env python3
"""
发送钉钉通知
"""
import sys
import argparse
import hmac
import hashlib
import base64
import time
import requests
from urllib.parse import quote


def send_dingtalk(webhook_url: str, secret: str, summary: str):
    """发送钉钉消息"""

    # 生成签名
    timestamp = str(round(time.time() * 1000))
    secret_enc = secret.encode('utf-8')
    string_to_sign = f'{timestamp}\n{secret}'
    string_to_sign_enc = string_to_sign.encode('utf-8')
    hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
    sign = quote(base64.b64encode(hmac_code))

    # 构建URL
    url = f"{webhook_url}&timestamp={timestamp}&sign={sign}"

    # 构建消息
    data = {
        "msgtype": "text",
        "text": {
            "content": f"✅ 邮件提取完成\n{summary}"
        }
    }

    # 发送
    response = requests.post(url, json=data)
    response.raise_for_status()

    print("✅ 钉钉通知已发送")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='发送钉钉通知')
    parser.add_argument('--webhook', required=True, help='钉钉Webhook URL')
    parser.add_argument('--secret', required=True, help='钉钉签名密钥')
    parser.add_argument('--summary', required=True, help='摘要信息（JSON字符串）')

    args = parser.parse_args()

    send_dingtalk(args.webhook, args.secret, args.summary)
```

---

## 📊 完成标准

### 必须完成（P0）

- [ ] scripts/extract_emails.py 独立提取脚本
- [ ] .github/workflows/email-extraction.yml 工作流文件
- [ ] GitHub Secrets 配置完成
- [ ] core/github_client.py GitHub API客户端
- [ ] scripts/trigger_workflow.py 触发脚本
- [ ] 手动触发测试通过

### 推荐完成（P1）

- [ ] scripts/github_action_adapter.py 环境适配器
- [ ] scripts/send_dingtalk_notification.py 钉钉通知
- [ ] outputs/results.json.template 输出格式
- [ ] API触发测试通过
- [ ] 完整流程测试通过

### 可选完成（P2）

- [ ] 错误重试机制
- [ ] API限流处理
- [ ] 降级到本地执行
- [ ] 单元测试

---

## ⚠️ 风险点

### 1. GitHub Secrets泄露

**风险**: 敏感信息泄露

**缓解**:
- 使用加密Secrets
- 定期轮换Token
- 限制访问权限

### 2. 执行超时

**风险**: GitHub Actions有6小时超时限制

**缓解**:
- 优化提取逻辑
- 设置合理的time_range_days
- 添加进度日志

### 3. API限流

**风险**: GitHub API有5000次/小时限流

**缓解**:
- 减少轮询频率
- 缓存结果
- 使用webhook回调

---

## 🧪 测试计划

### 单元测试

```bash
# 测试GitHub客户端
python -m pytest tests/test_github_client.py

# 测试提取脚本
python -m pytest tests/test_extract_emails.py
```

### 集成测试

```bash
# 1. 手动触发workflow
gh workflow run email-extraction.yml

# 2. 使用Python脚本触发
python scripts/trigger_workflow.py \
  --token "$GITHUB_TOKEN" \
  --repo "username/repo" \
  --wait
```

### 完整流程测试

```bash
# 触发 -> 等待完成 -> 获取结果 -> 验证数据
```

---

## 🎯 下一步

完成本计划后，可以进入：
- **子计划3**: 本地Docker Web UI控制端

---

**相关文档**:
- [GitHub Actions文档](https://docs.github.com/en/actions)
- [GitHub API文档](https://docs.github.com/en/rest)
- [主计划文件](./bubbly-booping-rossum.md)
