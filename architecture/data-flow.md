# 数据流图

**最后更新**: 2026-03-11

本文档详细说明系统中各种数据的流动路径和转换过程。

---

## 目录

1. [邮件处理主流程](#邮件处理主流程)
2. [数据流向详细说明](#数据流向详细说明)
3. [数据转换过程](#数据转换过程)
4. [数据库数据流](#数据库数据流)
5. [文件系统数据流](#文件系统数据流)
6. [钉钉推送数据流](#钉钉推送数据流)

---

## 邮件处理主流程

### 高层流程图

```
┌─────────────┐
│  用户邮箱   │
│  (IMAP)     │
└──────┬──────┘
       │
       │ ① IMAP 连接 & 邮件搜索
       ▼
┌─────────────────────────────┐
│  main.py 主循环              │
│  - 定时任务调度              │
│  - 时区支持                  │
└──────┬──────────────────────┘
       │
       │ ② 拉取邮件
       ▼
┌─────────────────────────────┐
│  email_fetcher.py            │
│  - IMAP 连接                 │
│  - 邮件搜索 (SINCE {date})   │
│  - 逐个解析                  │
└──────┬──────────────────────┘
       │
       │ ③ 规则匹配
       ▼
┌─────────────────────────────┐
│  rule_loader.py              │
│  - 加载规则                  │
│  - 多维度匹配                │
│  - 返回匹配规则列表          │
└──────┬──────────────────────┘
       │
       ├────→ ④a 匹配失败 → 跳过
       │
       └─→ ④b 匹配成功
            │
            │ ⑤ 去重检查
            ▼
      ┌─────────────────────┐
      │  database.py         │
      │  - get_existing_     │
      │    mail_dates()      │
      └──────┬──────────────┘
             │
             ├─→ ⑥a 已存在 → 跳过
             │
             └─→ ⑥b 新邮件
                  │
                  │ ⑦ 内容提取
                  ▼
            ┌─────────────────────┐
            │  email_extractor.py │
            │  - 保存正文 HTML     │
            │  - 提取附件         │
            │  - 解压压缩包       │
            │  - 导出 JSON        │
            └──────┬──────────────┘
                   │
                   │ ⑧ 数据库记录
                   ▼
            ┌─────────────────────┐
            │  database.py         │
            │  - add_extracted_    │
            │    email()           │
            │  - add_extraction_   │
            │    history()         │
            └──────┬──────────────┘
                   │
                   │ ⑨ 消息推送
                   ▼
            ┌─────────────────────┐
            │  dingtalk_notifier  │
            │  .py                │
            │  - 发送汇总通知      │
            └──────┬──────────────┘
                   │
                   └─→ ⑩ 完成
```

---

## 数据流向详细说明

### ① IMAP 连接 & 邮件搜索

**数据来源**: 用户邮箱（IMAP 服务器）

**数据流**:
```
用户邮箱 → IMAP 服务器 → email_fetcher.py
```

**输入数据**:
- IMAP 服务器地址（IMAP_HOST）
- 用户名（IMAP_USER）
- 密码（IMAP_PASS）
- 搜索文件夹（MAIL_CHECK_FOLDER，默认 INBOX）
- 搜索条件（MAIL_SEARCH_CRITERIA，默认 UNSEEN）

**输出数据**:
- 邮件 ID 列表

---

### ② 拉取邮件

**数据流**:
```
email_fetcher.py → 邮件对象列表
```

**处理步骤**:
1. 连接 IMAP 服务器
2. 选择文件夹
3. 搜索邮件（SINCE {date}）
4. 获取邮件 ID 列表

**输出数据**:
- 邮件 ID 列表

---

### ③ 规则匹配

**数据流**:
```
邮件对象 → parse_reimbursement_mail() → 邮件数据字典
```

**处理步骤**:
1. 提取邮件头（Message-ID, Subject, From, Date）
2. 解码邮件头（处理各种编码）
3. 提取邮件正文（text/plain + text/html）
4. 使用规则匹配（RuleLoader.match_rules）
5. 如果匹配，返回邮件数据；否则返回 None

**输出数据结构**:
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

---

### ④ 规则匹配结果

**数据流**:
```
parse_reimbursement_mail() → 匹配结果
```

**输出**:
- **匹配失败**: 返回 `None`，跳过该邮件
- **匹配成功**: 返回邮件数据字典，继续处理

---

### ⑤ 去重检查

**数据流**:
```
邮件数据 → database.py → 去重结果
```

**处理步骤**:
1. 获取已提取邮件的发送时间集合
   ```python
   existing_mail_dates = db.get_existing_mail_dates()
   ```
2. 检查当前邮件的 `mail_date` 是否在集合中
   ```python
   if mail_date in existing_mail_dates:
       # 已提取，跳过
   else:
       # 新邮件，继续提取
   ```

---

### ⑥ 去重结果

**数据流**:
```
去重检查 → 处理决策
```

**输出**:
- **⑥a 已存在**: 跳过提取，记录到 extraction_history（action=skipped）
- **⑥b 新邮件**: 继续内容提取流程

---

### ⑦ 内容提取

**数据流**:
```
邮件对象 → email_extractor.py → 提取结果
```

**处理步骤**:
1. 创建提取目录
   ```python
   extraction_dir = extractor.create_extraction_dir()
   # → extracted_mails/2026-03-11_070000/
   ```

2. 保存邮件正文 HTML
   ```python
   body_file = extractor.save_email_body(msg, mail_data, extraction_dir)
   # → bodies/{rule_id}/{md5(message_id)}.html
   ```

3. 提取附件
   ```python
   attachments = extractor.extract_attachments(msg, mail_data, extraction_dir)
   # → attachments/{rule_id}/{原文件名}
   ```

4. 解压压缩文件（如果启用）
   ```python
   extracted_archives = extractor.extract_archives(attachments)
   # → attachments/{rule_id}/{name}_extracted.{ext}/
   ```

5. 保存结构化数据
   ```python
   json_file = extractor.save_extracted_content(mail_data, extraction_dir)
   # → extracted/{rule_id}/{md5(message_id)}.json
   ```

**输出数据结构**:
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

### ⑧ 数据库记录

**数据流**:
```
提取结果 → database.py → 数据库
```

**处理步骤**:
1. 创建邮件记录
   ```python
   email_record = ExtractedEmail(
       message_id=mail_data['message_id'],
       subject=mail_data['subject'],
       sender=mail_data['sender'],
       rule_id=matched_rules[0].rule_id,
       mail_date=mail_data['date'],
       extracted_at=datetime.now(),
       storage_path=result['storage_path'],
       attachment_count=result['attachment_count'],
       body_file_path=result['body_file_path']
   )
   ```

2. 添加到数据库
   ```python
   db.add_extracted_email(email_record)
   # INSERT INTO extracted_emails ...
   ```

3. 记录提取历史
   ```python
   history = ExtractionHistory(
       message_id=mail_data['message_id'],
       rule_id=matched_rules[0].rule_id,
       action='matched',
       created_at=datetime.now()
   )
   db.add_extraction_history(history)
   # INSERT INTO extraction_history ...
   ```

---

### ⑨ 消息推送

**数据流**:
```
matched_mails 列表 → dingtalk_notifier.py → 钉钉机器人
```

**处理步骤**:
1. 汇总匹配的邮件
   ```python
   summary = f"发现 {len(matched_mails)} 封新邮件:\n"
   for mail in matched_mails:
       summary += f"- {mail['subject']}\n"
   ```

2. 发送钉钉消息
   ```python
   send_dingtalk_message(summary)
   ```

---

### ⑩ 完成

**数据流**:
```
处理完成 → 等待下一个定时周期
```

**清理工作**:
- 关闭 IMAP 连接
- 刷新日志
- 等待 `CHECK_INTERVAL` 秒

---

## 数据转换过程

### 邮件头解码

**输入**: 编码的邮件头（各种字符编码）

**处理**: `decode_mail_header()`
```python
# 解码邮件头（处理 ISO-8859-1, GBK, UTF-8 等编码）
decoded = decode_mail_header(raw_header)
```

**输出**: UTF-8 编码的字符串

---

### 邮件正文提取

**输入**: 邮件对象（multipart）

**处理**: `_extract_html_content()`
```python
# 提取 HTML 内容（优先级高于 text/plain）
html_content = _extract_html_content(msg)
```

**输出**: HTML 字符串

---

### 附件解码

**输入**: 编码的附件数据（base64）

**处理**:
```python
# 解码附件
decoded_data = base64.b64decode(encoded_data)
```

**输出**: 二进制数据 → 写入文件

---

### 结构化数据导出

**输入**: 邮件数据字典

**处理**: `save_extracted_content()`
```python
# 导出为 JSON
json_data = {
    "message_id": mail_data['message_id'],
    "subject": mail_data['subject'],
    "sender": mail_data['sender'],
    "date": mail_data['date'],
    "body": mail_data['body'],
    "matched_rules": [r.rule_id for r in mail_data['matched_rules']],
    "attachments": attachment_paths,
    "extracted_at": datetime.now().isoformat()
}
```

**输出**: JSON 文件

---

## 数据库数据流

### 数据写入流程

```
邮件数据
    ↓
add_extracted_email()
    ↓
INSERT INTO extracted_emails
    ↓
数据库文件 (SQLite)
```

### 数据读取流程

```
数据库查询
    ↓
get_existing_mail_dates()
    ↓
SELECT mail_date FROM extracted_emails
    ↓
验证文件存在性
    ↓
返回 mail_date 集合
```

### 数据清理流程

```
无效记录检测
    ↓
clean_invalid_records()
    ↓
DELETE FROM extraction_history (WHERE message_id)
    ↓
DELETE FROM extracted_emails (WHERE id)
    ↓
数据库清理完成
```

---

## 文件系统数据流

### 文件写入流程

```
提取目录创建
    ↓
bodies/{rule_id}/        → 邮件正文 HTML
attachments/{rule_id}/   → 邮件附件
extracted/{rule_id}/     → 结构化数据 JSON
```

### 文件验证流程

```
数据库记录
    ↓
check_file_exists()
    ↓
Path(file_path).exists()
    ↓
返回验证结果
```

---

## 钉钉推送数据流

### 消息发送流程

```
matched_mails 列表
    ↓
send_mail_summary_notification()
    ↓
汇总消息内容
    ↓
send_dingtalk_message()
    ↓
计算签名（HMAC-SHA256）
    ↓
POST 请求 → 钉钉 API
    ↓
响应处理（errcode == 0）
```

---

## 数据流图例

### 符号说明

```
→   数据流向
└→  条件分支（True）
├→  条件分支（False）
⚪   处理节点
◆   判断节点
```

---

## 性能考虑

### 数据流优化

1. **预检查去重**: 在邮件拉取前先获取已提取邮件集合，避免重复解析
2. **批量操作**: 数据库操作使用事务，减少 I/O
3. **文件写入**: 使用行缓冲 + 强制刷盘，确保数据完整性

### 数据量控制

1. **邮件搜索**: 使用 `SINCE {date}` 限制搜索范围
2. **正文截取**: 只保存前 200 字符到数据库
3. **附件大小**: 可配置附件大小限制

---

## 故障恢复

### 数据一致性

1. **数据库事务**: 确保写入原子性
2. **文件验证**: 去重时验证文件实际存在
3. **自动清理**: 定期清理文件不存在的记录

### 错误处理

1. **IMAP 连接失败**: 记录错误日志，等待下次重试
2. **规则解析失败**: 使用默认规则，继续处理
3. **文件写入失败**: 记录错误，跳过该文件
4. **钉钉推送失败**: 不影响主流程，记录错误

---

## 相关文档

- [系统架构总览](system-overview.md) - 高层架构视图
- [模块参考手册](module-reference.md) - 各模块详细说明
- [API 接口文档](api-reference.md) - 公共 API 说明
- [CLAUDE.md](../CLAUDE.md) - 主项目文档
