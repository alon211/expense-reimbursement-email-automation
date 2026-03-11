# 部署架构

**最后更新**: 2026-03-11

本文档提供项目的部署指南，包括本地部署和 Docker 容器化部署。

---

## 目录

1. [本地部署](#本地部署)
2. [Docker 部署](#docker-部署)
3. [环境变量配置](#环境变量配置)
4. [敏感信息存储](#敏感信息存储)
5. [故障排查](#故障排查)

---

## 本地部署

### 前置要求

- **Python**: 3.9 或更高版本
- **操作系统**: Windows / Linux / macOS
- **IMAP 邮箱访问权限**:
  - IMAP 服务器地址
  - IMAP 端口（通常 143 或 993）
  - 用户名和密码
  - 部分邮箱需要开启"应用专用密码"
- **钉钉机器人**（可选）:
  - 钉钉机器人 Webhook URL
  - 钉钉机器人签名密钥（如果启用了签名）

---

### 安装步骤

#### 1. 克隆项目

```bash
git clone <repository_url>
cd expense-reimbursement-email-automation
```

#### 2. 创建虚拟环境

**Windows**:
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux / macOS**:
```bash
python3 -m venv venv
source venv/bin/activate
```

#### 3. 安装依赖

```bash
pip install -r requirements.txt
```

#### 4. 配置环境变量

复制示例环境变量文件（如果存在）:
```bash
cp .env.example .env
```

编辑 `.env` 文件，填写配置项（详见[环境变量配置](#环境变量配置)）

#### 5. 创建必要目录

```bash
mkdir logs
mkdir extracted_mails
```

#### 6. 测试运行

```bash
python main.py
```

如果一切正常，您应该看到类似以下的日志输出:
```
2026-03-11 10:00:00 - 12345 - __main__ - INFO - 邮件自动化服务启动
2026-03-11 10:00:00 - 12345 - __main__ - INFO - 加载规则: ./rules/parse_rules.json
2026-03-11 10:00:00 - 12345 - __main__ - INFO - 初始化数据库: ./extracted_mails/data.db
2026-03-11 10:00:00 - 12345 - __main__ - INFO - 开始拉取邮件...
```

---

## Docker 部署

### 前置要求

- **Docker**: 20.10 或更高版本
- **docker-compose**: 1.29 或更高版本

---

### 使用 docker-compose 部署

#### 1. 构建镜像

```bash
docker-compose build
```

#### 2. 配置环境变量

创建 `.env` 文件（详见[环境变量配置](#环境变量配置)）

#### 3. 启动服务

```bash
# 前台运行（查看日志）
docker-compose up

# 后台运行
docker-compose up -d
```

#### 4. 查看日志

```bash
# 查看所有日志
docker-compose logs -f

# 查看最近 100 行日志
docker-compose logs --tail=100
```

#### 5. 停止服务

```bash
docker-compose down
```

#### 6. 重启服务

```bash
docker-compose restart
```

---

### 数据持久化

docker-compose.yml 配置示例：

```yaml
version: '3.8'

services:
  email-automation:
    build: .
    container_name: expense-email-automation
    restart: unless-stopped
    environment:
      - IMAP_HOST=${IMAP_HOST}
      - IMAP_USER=${IMAP_USER}
      - IMAP_PASS=${IMAP_PASS}
      - CHECK_INTERVAL=${CHECK_INTERVAL:-60}
      - TIME_ZONE=${TIME_ZONE:-Asia/Shanghai}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - PUSH_SWITCH=${PUSH_SWITCH:-True}
      - DINGTALK_WEBHOOK=${DINGTALK_WEBHOOK}
      - DINGTALK_SECRET=${DINGTALK_SECRET}
    volumes:
      # 日志目录
      - ./logs:/app/logs
      # 提取文件目录
      - ./extracted_mails:/app/extracted_mails
      # 规则配置
      - ./rules:/app/rules
    tz: Asia/Shanghai
```

**注意**:
- 数据库文件默认存储在 `./extracted_mails/data.db`
- 日志文件存储在 `./logs/` 目录
- 提取的邮件存储在 `./extracted_mails/` 目录

---

## 环境变量配置

### 必填配置

```bash
# 邮箱配置
IMAP_HOST=imap.example.com          # IMAP 服务器地址
IMAP_USER=user@example.com          # IMAP 用户名
IMAP_PASS=password                  # IMAP 密码

# 目录配置
LOG_DIR=./logs                      # 日志目录
PARSE_RULES_JSON_PATH=./rules/parse_rules.json  # 规则配置文件
EXTRACT_ROOT_DIR=./extracted_mails  # 提取文件根目录
```

### 可选配置

```bash
# 邮箱配置
MAIL_CHECK_FOLDER=INBOX             # 邮件文件夹（默认 INBOX）
MAIL_SEARCH_CRITERIA=UNSEEN         # 搜索条件（默认 UNSEEN）

# 定时配置
CHECK_INTERVAL=60                   # 检查间隔（秒，默认 60）
TIME_ZONE=Asia/Shanghai             # 时区（默认 Asia/Shanghai）

# 日志配置
LOG_LEVEL=INFO                      # 日志级别（DEBUG/INFO/WARNING/ERROR，默认 INFO）
LOG_MAX_SIZE=10485760               # 日志文件最大大小（字节，默认 10MB）
LOG_BACKUP_COUNT=5                  # 日志备份数量（默认 5）

# 推送配置
DINGTALK_WEBHOOK=https://oapi.dingtalk.com/robot/send?access_token=xxx
DINGTALK_SECRET=SECxxxxxxxxxxx      # 钉钉签名密钥（如果启用了签名）
PUSH_SWITCH=True                    # 推送开关（True/False，默认 True）

# 数据库配置
CLEAR_DB_ON_STARTUP=False           # 启动时清空数据库（True/False，默认 False）
```

---

## 敏感信息存储

### 邮箱密码

**推荐方式**: 使用环境变量（.env 文件）

```bash
# .env 文件
IMAP_PASS=your_email_password
```

**安全建议**:
- ✅ 将 `.env` 文件添加到 `.gitignore`
- ✅ 不要在代码中硬编码密码
- ✅ 使用应用专用密码（如果邮箱支持）
- ✅ 定期更换密码

---

### 钉钉 Webhook 和密钥

**推荐方式**: 使用环境变量（.env 文件）

```bash
# .env 文件
DINGTALK_WEBHOOK=https://oapi.dingtalk.com/robot/send?access_token=xxx
DINGTALK_SECRET=SECxxxxxxxxxxx
```

**安全建议**:
- ✅ 将 `.env` 文件添加到 `.gitignore`
- ✅ 不要在代码中硬编码 Webhook URL
- ✅ 启用钉钉签名验证（推荐）
- ✅ 定期更换密钥

---

## 常见邮箱配置

### Gmail

```bash
IMAP_HOST=imap.gmail.com
IMAP_USER=your_email@gmail.com
IMAP_PASS=your_app_password  # 需要生成应用专用密码
MAIL_CHECK_FOLDER=INBOX
```

**注意**: Gmail 需要开启"允许不够安全的应用访问"或生成应用专用密码

---

### QQ 邮箱

```bash
IMAP_HOST=imap.qq.com
IMAP_USER=your_email@qq.com
IMAP_PASS=authorization_code  # 授权码，不是 QQ 密码
MAIL_CHECK_FOLDER=INBOX
```

**注意**: QQ 邮箱需要开启 IMAP 服务并生成授权码

---

### 163 邮箱

```bash
IMAP_HOST=imap.163.com
IMAP_USER=your_email@163.com
IMAP_PASS=authorization_code  # 授权码，不是 163 密码
MAIL_CHECK_FOLDER=INBOX
```

**注意**: 163 邮箱需要开启 IMAP 服务并设置授权码

---

### 企业邮箱（Exchange）

```bash
IMAP_HOST=imap.exchanger.com
IMAP_USER=your_email@company.com
IMAP_PASS=your_password
MAIL_CHECK_FOLDER=INBOX
```

**注意**: 某些企业邮箱可能需要额外配置（如 SSL 端口）

---

## 故障排查

### 问题 1: 无法连接到 IMAP 服务器

**症状**:
```
ERROR: IMAP 连接失败: [Errno 111] Connection refused
```

**可能原因**:
1. IMAP 服务器地址错误
2. IMAP 端口被防火墙阻止
3. 网络连接问题

**解决方案**:
1. 检查 `IMAP_HOST` 配置是否正确
2. 尝试使用 telnet 测试连接：
   ```bash
   telnet imap.example.com 143
   telnet imap.example.com 993
   ```
3. 检查防火墙设置

---

### 问题 2: 邮箱认证失败

**症状**:
```
ERROR: IMAP 认证失败: Authentication failed
```

**可能原因**:
1. 用户名或密码错误
2. 需要使用应用专用密码/授权码
3. IMAP 服务未开启

**解决方案**:
1. 检查 `IMAP_USER` 和 `IMAP_PASS` 配置
2. 确认邮箱已开启 IMAP 服务
3. 使用应用专用密码（Gmail、QQ 邮箱等）

---

### 问题 3: 没有匹配到邮件

**症状**:
```
INFO: 没有匹配到新邮件
```

**可能原因**:
1. 规则配置不正确
2. 邮件不在搜索时间范围内
3. 邮件已被标记为已读

**解决方案**:
1. 检查 `rules/parse_rules.json` 配置
2. 调整 `parse_time_range_days` 参数
3. 修改 `MAIL_SEARCH_CRITERIA` 为 `ALL`

---

### 问题 4: 钉钉消息推送失败

**症状**:
```
ERROR: 钉钉消息推送失败: ...
```

**可能原因**:
1. Webhook URL 错误
2. 签名密钥错误
3. 网络连接问题

**解决方案**:
1. 检查 `DINGTALK_WEBHOOK` 配置
2. 检查 `DINGTALK_SECRET` 配置（如果启用了签名）
3. 测试钉钉机器人是否正常工作

---

### 问题 5: 数据库错误

**症状**:
```
ERROR: 数据库操作失败: no such table: extracted_emails
```

**可能原因**:
1. 数据库文件不存在
2. 数据库表未初始化

**解决方案**:
1. 删除数据库文件 `data.db`
2. 重启程序，自动初始化数据库
3. 或手动运行初始化脚本

---

### 问题 6: 文件写入权限错误

**症状**:
```
ERROR: 无法创建目录: Permission denied
```

**可能原因**:
1. 目录权限不足
2. 磁盘空间不足

**解决方案**:
1. 检查目录权限：
   ```bash
   ls -la logs/
   ls -la extracted_mails/
   ```
2. 修改目录权限：
   ```bash
   chmod 755 logs/
   chmod 755 extracted_mails/
   ```
3. 检查磁盘空间：
   ```bash
   df -h
   ```

---

## 监控和维护

### 日志查看

**查看最新日志**:
```bash
tail -f logs/app_*.log
```

**查看错误日志**:
```bash
grep "ERROR" logs/app_*.log
```

---

### 数据库维护

**备份数据库**:
```bash
cp extracted_mails/data.db extracted_mails/data.db.backup
```

**清理数据库**:
```bash
python clean_invalid_records.py
```

**重置数据库**:
1. 设置环境变量 `CLEAR_DB_ON_STARTUP=True`
2. 重启程序

---

### 文件清理

**清理旧的提取文件**:
```bash
# 删除 30 天前的提取目录
find extracted_mails/ -type d -mtime +30 -exec rm -rf {} +
```

**清理旧日志**:
```bash
# 删除 30 天前的日志
find logs/ -type f -name "*.log" -mtime +30 -delete
```

---

## 性能优化

### 调整检查间隔

根据实际需求调整 `CHECK_INTERVAL`：

```bash
# 频繁检查（30 秒）
CHECK_INTERVAL=30

# 正常检查（60 秒，默认）
CHECK_INTERVAL=60

# 低频检查（5 分钟）
CHECK_INTERVAL=300
```

**注意**: 频繁检查会增加服务器负载

---

### 调整日志级别

生产环境建议使用 `INFO` 或 `WARNING`：

```bash
LOG_LEVEL=INFO
```

开发环境可以使用 `DEBUG`：

```bash
LOG_LEVEL=DEBUG
```

---

## 相关文档

- [系统架构总览](system-overview.md) - 高层架构视图
- [模块参考手册](module-reference.md) - 各模块详细说明
- [数据流图](data-flow.md) - 数据流详细说明
- [API 接口文档](api-reference.md) - 公共 API 说明
- [CLAUDE.md](../CLAUDE.md) - 主项目文档
