# 子计划1：本地功能测试与验证

**目标**: 在本地环境测试和验证邮箱提取功能，为GitHub Actions部署做准备

**预计工期**: 1-2天

---

## 📋 执行步骤

### 阶段1：本地环境准备（0.5天）

#### 步骤1.1：检查Python环境

```bash
# 检查Python版本（需要3.9+）
python --version

# 检查pip
pip --version
```

**预期结果**:
- Python版本 >= 3.9
- pip可用

#### 步骤1.2：安装项目依赖

```bash
# 创建虚拟环境（推荐）
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

#### 步骤1.3：创建配置文件

```bash
# 复制或创建.env文件
cp .env.example .env

# 编辑.env，填写邮箱配置
# IMAP_HOST=imap.qq.com
# IMAP_USER=your_email@qq.com
# IMAP_PASS=your_authorization_code
# ... 其他配置
```

#### 步骤1.4：验证规则文件

```bash
# 检查规则文件是否存在
ls -la rules/parse_rules.json

# 查看规则内容
cat rules/parse_rules.json | python -m json.tool
```

**预期结果**:
- 规则文件存在
- JSON格式正确

---

### 阶段2：附件重命名功能测试（0.5天）🆕

#### 步骤2.1：修改附件提取逻辑

在 [core/email_extractor.py](../core/email_extractor.py) 中添加 `_get_unique_filename` 方法：

```python
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

#### 步骤2.2：修改extract_attachments方法

在 `extract_attachments` 方法中使用重命名逻辑：

```python
def extract_attachments(self, msg, rule_id, extraction_dir, message_id):
    """提取并保存邮件附件（支持文件重命名）"""
    rule_dir = extraction_dir / "attachments" / rule_id
    rule_dir.mkdir(parents=True, exist_ok=True)

    attachments = []
    attachment_count = 0

    for part in msg.walk():
        # ... 检查是否为附件的代码 ...

        if filename:
            filename = self._decode_filename(filename)

            # 🆕 使用重命名逻辑
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
```

#### 步骤2.3：创建单元测试

创建 [tests/test_attachment_rename.py](../tests/test_attachment_rename.py)：

```python
"""
测试附件重命名功能
"""
import tempfile
import shutil
from pathlib import Path
from core.email_extractor import EmailExtractor

def test_unique_filename_generation():
    """测试唯一文件名生成"""
    extractor = EmailExtractor()

    # 创建临时目录
    with tempfile.TemporaryDirectory() as test_dir:
        test_path = Path(test_dir)

        # 场景1: 文件不存在，使用原文件名
        result1 = extractor._get_unique_filename(test_path, "invoice.pdf")
        assert result1 == test_path / "invoice.pdf"
        print("✅ 场景1通过: 文件不存在，使用原文件名")

        # 创建文件
        (test_path / "invoice.pdf").touch()

        # 场景2: 文件已存在，添加序号
        result2 = extractor._get_unique_filename(test_path, "invoice.pdf")
        assert result2 == test_path / "invoice_1.pdf"
        print("✅ 场景2通过: 文件已存在，重命名为 invoice_1.pdf")

        # 创建第二个文件
        (test_path / "invoice_1.pdf").touch()

        # 场景3: 继续递增
        result3 = extractor._get_unique_filename(test_path, "invoice.pdf")
        assert result3 == test_path / "invoice_2.pdf"
        print("✅ 场景3通过: 继续递增为 invoice_2.pdf")

        # 场景4: 不同文件名，不冲突
        result4 = extractor._get_unique_filename(test_path, "contract.pdf")
        assert result4 == test_path / "contract.pdf"
        print("✅ 场景4通过: 不同文件名不冲突")

    print("\n✅ 所有测试通过！")

if __name__ == "__main__":
    test_unique_filename_generation()
```

#### 步骤2.4：运行测试

```bash
# 运行测试
python tests/test_attachment_rename.py

# 预期输出
# ✅ 场景1通过: 文件不存在，使用原文件名
# ✅ 场景2通过: 文件已存在，重命名为 invoice_1.pdf
# ✅ 场景3通过: 继续递增为 invoice_2.pdf
# ✅ 场景4通过: 不同文件名不冲突
# ✅ 所有测试通过！
```

---

### 阶段3：本地提取功能测试（0.5天）

#### 步骤3.1：创建测试脚本

创建 [scripts/test_local_extraction.py](../scripts/test_local_extraction.py)：

```python
#!/usr/bin/env python3
"""
本地邮箱提取测试脚本
"""
import sys
import logging
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.logger_config import init_logger
from core.email_fetcher import fetch_reimbursement_mails
from core.database import DatabaseManager

def main():
    """测试本地邮箱提取功能"""

    # 初始化日志
    logger = init_logger()
    logger.info("🧪 开始本地提取测试...")

    # 初始化数据库
    db_path = Path("./extracted_mails/data.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db = DatabaseManager(str(db_path))

    try:
        # 拉取邮件
        logger.info("📧 开始拉取邮件...")
        matched_mails = fetch_reimbursement_mails(
            logger_instance=logger,
            db_manager=db
        )

        # 显示结果
        logger.info(f"✅ 匹配到 {len(matched_mails)} 封邮件")

        for i, mail in enumerate(matched_mails, 1):
            logger.info(f"邮件 {i}: {mail['subject']}")
            logger.info(f"  发件人: {mail['sender']}")
            logger.info(f"  匹配规则: {[r.rule_name for r in mail['matched_rules']]}")

        # 统计信息
        stats = db.get_statistics()
        logger.info(f"📊 统计信息:")
        logger.info(f"  总邮件数: {stats['total_emails']}")
        logger.info(f"  历史记录: {stats['total_history']}")

        logger.info("✅ 本地提取测试完成")

    except Exception as e:
        logger.error(f"❌ 提取失败: {e}", exc_info=True)
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
```

#### 步骤3.2：运行测试

```bash
# 确保虚拟环境已激活
# 然后运行测试
python scripts/test_local_extraction.py
```

**预期结果**:
```
🧪 开始本地提取测试...
📧 开始拉取邮件...
✅ 匹配到 X 封邮件
邮件 1: 12306订单通知
  发件人: 12306@12306.cn
  匹配规则: 12306提取
...
✅ 本地提取测试完成
```

---

### 阶段4：验证提取结果（0.5天）

#### 步骤4.1：检查文件结构

```bash
# 查看提取目录
ls -la extracted_mails/

# 查看附件目录
ls -la extracted_mails/*/attachments/

# 查看数据库文件
ls -la extracted_mails/data.db
```

#### 步骤4.2：验证附件重命名

```bash
# 检查是否有重命名的文件
# 应该看到类似 invoice_1.pdf, invoice_2.pdf 的文件
find extracted_mails/*/attachments/ -name "*_*.pdf" -o -name "*_*.png"
```

#### 步骤4.3：查看数据库记录

```python
# 创建简单的查询脚本
python -c "
from core.database import DatabaseManager
db = DatabaseManager('./extracted_mails/data.db')
stats = db.get_statistics()
print(f'总邮件数: {stats[\"total_emails\"]}')
print(f'历史记录: {stats[\"total_history\"]}')
"
```

---

## 📊 完成标准

### 必须完成（P0）

- [ ] Python环境准备完成
- [ ] 依赖安装成功
- [ ] 配置文件创建（.env）
- [ ] 规则文件验证通过
- [ ] 附件重命名功能实现
- [ ] 附件重命名测试通过
- [ ] 本地提取测试成功
- [ ] 提取结果验证完成

### 推荐完成（P1）

- [ ] 创建测试脚本
- [ ] 数据库记录验证
- [ ] 文件结构检查
- [ ] 错误处理测试

---

## ⚠️ 常见问题

### 问题1: 依赖安装失败

**症状**: `pip install` 报错

**解决方案**:
```bash
# 升级pip
python -m pip install --upgrade pip

# 使用国内镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 问题2: 邮箱连接失败

**症状**: IMAP连接被拒绝

**解决方案**:
- 检查IMAP_HOST是否正确
- 检查IMAP端口是否开放
- 检查邮箱是否开启了IMAP服务
- 检查是否使用授权码（而非密码）

### 问题3: 附件重命名不生效

**症状**: 文件仍然被覆盖

**解决方案**:
- 确认 `_get_unique_filename` 方法已添加
- 确认 `extract_attachments` 方法调用了重命名逻辑
- 查看日志确认重命名逻辑被触发

---

## 🎯 验证清单

执行以下命令验证本地功能：

```bash
# 1. 环境检查
python --version  # >= 3.9
pip --version

# 2. 依赖检查
pip list | grep -E "(pytz|requests|)"

# 3. 配置检查
ls -la .env
ls -la rules/parse_rules.json

# 4. 运行附件重命名测试
python tests/test_attachment_rename.py

# 5. 运行本地提取测试
python scripts/test_local_extraction.py

# 6. 检查提取结果
ls -la extracted_mails/*/attachments/
```

---

## 📝 与后续计划的衔接

### 完成本计划后

本地测试通过后，可以继续：
- **子计划2**: 将本地验证过的代码上传到GitHub Actions
- **子计划3**: 开发Web UI控制端（可选）

### 关键衔接点

1. **附件重命名功能**
   - 本地测试通过后，GitHub Actions中也会使用相同逻辑
   - 确保在GitHub环境中也能正常工作

2. **环境变量配置**
   - 本地使用的 `.env` 配置
   - 迁移到GitHub Secrets中

3. **提取逻辑**
   - 本地验证通过的核心逻辑
   - 独立为脚本供GitHub Actions调用

---

## 🚀 快速开始

### 一键测试脚本

创建 [scripts/test_all.sh](../scripts/test_all.sh)：

```bash
#!/bin/bash
# 本地功能一键测试脚本

echo "🧪 开始本地功能测试..."
echo ""

echo "1️⃣ 环境检查..."
python --version
if [ $? -ne 0 ]; then
    echo "❌ Python未安装或版本不符合要求"
    exit 1
fi
echo "✅ Python环境正常"
echo ""

echo "2️⃣ 附件重命名测试..."
python tests/test_attachment_rename.py
if [ $? -ne 0 ]; then
    echo "❌ 附件重命名测试失败"
    exit 1
fi
echo ""

echo "3️⃣ 本地提取测试..."
python scripts/test_local_extraction.py
if [ $? -ne 0 ]; then
    echo "❌ 本地提取测试失败"
    exit 1
fi
echo ""

echo "✅ 所有测试通过！"
echo "📊 提取结果位置: extracted_mails/"
echo "📊 数据库文件: extracted_mails/data.db"
```

**使用方式**:
```bash
chmod +x scripts/test_all.sh
./scripts/test_all.sh
```

---

## 📞 相关文档

- [子计划2：GitHub Actions集成](./subplan-2-github-actions.md)
- [子计划3：Web UI控制端](./subplan-3-web-ui.md)
- [子计划索引](./subplan-index.md)
- [附件重命名功能说明](../docs/ATTACHMENT_RENAMING.md)
- [主项目文档](../CLAUDE.md)
