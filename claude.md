## 文档导航

### 📋 计划文档
- **[功能完成状态](plan/feature-status.md)** - 查看项目各功能的开发状态（已完成/未完成）
- **[开发路线图](plan/development-roadmap.md)** - 查看项目未来开发方向和优先级
- **[测试覆盖状态](plan/testing-status.md)** - 查看测试覆盖情况和待测试项

### 🏗️ 架构文档
- **[系统架构总览](architecture/system-overview.md)** - 了解项目整体架构和核心特性
- **[模块参考手册](architecture/module-reference.md)** - 查看各模块的详细说明和使用方法
- **[数据流图](architecture/data-flow.md)** - 了解数据在系统中的流动路径
- **[API 接口文档](architecture/api-reference.md)** - 查看公共 API 的详细说明
- **[部署架构](architecture/deployment.md)** - 查看本地部署和 Docker 部署指南

### 📁 专题文档
- **数据库相关**: [architecture/database/](architecture/database/) - 数据库使用、集成、配置等文档
- **实现记录**: [plan/implementation/](plan/implementation/) - 功能实现和验证记录
- **配置相关**: [architecture/config/](architecture/config/) - 敏感信息存储等配置文档

---

## 强制约束
自动git commit，需要用户确认后才可以

---

## 功能清单

### 功能状态说明
- ✅ **已完成** - 功能已实现并测试通过
- ⚠️ **已实现但未测试** - 代码已完成，但尚未进行实际测试
- ❌ **未实现** - 功能尚未开发

### 核心功能（已完成）

- ✅ **环境依赖搭建**
  - Python 虚拟环境配置
  - requirements.txt 依赖管理
  - 跨平台兼容性处理（Windows/Linux）

- ✅ **配置管理模块**
  - 环境变量读取（.env 文件）
  - 配置校验（邮箱格式、必填项检查）
  - 多环境配置支持（开发/生产）

- ✅ **日志系统**
  - 实时刷盘机制（行缓冲 + fsync）
  - 多级别日志输出（DEBUG/INFO/WARNING/ERROR）
  - 控制台 + 文件双输出
  - 退出钩子确保日志完整性

- ✅ **数据库管理**
  - SQLite 数据库初始化
  - 邮件记录表（extracted_emails）
  - 提取历史表（extraction_history）
  - 索引优化（message_id, rule_id, extracted_at）
  - 数据库迁移（mail_date 字段自动添加）

- ✅ **规则引擎**
  - JSON 规则配置（rules/parse_rules.json）
  - 规则加载和验证（RuleLoader）
  - 多维度匹配（发件人、主题、正文）
  - 规则启用/禁用开关
  - 时间范围配置（parse_time_range_days）

- ✅ **邮件拉取模块**
  - IMAP 协议连接
  - 邮件搜索（时间范围 + 状态筛选）
  - 邮件头解码（多编码支持）
  - 邮件正文提取（text/plain + text/html）
  - 规则匹配引擎
  - 已读标记

- ✅ **邮件内容提取**
  - 邮件正文 HTML 保存
  - 附件提取和解码
  - 结构化数据导出（JSON）
  - 按规则分类存储
  - 文件名安全处理（MD5 哈希）
  - 目录组织（bodies/attachments/extracted）

- ✅ **智能去重机制**
  - 基于邮件发送时间（mail_date）的唯一标识
  - 预检查去重（get_existing_mail_dates）
  - 文件存在性验证
  - 数据库记录 + 文件双重验证
  - 智能更新（记录存在则更新，不存在则插入）
  - 三层防护机制

- ⚠️ **钉钉通知推送**（已实现但未测试）
  - Webhook 消息发送
  - 签名验证（HMAC-SHA256）
  - 推送开关控制
  - 汇总通知（多邮件合并）
  - 异常错误通知
  - **需要测试**：实际发送钉钉消息验证

- ✅ **主程序循环**
  - 定时任务调度（CHECK_INTERVAL）
  - 时区支持（pytz）
  - 全局异常捕获
  - 优雅退出（KeyboardInterrupt 处理）
  - 数据库清空配置（CLEAR_DB_ON_STARTUP）

- ✅ **工具函数模块**
  - 邮件头解码（utils/header_decoder.py）
  - 文件操作工具（utils/file_utils.py）
  - 路径规范化（Windows/Linux 兼容）
  - 文件存在性检查

- ⚠️ **Docker 容器化**（已实现但未测试）
  - Dockerfile 镜像构建
  - docker-compose.yml 编排配置
  - 环境变量注入
  - 数据持久化挂载
  - **需要测试**：Docker 镜像构建和运行验证

- ✅ **测试脚本**
  - 数据库测试（test_database.py）
  - 规则测试（test_rules.py）
  - 集成测试（test_db_main_integration.py）
  - 去重测试（test_enhanced_dedup.py, test_mail_date_dedup.py）
  - 调试工具（debug_db_paths.py, debug_mail_matching.py）

### 文档功能（已完成）

- ✅ **项目架构文档**（CLAUDE.md）
  - 目录结构说明
  - 数据模型定义
  - 函数功能清单
  - 调用关系图
  - 去重机制详解
  - 环境变量配置
  - Git 提交历史
  - 故障排查指南

- ✅ **实现文档**（docs/）
  - TODO3_IMPLEMENTATION.md（文件提取实现）
  - TODO3_VERIFICATION.md（功能验证）
  - MAIN_DB_INTEGRATION.md（数据库集成）
  - CLEAR_DB_CONFIG.md（清库配置）
  - DATABASE_STATUS.md（数据库状态）

### 待扩展功能（未实现）

- ❌ **README.md 项目说明**
  - 项目介绍和使用指南
  - 快速开始教程
  - 常见问题解答

- ❌ **单元测试覆盖**
  - pytest 测试框架
  - Mock 外部依赖（IMAP、钉钉 API）
  - 测试覆盖率报告（>80%）

- ❌ **企业微信推送**
  - 企业微信机器人集成
  - 多渠道推送支持（钉钉 + 企业微信）

- ❌ **Exchange 协议支持**
  - Microsoft Exchange 邮箱支持
  - EWS API 集成

- ❌ **Web UI 管理界面**
  - Flask/FastAPI 后端
  - Vue.js 前端界面
  - 规则在线编辑
  - 邮件记录查看
  - 统计报表展示

- ❌ **邮件附件预览**
  - PDF 在线预览
  - 图片预览
  - Office 文档预览

- ✅ **压缩文件附件自动解压**（已实现）
  - 检测附件是否为压缩文件（zip、rar、7z、tar.gz 等）
  - 根据规则配置决定是否解压
  - 支持密码保护的压缩包
  - 解压后使用嵌套目录结构（如 invoice.zip/ 目录）
  - 解压后保留原压缩包
  - 支持的格式：zip、rar、7z、tar.gz、tar.bz2

- ❌ **定时任务优化**
  - Cron 表达式支持
  - 任务调度可视化
  - 任务执行历史

- ❌ **监控告警**
  - 服务健康检查
  - 错误率监控
  - 性能指标采集
  - 告警规则配置

---

# 报销邮件自动化服务 - 项目架构文档

## 项目概述

这是一个基于 Python 的邮件自动化处理服务，用于从 IMAP 邮箱中拉取匹配规则的报销邮件，提取正文和附件，并通过钉钉推送通知。

**核心特性**：
- 基于规则的邮件匹配（JSON配置）
- 智能去重机制（基于邮件发送时间 + 文件存在性验证）
- 邮件内容提取（正文HTML、附件、结构化数据）
- SQLite 数据库记录和去重
- 钉钉消息推送
- Docker 容器化部署

---

## 目录结构

```
expense-reimbursement-email-automation/
├── main.py                        # 程序入口，主循环逻辑
├── requirements.txt               # Python 依赖
├── .env.example                   # 环境变量示例
├── .env                          # 本地环境变量（不提交）
├── .gitignore                    # Git 忽略规则
├── Dockerfile                    # Docker 镜像构建
├── docker-compose.yml            # Docker 编排配置
│
├── config/                       # 配置模块
│   ├── __init__.py
│   ├── settings.py               # 环境变量读取和校验
│   └── logger_config.py          # 日志系统初始化
│
├── core/                         # 核心业务逻辑
│   ├── __init__.py
│   ├── models.py                 # 数据模型定义
│   ├── database.py               # SQLite 数据库管理
│   ├── rule_loader.py            # 规则加载和匹配引擎
│   ├── email_fetcher.py          # 邮件拉取和解析
│   ├── email_extractor.py        # 邮件内容提取（正文/附件）
│   └── dingtalk_notifier.py      # 钉钉消息推送
│
├── utils/                        # 工具函数
│   ├── __init__.py
│   ├── header_decoder.py         # 邮件头解码
│   └── file_utils.py             # 文件操作工具
│
├── rules/                        # 规则配置
│   └── parse_rules.json          # 邮件匹配规则（JSON）
│
├── logs/                         # 日志目录（自动生成）
└── extracted_mails/              # 提取文件存储
    └── YYYY-MM-DD_HHMMSS/        # 时间戳目录（每次运行）
        ├── bodies/               # 邮件正文HTML
        │   └── {rule_id}/
        ├── attachments/          # 邮件附件
        │   └── {rule_id}/
        └── extracted/            # 结构化数据（JSON）
            └── {rule_id}/
```

---

## 数据模型

### ExtractedEmail（已提取邮件记录）
```python
@dataclass
class ExtractedEmail:
    id: Optional[int]              # 数据库自增ID
    message_id: str                # 邮件Message-ID（IMAP）
    subject: str                   # 邮件主题
    sender: str                    # 发件人
    rule_id: str                   # 匹配的规则ID
    mail_date: str                 # 邮件发送时间（唯一标识，用于去重）
    extracted_at: Optional[datetime] # 提取时间
    storage_path: str              # 提取目录路径
    attachment_count: int          # 附件数量
    body_file_path: str            # 正文文件路径
```

### ExtractionHistory（提取历史记录）
```python
@dataclass
class ExtractionHistory:
    id: Optional[int]
    message_id: str                # 关联邮件Message-ID
    rule_id: str                   # 匹配的规则ID
    action: str                    # 动作类型（matched/skipped）
    created_at: Optional[datetime] # 创建时间
```

---

## 核心功能模块

### 1. 主程序入口（main.py）

#### `main()` - 主循环
**职责**：定时检查邮箱，拉取并处理匹配的邮件

**调用流程**：
```
main()
├── init_logger()                          # 初始化日志系统
├── DatabaseManager()                      # 初始化数据库
│   └── _init_database()                  # 创建表结构
├── RuleLoader()                           # 加载解析规则
└── while True:                            # 主循环
    ├── fetch_reimbursement_mails(logger, db)
    ├── 遍历 matched_mails
    │   ├── 创建 ExtractedEmail 记录
    │   ├── add_extracted_email() / update_extracted_email()
    │   └── add_extraction_history()
    └── send_mail_summary_notification()
```

**关键代码片段**：
```python
# 预检查：获取已提取邮件的发送时间集合
existing_mail_dates = db.get_existing_mail_dates()

# 拉取匹配的邮件（带去重检查）
matched_mails = fetch_reimbursement_mails(logger, db_manager=db)

# 处理每封匹配的邮件
for mail_data in matched_mails:
    # 保存到数据库
    email_record = ExtractedEmail(...)
    db.add_extracted_email(email_record)
```

---

### 2. 配置模块（config/）

#### `settings.py` - 配置管理
**职责**：从 .env 文件读取环境变量，进行类型转换和校验

**导出配置**：
```python
# 邮箱配置
IMAP_HOST, IMAP_USER, IMAP_PASS
MAIL_CHECK_FOLDER, MAIL_SEARCH_CRITERIA

# 定时配置
CHECK_INTERVAL, TIME_ZONE

# 日志配置
LOG_LEVEL, LOG_DIR, LOG_MAX_SIZE, LOG_BACKUP_COUNT

# 推送配置
DINGTALK_WEBHOOK, DINGTALK_SECRET, PUSH_SWITCH

# 解析 & 存储配置
PARSE_RULES_JSON_PATH, EXTRACT_ROOT_DIR, CLEAR_DB_ON_STARTUP
```

**核心函数**：
- `validate_email_format(email_str)` - 校验邮箱格式
- `validate_config()` - 严格校验所有配置

#### `logger_config.py` - 日志配置
**职责**：初始化日志系统，支持实时刷盘

**核心函数**：
- `generate_log_filename()` - 生成日志文件名（日期+时分秒+级别）
- `init_logger()` - 初始化日志系统
  - 创建控制台Handler（同步刷新）
  - 创建文件Handler（行缓冲 + 强制刷盘）
  - 重写 emit 方法，每条日志后立即刷盘
  - 注册退出钩子

**日志格式**：
```
%(asctime)s - %(process)d - %(name)s - %(levelname)s - %(message)s
```

---

### 3. 数据库模块（core/database.py）

#### `DatabaseManager` - 数据库管理器
**职责**：管理 SQLite 数据库，提供邮件去重和记录功能

**表结构**：
```sql
-- 已提取邮件记录表
CREATE TABLE extracted_emails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id TEXT UNIQUE NOT NULL,    -- 邮件Message-ID
    subject TEXT,
    sender TEXT,
    rule_id TEXT,
    mail_date TEXT,                      -- 邮件发送时间（用于去重）
    extracted_at TIMESTAMP,
    storage_path TEXT,                   -- 提取目录
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

**核心方法**：

| 方法 | 功能 | 调用者 | 关联逻辑 |
|------|------|--------|---------|
| `_init_database()` | 创建表结构和索引 | `__init__()` | - |
| `is_email_extracted(message_id)` | 检查邮件是否已提取（基础） | - | - |
| `is_email_extracted_with_files(message_id)` | 增强版去重检查（验证文件存在） | - | - |
| `add_extracted_email(email_record)` | 添加新邮件记录 | `main.py` | - |
| `update_extracted_email(email_record)` | 更新已存在的邮件记录 | `main.py` | - |
| `get_extracted_email(message_id)` | 根据Message-ID获取记录 | - | - |
| **`get_existing_mail_dates()`** | **获取已提取且文件存在的邮件发送时间集合，自动清理文件不存在的记录** | `fetch_reimbursement_mails()` | 先通过 `message_id` 删除 extraction_history 记录，再删除 extracted_emails 记录 |
| `clean_invalid_records()` | **手动清理**所有文件不存在的记录 | `clean_invalid_records.py` | 先通过 `message_id` 删除 extraction_history 记录，再删除 extracted_emails 记录 |
| `add_extraction_history(history)` | 添加提取历史 | `main.py` | - |
| `get_statistics()` | 获取统计信息 | - | - |
| `clear_all_data()` | 清空所有数据 | `main.py` | - |

**去重机制（智能预检查）**：
```python
def get_existing_mail_dates(self) -> set:
    """
    获取所有已提取且文件存在的邮件发送时间集合
    用于快速去重检查，避免重复提取
    """
    # 查询所有有 storage_path 或 body_file_path 的记录
    # 验证文件实际存在
    # 返回 mail_date 集合
```

---

### 4. 规则引擎（core/rule_loader.py）

#### `Rule` - 规则模型
**职责**：定义单条匹配规则

**属性**：
```python
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

**核心方法**：
- `match(subject, sender, body)` - 检查邮件是否匹配此规则

#### `RuleLoader` - 规则加载器
**职责**：加载和管理规则配置

**核心方法**：
- `_load_rules()` - 从 JSON 文件加载规则
- `get_enabled_rules()` - 获取所有启用的规则
- `match_rules(subject, sender, body)` - 匹配所有符合条件的规则

**规则配置示例**（rules/parse_rules.json）：
```json
{
  "parse_time_range_days": 20,
  "rules": [
    {
      "rule_id": "rule_002",
      "rule_name": "12306提取",
      "enabled": true,
      "match_conditions": {
        "sender_contains": ["12306", "didifapiao"],
        "subject_contains": [],
        "body_contains": []
      },
      "extract_options": {
        "extract_attachments": true,
        "extract_body": false
      }
    }
  ]
}
```

---

### 5. 邮件拉取模块（core/email_fetcher.py）

#### `parse_reimbursement_mail(msg, rule_loader)` - 解析单封邮件
**职责**：解析邮件内容，使用规则判断是否为目标邮件

**流程**：
```
1. 提取邮件头（Message-ID, Subject, From, Date）
2. 解码邮件头（处理各种编码）
3. 提取邮件正文（支持 multipart/纯文本）
4. 使用规则匹配（RuleLoader.match_rules）
5. 如果匹配，返回邮件数据；否则返回 None
```

**返回数据结构**：
```python
{
    "message_id": "xxx",
    "subject": "邮件主题",
    "sender": "发件人",
    "date": "发送时间",              # 用于去重的唯一标识
    "body": "正文（前200字符）...",
    "matched_rules": [Rule对象]
}
```

#### `fetch_reimbursement_mails(logger, db_manager)` - 拉取邮件
**职责**：连接邮箱，搜索并拉取匹配的邮件（核心业务逻辑）

**流程**：
```
1. 初始化规则加载器
2. 【预检查】获取已提取邮件的发送时间集合
   - db_manager.get_existing_mail_dates()
3. 连接 IMAP 服务器
4. 搜索邮件（时间范围 + 搜索条件）
5. 逐个解析邮件
   - parse_reimbursement_mail()
   - 检查 mail_date 是否在已存在集合中
   - 如果存在，跳过（去重）
   - 如果不存在，创建提取目录并提取内容
6. 标记邮件为已读
7. 返回匹配的邮件列表
```

**去重逻辑（智能预检查）**：
```python
# 预检查阶段
existing_mail_dates = db_manager.get_existing_mail_dates()

# 匹配阶段
for mail in mails:
    mail_date = matched_mail.get('date', '')
    if mail_date in existing_mail_dates:
        logger.info("邮件已提取（基于发送时间匹配），跳过")
        continue  # 跳过已提取的邮件
```

#### `send_mail_summary_notification(matched_mails, time_range_days)` - 发送汇总通知
**职责**：将匹配的邮件汇总后推送到钉钉

---

### 6. 邮件提取模块（core/email_extractor.py）

#### `EmailExtractor` - 邮件提取器
**职责**：提取和保存邮件内容（正文、附件、结构化数据）

**目录结构**：
```
extracted_mails/YYYY-MM-DD_HHMMSS/
├── bodies/{rule_id}/           # 邮件正文HTML
│   └── {md5(message_id)}.html
├── attachments/{rule_id}/      # 邮件附件
│   └── {原文件名}
└── extracted/{rule_id}/        # 结构化数据（JSON）
    └── {md5(message_id)}.json
```

**核心方法**：

| 方法 | 功能 | 输出 |
|------|------|------|
| `create_extraction_dir()` | 创建本次提取的存储目录 | Path |
| `save_email_body()` | 保存邮件正文HTML | bodies/{rule_id}/xxx.html |
| `extract_attachments()` | 提取并保存邮件附件 | attachments/{rule_id}/xxx |
| `save_extracted_content()` | 保存结构化数据（JSON） | extracted/{rule_id}/xxx.json |
| `_extract_html_content()` | 提取邮件HTML内容 | str |
| `_decode_filename()` | 解码附件文件名 | str |

#### `extract_email_full(msg, mail_data, extraction_dir)` - 完整提取
**职责**：完整提取一封邮件（正文、附件、提取内容）

**流程**：
```
1. 创建 EmailExtractor 实例
2. 保存邮件正文HTML -> save_email_body()
3. 提取附件 -> extract_attachments()
4. 保存结构化内容 -> save_extracted_content()
5. 返回提取结果字典
```

**返回数据结构**：
```python
{
    'storage_path': 'extracted_mails/2026-03-11_070000',
    'body_file_path': '.../bodies/rule_002/abc123.html',
    'attachment_count': 2,
    'attachment_paths': ['.../attachments/rule_002/file1.pdf', ...],
    'extracted_content_path': '.../extracted/rule_002/abc123.json'
}
```

---

### 7. 钉钉通知模块（core/dingtalk_notifier.py）

#### `send_dingtalk_message(content)` - 发送钉钉消息
**职责**：通过钉钉机器人发送文本消息

**流程**：
```
1. 检查推送开关（PUSH_SWITCH）
2. 检查 Webhook 配置
3. 如果配置了签名密钥，计算签名
   - timestamp + secret -> HMAC-SHA256 -> Base64
4. 构建请求数据（msgtype: text）
5. 发送 POST 请求到钉钉 API
6. 检查响应（errcode == 0）
```

---

### 8. 工具函数（utils/）

#### `header_decoder.py` - 邮件头解码
- `decode_mail_header(header)` - 解码邮件头（处理编码）

#### `file_utils.py` - 文件工具
- `ensure_log_dir(log_dir)` - 确保日志目录存在
- `check_file_exists(file_path)` - 检查文件是否存在
- `normalize_path(path)` - 规范化路径分隔符

---

## 完整调用关系图

```
main()
 │
 ├─→ init_logger()                          [config/logger_config.py]
 │
 ├─→ DatabaseManager(db_path)               [core/database.py]
 │   └─→ _init_database()
 │       ├─→ 创建 extracted_emails 表
 │       ├─→ 创建 extraction_history 表
 │       └─→ 创建索引
 │
 ├─→ RuleLoader(rules_path)                [core/rule_loader.py]
 │   └─→ _load_rules()
 │       ├─→ 加载 JSON 配置
 │       └─→ 解析规则列表
 │
 └─→ while True: 主循环
     │
     ├─→ fetch_reimbursement_mails(logger, db_manager)  [core/email_fetcher.py]
     │   │
     │   ├─→ RuleLoader.get_enabled_rules()
     │   │
     │   ├─→ db_manager.get_existing_mail_dates()       【预检查去重】
     │   │
     │   ├─→ 连接 IMAP 服务器
     │   │
     │   ├─→ 搜索邮件（SINCE {date}）
     │   │
     │   └─→ 逐个处理邮件
     │       │
     │       ├─→ parse_reimbursement_mail(msg, rule_loader)
     │       │   ├─→ decode_mail_header()               [utils/header_decoder.py]
     │       │   ├─→ 提取邮件正文
     │       │   └─→ rule_loader.match_rules()
     │       │       └─→ Rule.match()
     │       │
     │       ├─→ 检查 mail_date in existing_mail_dates   【去重判断】
     │       │
     │       └─→ extract_email_full(msg, mail_data, extraction_dir)  [core/email_extractor.py]
     │           │
     │           ├─→ EmailExtractor()
     │           │
     │           ├─→ extractor.create_extraction_dir()
     │           │
     │           ├─→ extractor.save_email_body()
     │           │
     │           ├─→ extractor.extract_attachments()
     │           │
     │           └─→ extractor.save_extracted_content()
     │
     ├─→ 遍历 matched_mails
     │   │
     │   ├─→ db_manager.add_extracted_email(record)
     │   │   └─→ INSERT INTO extracted_emails
     │   │
     │   ├─→ db_manager.add_extraction_history(history)
     │   │   └─→ INSERT INTO extraction_history
     │   │
     │   └─→ send_mail_summary_notification(matched_mails, time_range_days)
     │       └─→ send_dingtalk_message(content)         [core/dingtalk_notifier.py]
     │           ├─→ 计算签名（HMAC-SHA256）
     │           └─→ requests.post(webhook_url)
     │
     └─→ time.sleep(CHECK_INTERVAL)
```

---

## 去重机制详解

### 三层去重防护

1. **预检查阶段**（`get_existing_mail_dates()`）
   - 查询数据库中所有已提取的邮件发送时间
   - 验证文件实际存在性
   - 返回 `mail_date` 集合用于快速匹配

2. **匹配阶段**（`fetch_reimbursement_mails()`）
   - 对每封匹配的邮件，检查 `mail_date in existing_mail_dates`
   - 如果存在，跳过提取
   - 如果不存在，继续处理

3. **记录阶段**（`add_extracted_email()` / `update_extracted_email()`）
   - 记录存在则更新文件路径
   - 记录不存在则插入新记录
   - 使用 `UNIQUE` 约束防止重复

### 为什么使用 `mail_date` 作为唯一标识？

- **更可靠**：邮件发送时间由邮件服务器生成，比 `message_id` 更稳定
- **易去重**：同一封邮件的发送时间始终相同
- **跨会话**：即使程序重启，发送时间也不变

---

## 环境变量配置

### 必填配置

```bash
# 邮箱配置
IMAP_HOST=imap.example.com
IMAP_USER=user@example.com
IMAP_PASS=password

# 目录配置
LOG_DIR=./logs
PARSE_RULES_JSON_PATH=./rules/parse_rules.json
EXTRACT_ROOT_DIR=./extracted_mails
```

### 可选配置

```bash
# 邮箱配置
MAIL_CHECK_FOLDER=INBOX
MAIL_SEARCH_CRITERIA=UNSEEN

# 定时配置
CHECK_INTERVAL=60
TIME_ZONE=Asia/Shanghai

# 日志配置
LOG_LEVEL=INFO
LOG_MAX_SIZE=10485760
LOG_BACKUP_COUNT=5

# 推送配置
DINGTALK_WEBHOOK=https://oapi.dingtalk.com/robot/send?access_token=xxx
DINGTALK_SECRET=SECxxxxxxxxxxx
PUSH_SWITCH=True

# 数据库配置
CLEAR_DB_ON_STARTUP=False
```

---

## Git 提交历史

### 最新提交

1. **`e0f600d`** - feat: 实现基于邮件发送时间的智能去重优化
   - 新增 `mail_date` 字段作为邮件唯一标识
   - 实现预检查去重机制
   - 智能目录创建（只在有新邮件时创建）

2. **`c68fd49`** - feat: 实现TODO 3文件提取和增强版去重逻辑
   - 实现文件提取和分类存储模块
   - 集成数据库去重和记录功能
   - 新增12个测试脚本

3. **`4108076`** - 规则提取完成
4. **`86417a6`** - 配置文件为python版本
5. **`9e19c2d`** - 环境依赖搭建

---

## 扩展建议

### 1. 新增规则类型
在 `rules/parse_rules.json` 中添加新规则：
```json
{
  "rule_id": "rule_004",
  "rule_name": "新规则",
  "enabled": true,
  "match_conditions": { ... },
  "extract_options": { ... }
}
```

### 2. 新增推送渠道
在 `core/` 下新增 `wechat_notifier.py`，参考 `dingtalk_notifier.py`

### 3. 新增数据源
在 `core/` 下新增 `exchange_fetcher.py`（支持 Exchange 协议）

---

## 故障排查

### 日志未写入
1. 检查 `LOG_DIR` 是否存在且有写权限
2. 检查 `LOG_LEVEL` 是否正确
3. 查看日志文件是否被其他进程占用

### 邮件未拉取
1. 检查 IMAP 连接是否正常
2. 检查 `MAIL_SEARCH_CRITERIA` 是否正确
3. 检查规则是否启用（`enabled: true`）
4. 查看日志中的匹配结果

### 钉钉通知未发送
1. 检查 `PUSH_SWITCH` 是否为 `True`
2. 检查 `DINGTALK_WEBHOOK` 和 `DINGTALK_SECRET` 是否正确
3. 检查网络连接

### 文件重复提取
1. 检查数据库中 `mail_date` 字段是否存在
2. 检查文件是否真实存在
3. 清空数据库重启（`CLEAR_DB_ON_STARTUP=True`）

---

**最后更新**: 2026-03-11
