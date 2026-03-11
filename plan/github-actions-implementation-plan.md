# GitHub Actions集成实施计划

**最后更新**: 2026-03-11
**状态**: 阶段0已完成，从阶段1开始执行

---

## 上下文（Context）

### 为什么需要这个改动？

当前项目运行在本地环境，需要手动启动和维护。为了实现以下目标，需要将核心提取逻辑迁移到GitHub Actions：

1. **远程触发执行** - 通过API触发邮件提取，无需本地运行
2. **安全存储敏感信息** - 邮箱密码、钉钉密钥等存储在GitHub Secrets，不暴露在代码中
3. **自动化运行** - 定时或手动触发，无需人工干预
4. **结果返回** - API直接返回JSON格式的提取结果

### 安全架构原则

根据 [architecture/config/sensitive-data.md](../architecture/config/sensitive-data.md) 的指导：

- **绝对禁止**将邮箱密码放在Docker参数、API请求体、日志中传输
- **敏感信息仅存储在GitHub Secrets** - 加密存储，仅在Actions执行时临时解密
- **本地仅传非敏感参数** - 触发指令只包含时间范围、格式等非敏感信息
- **密码仅在GitHub Actions内部使用** - 用完即销毁，不落地、不传输

---

## 推荐方案

### 整体架构

```
本地Docker Web UI → 触发指令（无密码） → GitHub API
                                              ↓
                            GitHub Secrets（邮箱密码）
                                              ↓
                          GitHub Actions执行环境
                                              ↓
                                    邮箱服务器
```

---

## 实施阶段（按优先级）

### 阶段概览

| 阶段 | 名称 | 预计工期 | 优先级 | 状态 |
|------|------|---------|--------|------|
| 0 | 附件重命名功能 | 0.5天 | P0 | ✅ 已完成 |
| 1 | 创建独立提取脚本 | 1-2天 | P0 | 🔵 待执行 |
| 2 | 配置GitHub Secrets | 0.5天 | P0 | 🔵 待执行 |
| 2.5 | 临时文件存储与清理 | 0.5天 | P1 | 🔵 待执行 |
| 3 | 创建GitHub Actions工作流 | 2-3天 | P0 | 🔵 待执行 |
| 4 | 创建GitHub API客户端 | 1-2天 | P0 | 🔵 待执行 |

**总预计工期**：6-9天

---

### ✅ 阶段0：附件重命名功能（已完成）

**状态**: 已实现并测试通过

**实现位置**: [core/email_extractor.py](../core/email_extractor.py) 第56-93行

**功能说明**:
- `_get_unique_filename()` 方法已实现
- 在 `extract_attachments()` 中已调用（第166行）
- 支持序号递增重命名：`invoice.pdf` → `invoice_1.pdf` → `invoice_2.pdf`
- 最多尝试1000次，防止无限循环

---

### 🔵 阶段1：创建独立提取脚本（1-2天）

**目标**：创建不依赖 `main.py` 循环逻辑的独立脚本，用于GitHub Actions单次执行。

#### 步骤1.1：创建独立提取脚本

**文件**: `scripts/extract_emails.py`

**功能要求**:
- 接受命令行参数（时间范围、输出格式）
- 输出JSON格式结果（使用特殊标记包围）
- 独立于 `main.py`，单次执行
- 支持GitHub Actions环境

**代码框架**:
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

        # 输出结果（使用特殊标记包围）
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

#### 步骤1.2：创建GitHub Actions适配器

**文件**: `scripts/github_action_adapter.py`

**功能要求**:
- 验证GitHub Secrets配置
- 设置环境变量
- 错误提示

**代码框架**:
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

### 🔵 阶段2：配置GitHub Secrets（核心任务）⚡

**这是您最关注的部分！**

#### 步骤2.1：创建GitHub仓库（如果还没有）

```bash
# 在GitHub网站上创建新仓库
# 仓库名：expense-reimbursement-email-automation

# 添加远程仓库
git remote add origin https://github.com/your-username/expense-reimbursement-email-automation.git

# 推送代码
git push -u origin master
```

#### 步骤2.2：在GitHub上配置Secrets

**操作路径**：
1. 打开GitHub仓库页面
2. 点击 **Settings**（设置）
3. 左侧菜单点击 **Secrets and variables** → **Actions**
4. 点击 **New repository secret** 按钮添加每个Secret

**必需Secrets（Required）**：

| Secret名称 | 说明 | 示例值 | 获取方式 |
|-----------|------|--------|----------|
| `IMAP_HOST` | IMAP服务器地址 | `imap.qq.com` | 邮箱服务商提供 |
| `IMAP_USER` | 邮箱账号 | `user@qq.com` | 您的邮箱地址 |
| `IMAP_PASS` | 邮箱密码或授权码 | `authorization_code` | 邮箱设置中生成 |

**可选Secrets（Optional）**：

| Secret名称 | 说明 | 示例值 | 获取方式 |
|-----------|------|--------|----------|
| `DINGTALK_WEBHOOK` | 钉钉Webhook URL | `https://oapi.dingtalk.com/robot/send?access_token=xxx` | 钉钉机器人设置 |
| `DINGTALK_SECRET` | 钉钉签名密钥 | `SECxxxxxxxxxxx` | 钉钉机器人安全设置 |

**🔒 安全注意事项**（根据 sensitive-data.md）：

- ✅ **必须**：这些Secrets只存储在GitHub，**绝不**放在本地 `.env` 文件中
- ✅ **必须**：GitHub Secrets采用加密存储，仅在Actions执行时临时解密
- ✅ **必须**：使用授权码/应用专用密码，不要使用邮箱登录密码
- ❌ **禁止**：在代码中硬编码密码
- ❌ **禁止**：在Docker参数中传递密码
- ❌ **禁止**：在日志中打印密码

**常见邮箱配置**：

**QQ邮箱**：
```
IMAP_HOST = imap.qq.com
IMAP_PASS = 授权码（需要在QQ邮箱设置中生成）
```

**163邮箱**：
```
IMAP_HOST = imap.163.com
IMAP_PASS = 授权码（需要在163邮箱设置中生成）
```

**Gmail**：
```
IMAP_HOST = imap.gmail.com
IMAP_PASS = 应用专用密码（需要在Google账户设置中生成）
```

---

### 🔵 阶段2.5：临时文件存储与清理策略（0.5天）

**目标**：定义GitHub Actions环境中的临时文件存储位置和清理机制。

#### 当前文件存储逻辑

**本地环境**（当前实现）：
- **根目录**：`EXTRACT_ROOT_DIR` = `./extracted_mails`（.env配置）
- **子目录结构**：
  ```
  extracted_mails/
  ├── 2026-03-11_070000/          # 时间戳目录
  │   ├── bodies/{rule_id}/       # 邮件正文HTML
  │   ├── attachments/{rule_id}/  # 邮件附件
  │   ├── extracted/{rule_id}/    # 结构化数据（JSON）
  │   └── nuonuo_invoices/{rule_id}/ # 诺诺网发票PDF
  └── data.db                     # SQLite数据库
  ```

**GitHub Actions环境问题**：
- ❌ 每次运行都会创建新的时间戳目录
- ❌ 旧文件不会自动清理，占用磁盘空间
- ❌ GitHub Actions有磁盘空间限制（14GB）
- ❌ 需要手动下载文件，不便于自动化

#### 解决方案设计

**方案A：使用固定临时目录（推荐）**

**存储位置**：
```yaml
# GitHub Actions环境变量
env:
  EXTRACTION_TEMP_DIR: /tmp/extraction_temp  # 临时提取目录
  EXTRACTION_OUTPUT_DIR: /tmp/extraction_output  # 最终输出目录
```

**目录结构**：
```
/tmp/extraction_temp/          # 临时工作目录（每次清空）
├── bodies/{rule_id}/          # 邮件正文
├── attachments/{rule_id}/     # 邮件附件
├── extracted/{rule_id}/       # 结构化数据
└── data.db                    # 临时数据库

/tmp/extraction_output/        # 输出目录（保留到Artifacts）
└── YYYY-MM-DD_HHMMSS/         # 打包的提取结果
    ├── emails/                # 邮件文件
    ├── attachments/           # 附件文件
    └── summary.json           # 提取摘要
```

**清理策略**：
1. **开始时清空临时目录**：
   ```yaml
   - name: Clean temporary directories
     run: |
       rm -rf /tmp/extraction_temp
       mkdir -p /tmp/extraction_temp
   ```

2. **执行时使用临时目录**：
   ```yaml
   - name: Execute email extraction
     env:
       EXTRACT_ROOT_DIR: /tmp/extraction_temp
     run: |
       python scripts/extract_emails.py \
         --time-range-days 20 \
         --output-dir /tmp/extraction_temp
   ```

3. **结束时打包输出**：
   ```yaml
   - name: Package extraction results
     run: |
       TIMESTAMP=$(date +%Y-%m-%d_%H%M%S)
       OUTPUT_DIR="/tmp/extraction_output/$TIMESTAMP"
       mkdir -p "$OUTPUT_DIR"

       # 复制文件到输出目录
       cp -r /tmp/extraction_temp/* "$OUTPUT_DIR/"

       # 生成摘要
       python scripts/generate_summary.py \
         --input-dir "$OUTPUT_DIR" \
         --output "$OUTPUT_DIR/summary.json"
   ```

4. **上传Artifacts**：
   ```yaml
   - name: Upload extraction results
     uses: actions/upload-artifact@v4
     if: always()  # 即使失败也上传
     with:
       name: extraction-results-${{ github.run_id }}
       path: /tmp/extraction_output/
       retention-days: 7  # 保留7天
   ```

5. **清空临时目录**：
   ```yaml
   - name: Clean up temporary files
     if: always()  # 无论成功失败都执行
     run: |
       rm -rf /tmp/extraction_temp
       echo "✅ 临时文件已清空"
   ```

**方案B：使用GitHub Artifacts存储（可选）**

**适用场景**：需要长期保存提取结果

**存储策略**：
- 临时文件：`/tmp/`（运行时自动清理）
- 输出文件：GitHub Artifacts（保留7-90天）
- 数据库：每次重建（无需持久化）

**优点**：
- ✅ 无需手动清理
- ✅ 自动过期删除
- ✅ 可通过API下载

**缺点**：
- ❌ 单个Artifact最大2GB
- ❌ 仓库总存储限制（取决于GitHub套餐）

#### 实现文件

**文件1：`scripts/cleanup_temp_files.py`**

```python
#!/usr/bin/env python3
"""
清理临时文件脚本
用于GitHub Actions环境
"""
import sys
import argparse
import shutil
from pathlib import Path

def cleanup_temp_dirs(temp_dir: Path, keep_output: bool = False):
    """
    清理临时目录

    Args:
        temp_dir: 临时目录路径
        keep_output: 是否保留输出目录
    """
    if not temp_dir.exists():
        print(f"临时目录不存在：{temp_dir}")
        return

    # 清理子目录
    for subdir in ["bodies", "attachments", "extracted", "nuonuo_invoices"]:
        subdir_path = temp_dir / subdir
        if subdir_path.exists():
            shutil.rmtree(subdir_path)
            print(f"✅ 已清理：{subdir_path}")

    # 清理数据库
    db_file = temp_dir / "data.db"
    if db_file.exists():
        db_file.unlink()
        print(f"✅ 已清理：{db_file}")

    if not keep_output:
        # 清理整个临时目录
        shutil.rmtree(temp_dir)
        print(f"✅ 已清空临时目录：{temp_dir}")
    else:
        print(f"⏸️  保留输出目录：{temp_dir}")

def main():
    parser = argparse.ArgumentParser(description='清理临时文件')
    parser.add_argument('--temp-dir', default='/tmp/extraction_temp', help='临时目录路径')
    parser.add_argument('--keep-output', action='store_true', help='保留输出目录')

    args = parser.parse_args()

    temp_dir = Path(args.temp_dir)
    cleanup_temp_dirs(temp_dir, args.keep_output)

    return 0

if __name__ == "__main__":
    sys.exit(main())
```

**文件2：`scripts/package_results.py`**

```python
#!/usr/bin/env python3
"""
打包提取结果
用于上传到GitHub Artifacts
"""
import sys
import argparse
import shutil
import json
from pathlib import Path
from datetime import datetime

def package_results(source_dir: Path, output_base_dir: Path) -> Path:
    """
    打包提取结果

    Args:
        source_dir: 源目录（临时提取目录）
        output_base_dir: 输出基础目录

    Returns:
        Path: 输出目录路径
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    output_dir = output_base_dir / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)

    # 复制文件
    if source_dir.exists():
        # 复制邮件文件
        for category in ["bodies", "attachments", "extracted", "nuonuo_invoices"]:
            src = source_dir / category
            if src.exists():
                dst = output_dir / category
                shutil.copytree(src, dst)
                print(f"✅ 已复制：{category}")

        # 生成摘要
        summary = {
            "timestamp": timestamp,
            "total_files": sum(len(list(output_dir.rglob("*"))) - 1 for _ in [0]),
            "categories": []
        }

        for category in ["bodies", "attachments", "extracted", "nuonuo_invoices"]:
            cat_dir = output_dir / category
            if cat_dir.exists():
                file_count = len(list(cat_dir.rglob("*")))
                summary["categories"].append({
                    "name": category,
                    "file_count": file_count
                })

        summary_file = output_dir / "summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        print(f"✅ 已生成摘要：{summary_file}")
    else:
        print(f"⚠️  源目录不存在：{source_dir}")

    return output_dir

def main():
    parser = argparse.ArgumentParser(description='打包提取结果')
    parser.add_argument('--source-dir', required=True, help='源目录路径')
    parser.add_argument('--output-dir', default='/tmp/extraction_output', help='输出目录路径')

    args = parser.parse_args()

    source_dir = Path(args.source_dir)
    output_base_dir = Path(args.output_dir)

    output_dir = package_results(source_dir, output_base_dir)

    print(f"\n📦 打包完成：{output_dir}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
```

#### GitHub Actions工作流集成

```yaml
jobs:
  extract-emails:
    runs-on: ubuntu-latest

    steps:
      # ... 前面的步骤 ...

      # 1. 清理临时目录
      - name: Clean temporary directories
        run: |
          rm -rf /tmp/extraction_temp
          mkdir -p /tmp/extraction_temp

      # 2. 执行提取（使用临时目录）
      - name: Execute email extraction
        env:
          EXTRACT_ROOT_DIR: /tmp/extraction_temp
        run: |
          python scripts/extract_emails.py \
            --time-range-days 20 \
            --output-dir /tmp/extraction_temp

      # 3. 打包结果
      - name: Package extraction results
        run: |
          python scripts/package_results.py \
            --source-dir /tmp/extraction_temp \
            --output-dir /tmp/extraction_output

      # 4. 上传Artifacts
      - name: Upload extraction results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: extraction-results-${{ github.run_id }}
          path: /tmp/extraction_output/
          retention-days: 7

      # 5. 清理临时文件
      - name: Clean up temporary files
        if: always()
        run: |
          python scripts/cleanup_temp_files.py \
            --temp-dir /tmp/extraction_temp
          echo "✅ 临时文件已清空"
```

#### 磁盘空间监控

**添加磁盘空间检查**：
```yaml
- name: Check disk space
        run: |
          echo "磁盘使用情况："
          df -h

          echo "临时目录大小："
          du -sh /tmp/extraction_temp || echo "目录不存在"
```

#### 下载Artifacts的方法

**方法1：GitHub网页界面**
1. 打开仓库的 **Actions** 标签
2. 点击具体的运行记录
3. 滚动到页面底部的 **Artifacts** 区域
4. 点击下载

**方法2：GitHub CLI**
```bash
# 列出Artifacts
gh run view <run-id> --log

# 下载Artifact
gh run download <run-id> -n extraction-results-<run-id>
```

**方法3：API下载**
```python
import requests

def download_artifact(repo: str, run_id: str, artifact_name: str, token: str):
    """下载GitHub Artifact"""
    url = f"https://api.github.com/repos/{repo}/actions/runs/{run_id}/artifacts"
    headers = {"Authorization": f"token {token}"}

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    artifacts = response.json()["artifacts"]
    for artifact in artifacts:
        if artifact["name"] == artifact_name:
            download_url = artifact["archive_download_url"]
            r = requests.get(download_url, headers=headers)
            r.raise_for_status()

            with open(f"{artifact_name}.zip", 'wb') as f:
                f.write(r.content)

            print(f"✅ 已下载：{artifact_name}.zip")
            break
```

#### 清理策略对比

| 策略 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| **自动清理（推荐）** | 无需手动干预<br/>节省磁盘空间 | 需要上传Artifacts | GitHub Actions |
| **保留本地** | 文件立即可用<br/>无需下载 | 占用磁盘空间<br/>需手动清理 | 本地开发 |
| **混合策略** | 灵活性高 | 实现复杂 | 生产环境 |

#### 最佳实践建议

1. **临时目录使用 `/tmp/`**
   - ✅ GitHub Actions自动清理
   - ✅ 不占用workspace空间

2. **输出目录使用Artifacts**
   - ✅ 自动过期删除
   - ✅ 可通过API访问
   - ✅ 支持大文件（最大2GB）

3. **数据库每次重建**
   - ✅ 无需持久化
   - ✅ 避免数据不一致

4. **添加磁盘空间检查**
   - ✅ 提前发现问题
   - ✅ 便于调试

5. **日志文件保留**
   - ✅ 失败时上传日志
   - ✅ 便于问题排查

---

### 🔵 阶段3：创建GitHub Actions工作流（2-3天）

#### 步骤3.1：创建工作流文件

**文件**: `.github/workflows/email-extraction.yml`

**功能要求**:
1. **触发方式**：
   - `workflow_dispatch` - 手动触发（可在GitHub网页界面点击运行）
   - `repository_dispatch` - API触发（通过GitHub API远程调用）

2. **输入参数**：
   - `time_range_days` : 搜索时间范围（7/20/30天）
   - `rule_filter` : 规则ID过滤器（逗号分隔，留空表示全部）

3. **环境变量**（从GitHub Secrets读取）：
   ```yaml
   env:
     IMAP_HOST: ${{ secrets.IMAP_HOST }}
     IMAP_USER: ${{ secrets.IMAP_USER }}
     IMAP_PASS: ${{ secrets.IMAP_PASS }}
     DINGTALK_WEBHOOK: ${{ secrets.DINGTALK_WEBHOOK }}
     DINGTALK_SECRET: ${{ secrets.DINGTALK_SECRET }}
   ```

4. **执行步骤**：
   - Checkout代码
   - 设置Python环境
   - 安装系统依赖（p7zip、unrar等）
   - 安装Python依赖
   - 执行提取脚本
   - 生成输出（summary、detail、status）
   - 发送钉钉通知（如果配置）
   - 上传日志（如果失败）

5. **输出结果**：
   - `summary` : 提取摘要（匹配数量、执行时间）
   - `detail` : 详细结果（JSON格式）
   - `status` : 执行状态（success/failure）
   - `executed_at` : 执行时间戳

**代码框架**:
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

---

### 🔵 阶段4：创建GitHub API客户端（1-2天）

#### 步骤4.1：创建GitHub API客户端

**文件**: `core/github_client.py`

**功能要求**:
- `trigger_workflow()` - 触发workflow
- `get_workflow_status()` - 查询状态
- `get_workflow_outputs()` - 获取结果

**代码框架**:
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
```

#### 步骤4.2：创建触发脚本

**文件**: `scripts/trigger_workflow.py`

**功能要求**:
- 接受命令行参数
- 触发workflow
- 可选：等待完成并获取结果

**代码框架**:
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

#### 步骤4.3：创建钉钉通知脚本

**文件**: `scripts/send_dingtalk_notification.py`

**功能要求**:
- 生成签名（HMAC-SHA256）
- 发送消息到钉钉

**代码框架**:
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

## 关键文件清单

### 需要创建的文件

| 文件路径 | 用途 | 优先级 | 阶段 | 状态 |
|---------|------|--------|------|------|
| `scripts/extract_emails.py` | 独立提取脚本 | P0 | 阶段1 | 🔵 待创建 |
| `scripts/github_action_adapter.py` | 环境适配器 | P1 | 阶段1 | 🔵 待创建 |
| `scripts/cleanup_temp_files.py` | 清理临时文件 | P1 | 阶段2.5 | 🔵 待创建 |
| `scripts/package_results.py` | 打包提取结果 | P1 | 阶段2.5 | 🔵 待创建 |
| `.github/workflows/email-extraction.yml` | GitHub Actions工作流 | P0 | 阶段3 | 🔵 待创建 |
| `core/github_client.py` | GitHub API客户端 | P0 | 阶段4 | 🔵 待创建 |
| `scripts/trigger_workflow.py` | 触发工具 | P0 | 阶段4 | 🔵 待创建 |
| `scripts/send_dingtalk_notification.py` | 钉钉通知 | P1 | 阶段4 | 🔵 待创建 |
| `outputs/results.json.template` | 输出格式模板 | P2 | 阶段1 | 🔵 待创建 |

### 已完成的文件

| 文件路径 | 功能 | 状态 |
|---------|------|------|
| `core/email_extractor.py` | 附件重命名功能 | ✅ 已完成（第56-93行） |

---

## 验证步骤

### 1. 本地测试独立脚本

```bash
# 测试提取脚本
python scripts/extract_emails.py \
  --time-range-days 7 \
  --output-dir /tmp/test_extraction
```

**预期结果**：
- 输出JSON格式结果
- 文件保存到指定目录
- 无错误退出

### 2. GitHub Secrets配置验证

在GitHub Actions工作流中添加配置验证步骤：

```yaml
- name: Verify Secrets
  run: |
    python scripts/github_action_adapter.py
```

**预期结果**：
- ✅ GitHub Secrets配置验证通过
- ❌ 缺少必需的Secrets: xxx

### 3. 手动触发工作流

**方法1：GitHub网页界面**
1. 打开仓库的 **Actions** 标签
2. 选择 **Email Extraction** 工作流
3. 点击 **Run workflow**
4. 选择参数并运行

**方法2：GitHub CLI**
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

**预期结果**：
- Workflow成功执行
- 输出包含提取的邮件数量
- 无错误日志

### 4. API触发测试

```bash
# 使用Python脚本触发
python scripts/trigger_workflow.py \
  --token "$GITHUB_TOKEN" \
  --repo "username/expense-reimbursement-email-automation" \
  --time-range-days 20 \
  --wait
```

**预期结果**：
- 返回 `success: true`
- 包含 `matched_count` 字段
- 钉钉收到通知（如果配置）

### 5. 完整流程测试

```bash
# 1. 发送测试邮件到邮箱
# 2. 触发workflow
# 3. 等待完成
# 4. 检查输出结果
# 5. 验证钉钉通知
# 6. 下载Artifacts（如果有）
```

---

## 风险点与缓解

### 风险1：GitHub Secrets泄露

**风险等级**：🔴 高

**缓解措施**：
- 使用最小权限的GitHub Personal Access Token
- 定期轮换Secrets
- 启用GitHub仓库的"Secrets扫描"功能
- 不要在日志中打印Secrets

### 风险2：执行超时

**风险等级**：🟡 中

**GitHub Actions限制**：6小时超时

**缓解措施**：
- 优化提取逻辑
- 设置合理的 `time_range_days`（不超过30天）
- 添加进度日志
- 考虑分批提取

### 风险3：API限流

**风险等级**：🟡 中

**GitHub API限制**：5000次/小时

**缓解措施**：
- 减少轮询频率（每10-30秒查询一次）
- 使用webhook回调代替轮询
- 缓存结果

---

## 完成标准（Definition of Done）

### P0（必须完成）

- [ ] GitHub Secrets已配置（IMAP_HOST、IMAP_USER、IMAP_PASS）
- [ ] scripts/extract_emails.py 独立提取脚本已创建
- [ ] scripts/cleanup_temp_files.py 清理脚本已创建
- [ ] scripts/package_results.py 打包脚本已创建
- [ ] .github/workflows/email-extraction.yml 工作流文件已创建
- [ ] core/github_client.py GitHub API客户端已创建
- [ ] scripts/trigger_workflow.py 触发脚本已创建
- [ ] 手动触发测试通过（GitHub网页界面）
- [ ] API触发测试通过（Python脚本）
- [ ] 临时文件自动清理测试通过

### P1（推荐完成）

- [ ] scripts/github_action_adapter.py 环境适配器已创建
- [ ] scripts/send_dingtalk_notification.py 钉钉通知已创建
- [ ] outputs/results.json.template 输出格式模板已创建
- [ ] Artifacts上传测试通过
- [ ] Artifacts下载测试通过
- [ ] 磁盘空间监控已添加
- [ ] 完整流程测试通过（触发→执行→清理→通知）

### P2（可选完成）

- [ ] 错误重试机制
- [ ] API限流处理
- [ ] 降级到本地执行
- [ ] 单元测试覆盖率 >80%
- [ ] 自动清理策略优化

---

## 后续步骤

完成本计划后，可以进入：
- **子计划3**：本地Docker Web UI控制端（可视化界面）

---

## 参考资料

- [GitHub Actions文档](https://docs.github.com/en/actions)
- [GitHub API文档](https://docs.github.com/en/rest)
- [敏感信息安全管控](../architecture/config/sensitive-data.md)
- [子计划2详细文档](./subplan-2-github-actions.md)
- [部署架构文档](../architecture/deployment.md)
