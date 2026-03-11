# 附件重命名功能说明

**最后更新**: 2026-03-11

---

## 📋 需求背景

在实际使用中，经常会遇到以下情况：
- **多个邮件有相同名称的附件**
  - 例如：3个不同的12306订单邮件，都有 `发票.pdf` 附件
  - 如果不重命名，后面的会覆盖前面的，导致数据丢失

### 当前问题

在 `core/email_extractor.py` 的第127行：
```python
# 保存附件
filepath = rule_dir / filename
```

直接使用原始文件名，如果文件已存在会被覆盖。

---

## 🎯 解决方案

### 重命名策略

**序号递增**（根据您的选择）：
```
invoice.pdf  (第1个邮件)
invoice_1.pdf (第2个邮件，文件名冲突)
invoice_2.pdf (第3个邮件，文件名冲突)
```

### 重命名时机

**仅冲突时重命名**（根据您的选择）：
- 如果文件不存在 → 使用原始文件名
- 如果文件已存在 → 添加序号后缀

### 应用范围

- ✅ **附件文件**：PDF、图片、Word、Excel等
- ✅ **压缩包文件**：zip、rar、7z等
- ❌ **压缩包内文件**：保持原样，不重命名

---

## 🔧 实现方式

### 1. 修改 `EmailExtractor` 类

在 [core/email_extractor.py](../core/email_extractor.py) 中添加新方法：

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

### 2. 修改 `extract_attachments` 方法

在 `extract_attachments` 方法中调用重命名逻辑：

```python
def extract_attachments(self, msg, rule_id, extraction_dir, message_id):
    """提取并保存邮件附件（支持文件重命名）"""
    rule_dir = extraction_dir / "attachments" / rule_id
    rule_dir.mkdir(parents=True, exist_ok=True)

    # ... 前面代码不变 ...

    for part in msg.walk():
        # ... 检查是否为附件 ...

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

---

## 🧪 测试验证

### 单元测试

创建 [tests/test_attachment_rename.py](../tests/test_attachment_rename.py)：

```python
"""
测试附件重命名功能
"""
import pytest
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

### 手动测试

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

## 📊 文件结构示例

### 提取前的邮件

```
邮件1: 订单A123 → 附件: 发票.pdf
邮件2: 订单B456 → 附件: 发票.pdf
邮件3: 订单C789 → 附件: 发票.pdf
```

### 提取后的目录结构

```
extracted_mails/2026-03-11_120000/
└── attachments/
    └── rule_002/
        ├── 发票.pdf        # 邮件1的附件
        ├── 发票_1.pdf      # 邮件2的附件（重命名）
        └── 发票_2.pdf      # 邮件3的附件（重命名）
```

---

## 🔍 日志输出

### 正常重命名日志

```
【提取器】发现附件：发票.pdf
【提取器】文件重命名：发票.pdf → 发票_1.pdf
【提取器】保存附件：.../attachments/rule_002/发票_1.pdf
```

### 无冲突日志

```
【提取器】发现附件：合同.pdf
【提取器】保存附件：.../attachments/rule_002/合同.pdf
```

---

## ⚠️ 注意事项

### 1. 压缩包处理

- ✅ 压缩包文件本身会重命名（如 `附件.zip` → `附件_1.zip`）
- ❌ 压缩包**内部**的文件不会重命名
- 解压后的文件存放在嵌套目录中（如 `附件.zip_extracted/`）

### 2. 文件名限制

- 最多支持 1000 个冲突文件（超出会报错）
- 如果某个附件超过1000个冲突，会抛出异常

### 3. 性能影响

- 重命名逻辑仅在有冲突时才会执行
- 对性能影响很小（仅文件存在性检查）

---

## 🎯 后续优化（可选）

### 1. 配置化重命名策略

如果将来需要其他重命名策略，可以在规则配置中添加：

```json
{
  "rule_id": "rule_002",
  "rename_strategy": "sequence",  // 序号递增
  "rename_alternatives": ["timestamp", "sender_date"]  // 其他策略
}
```

### 2. 记录原始文件名

在数据库中记录原始文件名和重命名后的文件名映射：

```python
# 数据库记录
{
    "original_filename": "发票.pdf",
    "saved_filename": "发票_1.pdf",
    "mail_date": "2026-03-11 10:00:00"
}
```

---

## 📞 相关文档

- [子计划2：GitHub Actions集成](./subplan-2-github-actions.md)
- [子计划索引](./subplan-index.md)
- [主项目文档](../CLAUDE.md)
