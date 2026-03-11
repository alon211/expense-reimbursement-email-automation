# API 接口文档

**最后更新**: 2026-03-11

本文档提供项目中所有公共 API 接口的详细说明，包括函数签名、参数、返回值和使用示例。

---

## 目录

1. [DatabaseManager API](#databasemanager-api)
2. [RuleLoader API](#ruleloader-api)
3. [Rule API](#rule-api)
4. [EmailExtractor API](#emailextractor-api)
5. [钉钉通知 API](#钉钉通知-api)
6. [工具函数 API](#工具函数-api)

---

## DatabaseManager API

**模块**: [core/database.py](../core/database.py)

### 初始化

```python
DatabaseManager(db_path: str)
```

**参数**:
- `db_path` (str): 数据库文件路径

**返回**: DatabaseManager 实例

**示例**:
```python
from core.database import DatabaseManager

db = DatabaseManager("./data.db")
```

---

### add_extracted_email()

添加新邮件记录到数据库。

```python
def add_extracted_email(self, email_record: ExtractedEmail) -> int:
    """
    添加新邮件记录

    Args:
        email_record: ExtractedEmail 对象

    Returns:
        int: 新插入记录的 ID

    Raises:
        sqlite3.IntegrityError: 如果 message_id 已存在
    """
```

**参数**:
- `email_record` (ExtractedEmail): 邮件记录对象

**返回**: `int` - 新插入记录的 ID

**异常**:
- `sqlite3.IntegrityError`: 如果 message_id 已存在

**示例**:
```python
from core.database import DatabaseManager
from core.models import ExtractedEmail
from datetime import datetime

db = DatabaseManager("./data.db")

email_record = ExtractedEmail(
    message_id="<test@example.com>",
    subject="测试邮件",
    sender="sender@example.com",
    rule_id="rule_001",
    mail_date="2026-03-11 10:00:00",
    extracted_at=datetime.now(),
    storage_path="./extracted_mails/2026-03-11_100000",
    attachment_count=1,
    body_file_path="./extracted_mails/.../bodies/rule_001/xxx.html"
)

record_id = db.add_extracted_email(email_record)
print(f"新记录 ID: {record_id}")
```

---

### update_extracted_email()

更新已存在的邮件记录。

```python
def update_extracted_email(self, email_record: ExtractedEmail) -> bool:
    """
    更新已存在的邮件记录

    Args:
        email_record: ExtractedEmail 对象（必须包含有效的 id 或 message_id）

    Returns:
        bool: 更新是否成功
    """
```

**参数**:
- `email_record` (ExtractedEmail): 邮件记录对象

**返回**: `bool` - 更新是否成功

**示例**:
```python
from core.database import DatabaseManager
from core.models import ExtractedEmail

db = DatabaseManager("./data.db")

# 获取现有记录
email_record = db.get_extracted_email("<test@example.com>")

# 更新字段
email_record.attachment_count = 5

# 保存更新
success = db.update_extracted_email(email_record)
```

---

### get_existing_mail_dates()

获取所有已提取且文件存在的邮件发送时间集合（用于去重）。

```python
def get_existing_mail_dates(self) -> set:
    """
    获取所有已提取且文件存在的邮件发送时间集合
    用于快速去重检查，避免重复提取

    Returns:
        set: 邮件发送时间集合（mail_date）

    Note:
        此方法会自动清理文件不存在的记录
    """
```

**返回**: `set` - 邮件发送时间集合（mail_date）

**注意**: 此方法会自动清理文件不存在的记录

**示例**:
```python
from core.database import DatabaseManager

db = DatabaseManager("./data.db")

# 获取已提取邮件的发送时间集合
existing_dates = db.get_existing_mail_dates()

# 去重检查
mail_date = "2026-03-11 10:00:00"
if mail_date in existing_dates:
    print("邮件已提取，跳过")
else:
    print("新邮件，继续提取")
```

---

### is_email_extracted()

检查邮件是否已提取（基础版本，只检查数据库）。

```python
def is_email_extracted(self, message_id: str) -> bool:
    """
    检查邮件是否已提取（基础版本）

    Args:
        message_id: 邮件 Message-ID

    Returns:
        bool: True 如果已提取，否则 False
    """
```

**参数**:
- `message_id` (str): 邮件 Message-ID

**返回**: `bool` - True 如果已提取，否则 False

**示例**:
```python
from core.database import DatabaseManager

db = DatabaseManager("./data.db")

if db.is_email_extracted("<test@example.com>"):
    print("邮件已提取")
```

---

### is_email_extracted_with_files()

检查邮件是否已提取（增强版本，验证文件实际存在）。

```python
def is_email_extracted_with_files(self, message_id: str) -> bool:
    """
    检查邮件是否已提取（增强版本，验证文件实际存在）

    Args:
        message_id: 邮件 Message-ID

    Returns:
        bool: True 如果已提取且文件存在，否则 False
    """
```

**参数**:
- `message_id` (str): 邮件 Message-ID

**返回**: `bool` - True 如果已提取且文件存在，否则 False

**示例**:
```python
from core.database import DatabaseManager

db = DatabaseManager("./data.db")

# 增强版检查（验证文件存在）
if db.is_email_extracted_with_files("<test@example.com>"):
    print("邮件已提取且文件完整")
```

---

### get_extracted_email()

根据 Message-ID 获取邮件记录。

```python
def get_extracted_email(self, message_id: str) -> Optional[ExtractedEmail]:
    """
    根据 Message-ID 获取邮件记录

    Args:
        message_id: 邮件 Message-ID

    Returns:
        ExtractedEmail 对象，如果不存在则返回 None
    """
```

**参数**:
- `message_id` (str): 邮件 Message-ID

**返回**: `ExtractedEmail` 对象，如果不存在则返回 `None`

**示例**:
```python
from core.database import DatabaseManager

db = DatabaseManager("./data.db")

email_record = db.get_extracted_email("<test@example.com>")

if email_record:
    print(f"主题: {email_record.subject}")
    print(f"发件人: {email_record.sender}")
```

---

### add_extraction_history()

添加提取历史记录。

```python
def add_extraction_history(self, history: ExtractionHistory) -> int:
    """
    添加提取历史记录

    Args:
        history: ExtractionHistory 对象

    Returns:
        int: 新插入记录的 ID
    """
```

**参数**:
- `history` (ExtractionHistory): 提取历史对象

**返回**: `int` - 新插入记录的 ID

**示例**:
```python
from core.database import DatabaseManager
from core.models import ExtractionHistory
from datetime import datetime

db = DatabaseManager("./data.db")

history = ExtractionHistory(
    message_id="<test@example.com>",
    rule_id="rule_001",
    action="matched",
    created_at=datetime.now()
)

history_id = db.add_extraction_history(history)
```

---

### get_statistics()

获取数据库统计信息。

```python
def get_statistics(self) -> dict:
    """
    获取数据库统计信息

    Returns:
        dict: 包含以下键的字典:
            - total_emails: 总邮件数
            - total_attachments: 总附件数
            - unique_senders: 唯一发件人数
            - rules_used: 使用的规则数
    """
```

**返回**: `dict` - 统计信息字典

**示例**:
```python
from core.database import DatabaseManager

db = DatabaseManager("./data.db")

stats = db.get_statistics()
print(f"总邮件数: {stats['total_emails']}")
print(f"总附件数: {stats['total_attachments']}")
print(f"唯一发件人: {stats['unique_senders']}")
```

---

### clear_all_data()

清空所有数据。

```python
def clear_all_data(self) -> bool:
    """
    清空所有数据

    Returns:
        bool: 清空是否成功
    """
```

**返回**: `bool` - 清空是否成功

**警告**: 此操作不可逆！

**示例**:
```python
from core.database import DatabaseManager

db = DatabaseManager("./data.db")

# 确认清空
confirm = input("确定要清空所有数据吗？(yes/no): ")
if confirm.lower() == "yes":
    db.clear_all_data()
    print("数据已清空")
```

---

### clean_invalid_records()

清理所有文件不存在的记录。

```python
def clean_invalid_records(self) -> int:
    """
    清理所有文件不存在的记录

    Returns:
        int: 清理的记录数
    """
```

**返回**: `int` - 清理的记录数

**示例**:
```python
from core.database import DatabaseManager

db = DatabaseManager("./data.db")

# 清理无效记录
cleaned_count = db.clean_invalid_records()
print(f"清理了 {cleaned_count} 条无效记录")
```

---

## RuleLoader API

**模块**: [core/rule_loader.py](../core/rule_loader.py)

### 初始化

```python
RuleLoader(rules_path: str)
```

**参数**:
- `rules_path` (str): 规则 JSON 文件路径

**返回**: RuleLoader 实例

**示例**:
```python
from core.rule_loader import RuleLoader

loader = RuleLoader("./rules/parse_rules.json")
```

---

### get_enabled_rules()

获取所有启用的规则。

```python
def get_enabled_rules(self) -> List[Rule]:
    """
    获取所有启用的规则

    Returns:
        List[Rule]: 启用的规则列表
    """
```

**返回**: `List[Rule]` - 启用的规则列表

**示例**:
```python
from core.rule_loader import RuleLoader

loader = RuleLoader("./rules/parse_rules.json")

enabled_rules = loader.get_enabled_rules()
for rule in enabled_rules:
    print(f"规则: {rule.rule_name} ({rule.rule_id})")
```

---

### match_rules()

匹配所有符合条件的规则。

```python
def match_rules(self, subject: str, sender: str, body: str) -> List[Rule]:
    """
    匹配所有符合条件的规则

    Args:
        subject: 邮件主题
        sender: 发件人
        body: 邮件正文

    Returns:
        List[Rule]: 匹配的规则列表
    """
```

**参数**:
- `subject` (str): 邮件主题
- `sender` (str): 发件人
- `body` (str): 邮件正文

**返回**: `List[Rule]` - 匹配的规则列表

**示例**:
```python
from core.rule_loader import RuleLoader

loader = RuleLoader("./rules/parse_rules.json")

matched_rules = loader.match_rules(
    subject="12306 订单通知",
    sender="12306@12306.cn",
    body="您的订单已支付"
)

for rule in matched_rules:
    print(f"匹配到规则: {rule.rule_name}")
```

---

## Rule API

**模块**: [core/rule_loader.py](../core/rule_loader.py)

### match()

检查邮件是否匹配此规则。

```python
def match(self, subject: str, sender: str, body: str) -> bool:
    """
    检查邮件是否匹配此规则

    Args:
        subject: 邮件主题
        sender: 发件人
        body: 邮件正文

    Returns:
        bool: True 如果匹配，否则 False
    """
```

**参数**:
- `subject` (str): 邮件主题
- `sender` (str): 发件人
- `body` (str): 邮件正文

**返回**: `bool` - True 如果匹配，否则 False

**示例**:
```python
from core.rule_loader import RuleLoader

loader = RuleLoader("./rules/parse_rules.json")
rules = loader.get_enabled_rules()

rule = rules[0]  # 获取第一条规则

if rule.match(
    subject="12306 订单通知",
    sender="12306@12306.cn",
    body="您的订单已支付"
):
    print(f"邮件匹配规则: {rule.rule_name}")
```

---

## EmailExtractor API

**模块**: [core/email_extractor.py](../core/email_extractor.py)

### 初始化

```python
EmailExtractor(logger=None)
```

**参数**:
- `logger` (logging.Logger, optional): 日志对象

**返回**: EmailExtractor 实例

**示例**:
```python
from core.email_extractor import EmailExtractor

extractor = EmailExtractor()
```

---

### create_extraction_dir()

创建本次提取的存储目录。

```python
def create_extraction_dir(self) -> Path:
    """
    创建本次提取的存储目录

    Returns:
        Path: 提取目录路径
    """
```

**返回**: `Path` - 提取目录路径

**示例**:
```python
from core.email_extractor import EmailExtractor

extractor = EmailExtractor()

extraction_dir = extractor.create_extraction_dir()
print(f"提取目录: {extraction_dir}")
# 输出: extracted_mails/2026-03-11_070000
```

---

### extract_email_full()

完整提取一封邮件（正文、附件、提取内容）。

```python
def extract_email_full(msg, mail_data: dict, extraction_dir: Path) -> dict:
    """
    完整提取一封邮件（正文、附件、提取内容）

    Args:
        msg: 邮件对象（imaplib）
        mail_data: 邮件数据字典
        extraction_dir: 提取目录

    Returns:
        dict: 提取结果字典，包含以下键:
            - storage_path: 存储路径
            - body_file_path: 正文文件路径
            - attachment_count: 附件数量
            - attachment_paths: 附件路径列表
            - extracted_content_path: 提取内容文件路径
    """
```

**参数**:
- `msg`: 邮件对象（imaplib）
- `mail_data` (dict): 邮件数据字典
- `extraction_dir` (Path): 提取目录

**返回**: `dict` - 提取结果字典

**示例**:
```python
from core.email_extractor import extract_email_full
from pathlib import Path

result = extract_email_full(
    msg,
    mail_data,
    Path("./extracted_mails/2026-03-11_100000")
)

print(f"存储路径: {result['storage_path']}")
print(f"附件数量: {result['attachment_count']}")
```

---

## 钉钉通知 API

**模块**: [core/dingtalk_notifier.py](../core/dingtalk_notifier.py)

### send_dingtalk_message()

发送钉钉消息。

```python
def send_dingtalk_message(content: str) -> bool:
    """
    发送钉钉消息

    Args:
        content: 消息内容

    Returns:
        bool: True 如果成功，否则 False
    """
```

**参数**:
- `content` (str): 消息内容

**返回**: `bool` - True 如果成功，否则 False

**示例**:
```python
from core.dingtalk_notifier import send_dingtalk_message

success = send_dingtalk_message("测试消息")

if success:
    print("消息发送成功")
else:
    print("消息发送失败")
```

---

## 工具函数 API

### header_decoder.py

**模块**: [utils/header_decoder.py](../utils/header_decoder.py)

#### decode_mail_header()

解码邮件头（处理各种编码）。

```python
def decode_mail_header(header: Any) -> str:
    """
    解码邮件头（处理各种编码）

    Args:
        header: 邮件头对象

    Returns:
        str: 解码后的字符串
    """
```

**参数**:
- `header`: 邮件头对象

**返回**: `str` - 解码后的字符串

**示例**:
```python
from utils.header_decoder import decode_mail_header

subject = decode_mail_header(msg["Subject"])
sender = decode_mail_header(msg["From"])

print(f"主题: {subject}")
print(f"发件人: {sender}")
```

---

### file_utils.py

**模块**: [utils/file_utils.py](../utils/file_utils.py)

#### check_file_exists()

检查文件是否存在。

```python
def check_file_exists(file_path: str) -> bool:
    """
    检查文件是否存在

    Args:
        file_path: 文件路径

    Returns:
        bool: True 如果文件存在，否则 False
    """
```

**参数**:
- `file_path` (str): 文件路径

**返回**: `bool` - True 如果文件存在，否则 False

**示例**:
```python
from utils.file_utils import check_file_exists

if check_file_exists("./data.db"):
    print("文件存在")
```

---

#### normalize_path()

规范化路径分隔符（Windows/Linux 兼容）。

```python
def normalize_path(path: str) -> str:
    """
    规范化路径分隔符（Windows/Linux 兼容）

    Args:
        path: 原始路径

    Returns:
        str: 规范化后的路径（统一使用 /）
    """
```

**参数**:
- `path` (str): 原始路径

**返回**: `str` - 规范化后的路径（统一使用 /）

**示例**:
```python
from utils.file_utils import normalize_path

path = normalize_path("data\\subdir\\file.txt")
# 输出: data/subdir/file.txt
```

---

### archive_utils.py

**模块**: [utils/archive_utils.py](../utils/archive_utils.py)

#### ArchiveExtractor.extract_archive()

解压压缩文件。

```python
def extract_archive(self, archive_path: Path, extract_dir: Path, password: str = None) -> List[Path]:
    """
    解压压缩文件

    Args:
        archive_path: 压缩文件路径
        extract_dir: 解压目标目录
        password: 压缩包密码（可选）

    Returns:
        List[Path]: 解压后的文件列表
    """
```

**参数**:
- `archive_path` (Path): 压缩文件路径
- `extract_dir` (Path): 解压目标目录
- `password` (str, optional): 压缩包密码

**返回**: `List[Path]` - 解压后的文件列表

**支持的格式**: ZIP, RAR, 7Z, TAR.GZ, TAR.BZ2

**示例**:
```python
from utils.archive_utils import ArchiveExtractor
from pathlib import Path

extractor = ArchiveExtractor()

# 解压无密码文件
files = extractor.extract_archive(
    Path("./file.zip"),
    Path("./output/")
)

# 解压有密码文件
files = extractor.extract_archive(
    Path("./protected.zip"),
    Path("./output/"),
    password="secret123"
)
```

---

## 错误处理

所有 API 方法都应该使用 try-except 捕获异常：

```python
from core.database import DatabaseManager
import sqlite3

try:
    db = DatabaseManager("./data.db")
    # 执行操作
except sqlite3.Error as e:
    print(f"数据库错误: {e}")
except Exception as e:
    print(f"未知错误: {e}")
```

---

## 相关文档

- [系统架构总览](system-overview.md) - 高层架构视图
- [模块参考手册](module-reference.md) - 各模块详细说明
- [数据流图](data-flow.md) - 数据流详细说明
- [CLAUDE.md](../CLAUDE.md) - 主项目文档
