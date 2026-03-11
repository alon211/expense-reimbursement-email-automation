# TODO 2: SQLite 数据库管理模块 - 完成报告

## 实现内容

### 1. 新建文件

#### `core/models.py` - 数据模型
- `ExtractedEmail`: 已提取邮件记录模型
  - 字段：id, message_id, subject, sender, rule_id, extracted_at, storage_path, attachment_count, body_file_path
  - 方法：to_dict()

- `ExtractionHistory`: 提取历史记录模型
  - 字段：id, message_id, rule_id, action, created_at
  - 方法：to_dict()

#### `core/database.py` - 数据库管理器
- `DatabaseManager`: 数据库管理类
  - 数据库初始化和表结构创建
  - 邮件去重检查
  - 邮件记录的增删查改
  - 提取历史记录管理
  - 统计信息获取
  - 旧记录清理功能

### 2. 数据库表结构

#### extracted_emails 表（已提取邮件记录）
```sql
CREATE TABLE extracted_emails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id TEXT UNIQUE NOT NULL,      -- 邮件唯一标识
    subject TEXT,                          -- 邮件主题
    sender TEXT,                           -- 发件人
    rule_id TEXT,                          -- 匹配的规则ID
    extracted_at TIMESTAMP,                -- 提取时间
    storage_path TEXT,                     -- 存储路径
    attachment_count INTEGER,              -- 附件数量
    body_file_path TEXT                    -- 正文文件路径
);
```

#### extraction_history 表（提取历史）
```sql
CREATE TABLE extraction_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id TEXT,                       -- 邮件唯一标识
    rule_id TEXT,                          -- 规则ID
    action TEXT,                           -- 操作类型
    created_at TIMESTAMP                   -- 创建时间
);
```

### 3. 索引优化
- `idx_message_id`: 邮件 ID 查询优化
- `idx_rule_id`: 规则 ID 查询优化
- `idx_extracted_at`: 时间范围查询优化
- `idx_history_message_id`: 历史记录查询优化

## 核心功能

### 1. 邮件去重
```python
from core.database import DatabaseManager

db = DatabaseManager("./extracted_mails/data.db")

# 检查邮件是否已提取
if not db.is_email_extracted(message_id):
    # 处理邮件
    pass
```

### 2. 添加提取记录
```python
from core.models import ExtractedEmail
from datetime import datetime

email_record = ExtractedEmail(
    message_id="<msg@example.com>",
    subject="邮件主题",
    sender="sender@example.com",
    rule_id="rule_001",
    extracted_at=datetime.now(),
    storage_path="./extracted_mails/2026-03-11_120000",
    attachment_count=2,
    body_file_path="./extracted_mails/2026-03-11_120000/bodies/rule_001/msg.txt"
)
db.add_extracted_email(email_record)
```

### 3. 查询记录
```python
# 获取单条记录
email = db.get_extracted_email(message_id)

# 获取所有记录（分页）
emails = db.get_all_extracted_emails(limit=10, offset=0)
```

### 4. 统计信息
```python
stats = db.get_statistics()
print(f"总邮件数: {stats['total_emails']}")
print(f"按规则分组: {stats['by_rule']}")
```

### 5. 历史记录
```python
from core.models import ExtractionHistory

history = ExtractionHistory(
    message_id="<msg@example.com>",
    rule_id="rule_001",
    action="extracted"
)
db.add_extraction_history(history)

# 获取历史
histories = db.get_extraction_history(message_id)
```

### 6. 数据清理
```python
# 删除指定记录
db.delete_email_record(message_id)

# 清理30天前的记录
deleted_count = db.clear_old_records(days=30)
```

## 测试验证

### 测试文件
1. `test_database.py` - 基础功能测试
2. `verify_db_structure.py` - 表结构验证
3. `test_db_integration.py` - 集成使用测试

### 测试结果
✅ 所有测试通过
- 数据库初始化
- 去重功能
- 记录增删查改
- 统计功能
- 历史记录管理
- 配置集成

## 配置说明

数据库路径由 `.env` 文件中的 `EXTRACT_ROOT_DIR` 配置决定：

```env
# 提取内容根文件夹路径
EXTRACT_ROOT_DIR=./extracted_mails
```

数据库文件将创建在：`./extracted_mails/data.db`

## 后续集成

数据库模块已完成，可在以下场景使用：

1. **TODO 3**: 在文件提取模块中记录提取的邮件
2. **TODO 4**: 在邮件处理流程中实现去重
3. **TODO 6**: 在管理工具中提供数据查询和管理界面

## 文件结构

```
expense-reimbursement-email-automation/
├── core/
│   ├── __init__.py         (已更新 - 导出 DatabaseManager, ExtractedEmail, ExtractionHistory)
│   ├── database.py         (新建 - 数据库管理)
│   └── models.py           (新建 - 数据模型)
├── extracted_mails/
│   └── data.db             (运行时自动创建)
├── test_database.py        (新建 - 基础测试)
├── verify_db_structure.py  (新建 - 结构验证)
└── test_db_integration.py  (新建 - 集成测试)
```

## 技术特性

- ✅ 使用 SQLite3 标准库，无需额外依赖
- ✅ 上下文管理器确保连接安全关闭
- ✅ 自动提交和错误回滚
- ✅ 支持字典式访问查询结果
- ✅ 自动创建数据库目录
- ✅ 索引优化查询性能

---

**TODO 2 状态**: ✅ 已完成并通过测试
