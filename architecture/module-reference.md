# 模块参考手册

**最后更新**: 2026-03-11

本文档提供项目各模块的详细参考，包括职责、功能、使用方法和代码示例。

---

## 目录结构

```
expense-reimbursement-email-automation/
├── config/                       # 配置模块
│   ├── settings.py               # 环境变量读取和校验
│   └── logger_config.py          # 日志系统初始化
│
├── core/                         # 核心业务逻辑
│   ├── models.py                 # 数据模型定义
│   ├── database.py               # SQLite 数据库管理
│   ├── rule_loader.py            # 规则加载和匹配引擎
│   ├── email_fetcher.py          # 邮件拉取和解析
│   ├── email_extractor.py        # 邮件内容提取
│   └── dingtalk_notifier.py      # 钉钉消息推送
│
└── utils/                        # 工具函数
    ├── header_decoder.py         # 邮件头解码
    ├── file_utils.py             # 文件操作工具
    └── archive_utils.py          # 压缩文件解压
```

---

## config/ - 配置模块

### settings.py

**职责**: 环境变量读取和校验

**导出配置**:

```python
# 邮箱配置
IMAP_HOST = os.getenv("IMAP_HOST")              # IMAP 服务器地址
IMAP_USER = os.getenv("IMAP_USER")              # IMAP 用户名
IMAP_PASS = os.getenv("IMAP_PASS")              # IMAP 密码

# 定时配置
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "60"))  # 检查间隔（秒）
TIME_ZONE = os.getenv("TIME_ZONE", "Asia/Shanghai")      # 时区

# 日志配置
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")              # 日志级别
LOG_DIR = os.getenv("LOG_DIR", "./logs")                # 日志目录
LOG_MAX_SIZE = int(os.getenv("LOG_MAX_SIZE", "10485760"))  # 日志文件最大大小
LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "5"))  # 日志备份数量

# 推送配置
DINGTALK_WEBHOOK = os.getenv("DINGTALK_WEBHOOK")    # 钉钉 Webhook URL
DINGTALK_SECRET = os.getenv("DINGTALK_SECRET")      # 钉钉签名密钥
PUSH_SWITCH = os.getenv("PUSH_SWITCH", "True").lower() == "true"  # 推送开关

# 解析 & 存储配置
PARSE_RULES_JSON_PATH = os.getenv("PARSE_RULES_JSON_PATH", "./rules/parse_rules.json")
EXTRACT_ROOT_DIR = os.getenv("EXTRACT_ROOT_DIR", "./extracted_mails")
CLEAR_DB_ON_STARTUP = os.getenv("CLEAR_DB_ON_STARTUP", "False").lower() == "true"
```

**核心函数**:

```python
def validate_email_format(email_str: str) -> bool:
    """校验邮箱格式"""
    pass

def validate_config() -> bool:
    """严格校验所有配置"""
    pass
```

**使用示例**:

```python
from config.settings import IMAP_HOST, IMAP_USER, IMAP_PASS

# 使用环境变量
host = IMAP_HOST
user = IMAP_USER
password = IMAP_PASS
```

---

### logger_config.py

**职责**: 日志系统初始化

**核心函数**:

```python
def generate_log_filename() -> str:
    """
    生成日志文件名
    格式: app_YYYY-MM-DD_HHMMSS_LEVEL.log
    """
    pass

def init_logger():
    """
    初始化日志系统
    - 控制台 Handler（同步刷新）
    - 文件 Handler（行缓冲 + 强制刷盘）
    - 退出钩子
    """
    pass
```

**日志格式**:

```
%(asctime)s - %(process)d - %(name)s - %(levelname)s - %(message)s
```

**使用示例**:

```python
from config.logger_config import init_logger
import logging

# 初始化日志
logger = init_logger()

# 使用日志
logger.info("这是一条信息日志")
logger.error("这是一条错误日志")
```

---

## core/ - 核心业务逻辑

### models.py

**职责**: 数据模型定义

**数据模型**:

```python
@dataclass
class ExtractedEmail:
    """已提取邮件记录"""
    id: Optional[int]              # 数据库自增ID
    message_id: str                # 邮件 Message-ID（IMAP）
    subject: str                   # 邮件主题
    sender: str                    # 发件人
    rule_id: str                   # 匹配的规则ID
    mail_date: str                 # 邮件发送时间（唯一标识）
    extracted_at: Optional[datetime]  # 提取时间
    storage_path: str              # 提取目录路径
    attachment_count: int          # 附件数量
    body_file_path: str            # 正文文件路径

@dataclass
class ExtractionHistory:
    """提取历史记录"""
    id: Optional[int]
    message_id: str                # 关联邮件 Message-ID
    rule_id: str                   # 匹配的规则ID
    action: str                    # 动作类型（matched/skipped）
    created_at: Optional[datetime]  # 创建时间
```

---

### database.py

**职责**: SQLite 数据库管理

**表结构**:

```sql
-- 已提取邮件记录表
CREATE TABLE extracted_emails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id TEXT UNIQUE NOT NULL,
    subject TEXT,
    sender TEXT,
    rule_id TEXT,
    mail_date TEXT,
    extracted_at TIMESTAMP,
    storage_path TEXT,
    attachment_count INTEGER,
    body_file_path TEXT
);

-- 提取历史表
CREATE TABLE extraction_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id TEXT,
    rule_id TEXT,
    action TEXT,
    created_at TIMESTAMP
);
```

**核心方法**:

| 方法 | 功能 | 调用者 | 关联逻辑 |
|------|------|--------|---------|
| `_init_database()` | 创建表结构和索引 | `__init__()` | - |
| `is_email_extracted(message_id)` | 检查邮件是否已提取 | - | 基础去重 |
| `is_email_extracted_with_files(message_id)` | 增强版去重检查（验证文件） | - | 文件验证去重 |
| `add_extracted_email(email_record)` | 添加新邮件记录 | main.py | INSERT |
| `update_extracted_email(email_record)` | 更新已存在的邮件记录 | main.py | UPDATE |
| `get_extracted_email(message_id)` | 根据 Message-ID 获取记录 | - | SELECT |
| **`get_existing_mail_dates()`** | **获取已提取且文件存在的邮件发送时间集合** | fetch_reimbursement_mails() | 预检查去重 |
| `add_extraction_history(history)` | 添加提取历史 | main.py | INSERT |
| `get_statistics()` | 获取统计信息 | - | SELECT |
| `clear_all_data()` | 清空所有数据 | main.py | DELETE |

**使用示例**:

```python
from core.database import DatabaseManager
from core.models import ExtractedEmail
from datetime import datetime

# 初始化数据库管理器
db = DatabaseManager("./data.db")

# 添加邮件记录
email_record = ExtractedEmail(
    message_id="<xxx@example.com>",
    subject="测试邮件",
    sender="sender@example.com",
    rule_id="rule_001",
    mail_date="2026-03-11 10:00:00",
    extracted_at=datetime.now(),
    storage_path="./extracted_mails/2026-03-11_100000",
    attachment_count=1,
    body_file_path="./extracted_mails/.../bodies/rule_001/xxx.html"
)
db.add_extracted_email(email_record)

# 检查邮件是否已提取
if db.is_email_extracted("<xxx@example.com>"):
    print("邮件已提取")

# 获取已提取邮件的发送时间集合
existing_dates = db.get_existing_mail_dates()
```

---

### rule_loader.py

**职责**: 规则加载和匹配引擎

**规则模型**:

```python
@dataclass
class Rule:
    """规则模型"""
    rule_id: str                    # 规则ID（如 "rule_002"）
    rule_name: str                  # 规则名称
    enabled: bool                   # 是否启用
    description: str                # 规则描述
    match_conditions: dict          # 匹配条件
        - sender_contains: List[str]  # 发件人关键词
        - subject_contains: List[str] # 主题关键词
        - body_contains: List[str]    # 正文关键词
    extract_options: dict           # 提取选项
        - extract_attachments: bool
        - extract_body: bool
        - extract_headers: bool
    output_subdir: str              # 输出子目录名
```

**核心方法**:

```python
class RuleLoader:
    def _load_rules(self) -> List[Rule]:
        """从 JSON 文件加载规则"""
        pass

    def get_enabled_rules(self) -> List[Rule]:
        """获取所有启用的规则"""
        pass

    def match_rules(self, subject: str, sender: str, body: str) -> List[Rule]:
        """匹配所有符合条件的规则"""
        pass
```

**Rule.match() 方法**:

```python
def match(self, subject: str, sender: str, body: str) -> bool:
    """
    检查邮件是否匹配此规则
    - subject: 邮件主题
    - sender: 发件人
    - body: 邮件正文
    - 返回: True 如果匹配，否则 False
    """
    pass
```

**使用示例**:

```python
from core.rule_loader import RuleLoader

# 初始化规则加载器
loader = RuleLoader("./rules/parse_rules.json")

# 获取所有启用的规则
enabled_rules = loader.get_enabled_rules()

# 匹配规则
matched_rules = loader.match_rules(
    subject="12306 订单通知",
    sender="12306@12306.cn",
    body="您的订单已支付"
)

for rule in matched_rules:
    print(f"匹配到规则: {rule.rule_name}")
```

---

### email_fetcher.py

**职责**: 邮件拉取和解析

**核心函数**:

```python
def parse_reimbursement_mail(msg, rule_loader: RuleLoader) -> Optional[dict]:
    """
    解析单封邮件，使用规则判断是否为目标邮件
    - msg: 邮件对象（imaplib）
    - rule_loader: 规则加载器
    - 返回: 邮件数据字典，如果不匹配则返回 None
    """
    pass

def fetch_reimbursement_mails(logger, db_manager: DatabaseManager) -> List[dict]:
    """
    拉取匹配规则的邮件
    - logger: 日志对象
    - db_manager: 数据库管理器（用于去重）
    - 返回: 匹配的邮件列表
    """
    pass

def send_mail_summary_notification(matched_mails: List[dict], time_range_days: int):
    """
    发送汇总通知到钉钉
    - matched_mails: 匹配的邮件列表
    - time_range_days: 时间范围（天）
    """
    pass
```

**邮件数据结构**:

```python
{
    "message_id": "xxx",           # 邮件 Message-ID
    "subject": "邮件主题",          # 邮件主题
    "sender": "发件人",             # 发件人
    "date": "2026-03-11 10:00:00",  # 发送时间（用于去重）
    "body": "正文内容...",          # 正文（前200字符）
    "matched_rules": [Rule对象]     # 匹配的规则列表
}
```

**使用示例**:

```python
from core.email_fetcher import fetch_reimbursement_mails
from core.database import DatabaseManager
from config.logger_config import init_logger

# 初始化
logger = init_logger()
db = DatabaseManager("./data.db")

# 拉取邮件
matched_mails = fetch_reimbursement_mails(logger, db)

# 处理匹配的邮件
for mail in matched_mails:
    print(f"主题: {mail['subject']}")
    print(f"发件人: {mail['sender']}")
    print(f"匹配规则: {[r.rule_name for r in mail['matched_rules']]}")
```

---

### email_extractor.py

**职责**: 邮件内容提取

**目录结构**:

```
extracted_mails/YYYY-MM-DD_HHMMSS/
├── bodies/{rule_id}/           # 邮件正文HTML
│   └── {md5(message_id)}.html
├── attachments/{rule_id}/      # 邮件附件
│   └── {原文件名}
└── extracted/{rule_id}/        # 结构化数据（JSON）
    └── {md5(message_id)}.json
```

**核心类**:

```python
class EmailExtractor:
    def create_extraction_dir(self) -> Path:
        """创建本次提取的存储目录"""
        pass

    def save_email_body(self, msg, mail_data: dict, extraction_dir: Path) -> str:
        """保存邮件正文HTML"""
        pass

    def extract_attachments(self, msg, mail_data: dict, extraction_dir: Path) -> List[str]:
        """提取并保存邮件附件"""
        pass

    def save_extracted_content(self, mail_data: dict, extraction_dir: Path) -> str:
        """保存结构化数据（JSON）"""
        pass
```

**完整提取函数**:

```python
def extract_email_full(msg, mail_data: dict, extraction_dir: Path) -> dict:
    """
    完整提取一封邮件（正文、附件、提取内容）
    - msg: 邮件对象（imaplib）
    - mail_data: 邮件数据字典
    - extraction_dir: 提取目录
    - 返回: 提取结果字典
    """
    pass
```

**提取结果数据结构**:

```python
{
    'storage_path': 'extracted_mails/2026-03-11_070000',
    'body_file_path': '.../bodies/rule_002/abc123.html',
    'attachment_count': 2,
    'attachment_paths': ['.../attachments/rule_002/file1.pdf', ...],
    'extracted_content_path': '.../extracted/rule_002/abc123.json'
}
```

**使用示例**:

```python
from core.email_extractor import extract_email_full
from pathlib import Path

# 提取邮件
result = extract_email_full(msg, mail_data, Path("./extracted_mails/2026-03-11_100000"))

# 查看结果
print(f"存储路径: {result['storage_path']}")
print(f"正文文件: {result['body_file_path']}")
print(f"附件数量: {result['attachment_count']}")
print(f"附件列表: {result['attachment_paths']}")
```

---

### dingtalk_notifier.py

**职责**: 钉钉消息推送

**核心函数**:

```python
def send_dingtalk_message(content: str) -> bool:
    """
    发送钉钉消息
    - content: 消息内容
    - 返回: True 如果成功，否则 False
    """
    pass
```

**使用示例**:

```python
from core.dingtalk_notifier import send_dingtalk_message

# 发送消息
success = send_dingtalk_message("测试消息")

if success:
    print("消息发送成功")
else:
    print("消息发送失败")
```

---

## utils/ - 工具函数

### header_decoder.py

**职责**: 邮件头解码

**核心函数**:

```python
def decode_mail_header(header: Any) -> str:
    """
    解码邮件头（处理各种编码）
    - header: 邮件头对象
    - 返回: 解码后的字符串
    """
    pass
```

**使用示例**:

```python
from utils.header_decoder import decode_mail_header

# 解码邮件头
subject = decode_mail_header(msg["Subject"])
sender = decode_mail_header(msg["From"])
```

---

### file_utils.py

**职责**: 文件操作工具

**核心函数**:

```python
def ensure_log_dir(log_dir: str):
    """确保日志目录存在"""
    pass

def check_file_exists(file_path: str) -> bool:
    """检查文件是否存在"""
    pass

def normalize_path(path: str) -> str:
    """规范化路径分隔符（Windows/Linux 兼容）"""
    pass
```

**使用示例**:

```python
from utils.file_utils import check_file_exists, normalize_path

# 检查文件存在
if check_file_exists("./data.db"):
    print("文件存在")

# 规范化路径
path = normalize_path("data\\subdir\\file.txt")  # Windows
# → "data/subdir/file.txt"
```

---

### archive_utils.py

**职责**: 压缩文件解压

**支持的格式**:
- ZIP
- RAR（需要 unrar 工具）
- 7Z
- TAR.GZ
- TAR.BZ2

**核心类**:

```python
class ArchiveExtractor:
    def __init__(self, logger=None):
        """初始化解压器"""
        pass

    def extract_archive(self, archive_path: Path, extract_dir: Path, password: str = None) -> List[Path]:
        """
        解压压缩文件
        - archive_path: 压缩文件路径
        - extract_dir: 解压目标目录
        - password: 压缩包密码（可选）
        - 返回: 解压后的文件列表
        """
        pass
```

**使用示例**:

```python
from utils.archive_utils import ArchiveExtractor
from pathlib import Path

# 初始化解压器
extractor = ArchiveExtractor()

# 解压文件（无密码）
extracted_files = extractor.extract_archive(
    Path("./attachments/file.zip"),
    Path("./attachments/file_extracted/")
)

# 解压文件（有密码）
extracted_files = extractor.extract_archive(
    Path("./attachments/protected.zip"),
    Path("./attachments/protected_extracted/"),
    password="secret123"
)

print(f"解压了 {len(extracted_files)} 个文件")
```

---

## rules/ - 规则配置

### parse_rules.json

**职责**: 邮件匹配规则配置

**配置示例**:

```json
{
  "parse_time_range_days": 20,
  "rules": [
    {
      "rule_id": "rule_002",
      "rule_name": "12306提取",
      "enabled": true,
      "description": "提取12306发送的订单邮件",
      "match_conditions": {
        "sender_contains": ["12306", "didifapiao"],
        "subject_contains": [],
        "body_contains": []
      },
      "extract_options": {
        "extract_attachments": true,
        "extract_body": false,
        "extract_headers": false
      },
      "output_subdir": "rule_002"
    }
  ]
}
```

**配置字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `parse_time_range_days` | int | 邮件搜索时间范围（天） |
| `rule_id` | str | 规则唯一标识 |
| `rule_name` | str | 规则名称 |
| `enabled` | bool | 是否启用 |
| `description` | str | 规则描述 |
| `sender_contains` | list | 发件人关键词列表 |
| `subject_contains` | list | 主题关键词列表 |
| `body_contains` | list | 正文关键词列表 |
| `extract_attachments` | bool | 是否提取附件 |
| `extract_body` | bool | 是否提取正文 |
| `output_subdir` | str | 输出子目录名 |

---

## 相关文档

- [系统架构总览](system-overview.md) - 高层架构视图
- [数据流图](data-flow.md) - 数据流详细说明
- [API 接口文档](api-reference.md) - 公共 API 说明
- [部署架构](deployment.md) - 部署指南
- [CLAUDE.md](../CLAUDE.md) - 主项目文档
