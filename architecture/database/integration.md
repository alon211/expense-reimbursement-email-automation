# 数据库集成到主程序 - 完成报告

## 集成概述

数据库功能已成功集成到主程序 [main.py](main.py) 中，实现了：
- ✅ 邮件去重检查
- ✅ 提取记录存储
- ✅ 提取历史追踪
- ✅ 数据库统计功能

## 修改内容

### 1. [core/email_fetcher.py](core/email_fetcher.py)

#### 添加 message_id 提取
```python
def parse_reimbursement_mail(msg, rule_loader, logger_instance=None):
    # 提取邮件唯一标识
    message_id = decode_mail_header(msg.get("Message-ID", ""))
    if not message_id:
        # 自动生成唯一标识
        message_id = f"<auto_{hash(...)}@generated>"

    return {
        "message_id": message_id,  # 新增字段
        "subject": subject,
        "sender": sender,
        ...
    }
```

#### 重构 fetch_reimbursement_mails 函数
- 新增 `db_manager` 参数（可选）
- 实现去重检查：`db_manager.is_email_extracted(message_id)`
- 返回匹配邮件列表，而不是内部处理所有逻辑
- 添加跳过计数日志

#### 新增 send_mail_summary_notification 函数
```python
def send_mail_summary_notification(matched_mails, time_range_days, logger_instance=None):
    """发送匹配邮件的汇总通知（独立函数）"""
```

### 2. [main.py](main.py)

#### 新增导入
```python
from core.email_fetcher import fetch_reimbursement_mails, send_mail_summary_notification
from core.database import DatabaseManager
from core.models import ExtractedEmail, ExtractionHistory
from core.rule_loader import RuleLoader
from pathlib import Path
```

#### main() 函数重构

**初始化阶段：**
```python
# 初始化数据库
db_path = Path(EXTRACT_ROOT_DIR) / "data.db"
db = DatabaseManager(str(db_path))

# 加载规则获取时间范围
rule_loader = RuleLoader(PARSE_RULES_JSON_PATH)
```

**主循环处理：**
```python
# 拉取匹配的邮件（带去重检查）
matched_mails = fetch_reimbursement_mails(logger, db_manager=db)

# 处理匹配的邮件
for mail_data in matched_mails:
    message_id = mail_data['message_id']
    subject = mail_data['subject']
    sender = mail_data['sender']
    matched_rules = mail_data.get('matched_rules', [])

    primary_rule_id = matched_rules[0].rule_id

    # 创建提取记录
    email_record = ExtractedEmail(
        message_id=message_id,
        subject=subject,
        sender=sender,
        rule_id=primary_rule_id,
        extracted_at=datetime.now(),
        storage_path="",  # TODO 3: 实现
        attachment_count=0,  # TODO 3: 实现
        body_file_path=""  # TODO 3: 实现
    )
    db.add_extracted_email(email_record)

    # 添加提取历史
    history = ExtractionHistory(
        message_id=message_id,
        rule_id=primary_rule_id,
        action="matched"
    )
    db.add_extraction_history(history)

# 发送汇总通知
send_mail_summary_notification(matched_mails, time_range_days, logger)
```

## 功能特性

### 1. 去重机制
- 基于 `message_id` 判断邮件是否已提取
- 已提取的邮件会被跳过，不重复处理
- 日志中显示跳过的邮件数量

### 2. 记录存储
- 每封匹配的邮件都会记录到数据库
- 存储：message_id, subject, sender, rule_id, extracted_at
- 待完善：storage_path, attachment_count, body_file_path（TODO 3）

### 3. 历史追踪
- 每次匹配都会添加历史记录
- 记录：message_id, rule_id, action, created_at

### 4. 错误处理
- 数据库初始化失败时程序退出
- 记录失败时记录错误日志但不中断流程
- 异常堆栈输出到日志

## 工作流程

```
┌─────────────────────────────────────────────────────┐
│  主程序启动                                          │
│  - 初始化日志                                        │
│  - 初始化数据库（extracted_mails/data.db）           │
│  - 加载解析规则                                      │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│  定时检查循环（每 CHECK_INTERVAL 秒）                │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│  拉取邮件                                            │
│  - 连接 IMAP 服务器                                  │
│  - 应用时间范围过滤（SINCE 5天）                     │
│  - 应用规则匹配                                      │
│  - 检查去重（查询数据库）                            │
│  - 返回新邮件列表                                    │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│  处理匹配邮件                                        │
│  - 遍历邮件列表                                      │
│  - 提取邮件信息（message_id, subject, sender）      │
│  - 获取匹配规则                                      │
│  - 写入数据库（extracted_emails 表）                │
│  - 写入历史（extraction_history 表）                │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│  发送通知                                            │
│  - 钉钉推送汇总信息                                  │
│  - 日志记录处理结果                                  │
└─────────────────────────────────────────────────────┘
```

## 测试验证

运行测试脚本：
```bash
python test_db_main_integration.py
```

测试内容：
1. ✅ 数据库初始化
2. ✅ 规则加载
3. ✅ 邮件处理流程
4. ✅ 去重功能
5. ✅ 统计信息
6. ✅ 记录查询
7. ✅ 数据清理

## 使用方法

### 启动服务
```bash
python main.py
```

### 预期日志输出
```
===== 报销邮件自动化服务启动 =====
【系统日志】时区：Asia/Shanghai | 检查间隔：60秒
【系统日志】日志文件：./logs/xxx.log
【系统日志】提取目录：./extracted_mails
【系统日志】数据库路径：extracted_mails\data.db
✅ 数据库初始化成功
【系统日志】解析规则：3 条，时间范围：5 天
===============================
```

### 处理新邮件时
```
【业务日志】发现 2 封新邮件，开始处理...
【业务日志】已记录邮件提取：ID=1，主题=差旅费报销
【业务日志】已记录邮件提取：ID=2，主题=12306订单
【业务日志】已发送 2 封邮件的钉钉通知
```

### 邮件已提取时
```
【业务日志】跳过 1 封已提取的邮件
【业务日志】未发现新邮件
```

## 数据库文件

**位置：** `./extracted_mails/data.db`

**表结构：**
- `extracted_emails`: 已提取邮件记录
- `extraction_history`: 提取历史记录
- `sqlite_sequence`: 自增ID序列

**查看数据：**
```bash
sqlite3 extracted_mails/data.db
sqlite> SELECT * FROM extracted_emails;
sqlite> SELECT * FROM extraction_history;
```

## 下一步（TODO 3）

当前代码中有 3 个 TODO 标记，待实现：
- `storage_path`: 文件存储路径
- `attachment_count`: 附件数量
- `body_file_path`: 正文文件路径

这些将在 TODO 3（文件提取和分类存储模块）中实现。

---

**集成状态：** ✅ 已完成并通过测试
**测试文件：** [test_db_main_integration.py](test_db_main_integration.py)
**数据库模块：** [core/database.py](core/database.py)
**主程序：** [main.py](main.py)
