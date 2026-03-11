# Docker 部署指南

**最后更新**: 2026-03-11

本文档介绍如何使用Docker部署报销邮件自动化服务。

---

## 前置要求

- **Docker**: 20.10 或更高版本
- **docker-compose**: 1.29 或更高版本

### 检查安装

```bash
docker --version
docker-compose --version
```

---

## 快速开始

### 1. 准备配置文件

复制并配置环境变量：

```bash
# 复制示例配置文件（如果存在）
cp .env.example .env

# 或者创建新的 .env 文件
cat > .env << 'EOF'
# 邮箱配置
IMAP_HOST=imap.example.com
IMAP_USER=your_email@example.com
IMAP_PASS=your_password

# 定时配置
CHECK_INTERVAL=60
TIME_ZONE=Asia/Shanghai

# 日志配置
LOG_LEVEL=INFO

# 推送配置（可选）
DINGTALK_WEBHOOK=https://oapi.dingtalk.com/robot/send?access_token=xxx
DINGTALK_SECRET=SECxxxxxxxxxxx
PUSH_SWITCH=True

# 数据库配置
CLEAR_DB_ON_STARTUP=False
EOF
```

### 2. 创建必要目录

```bash
mkdir -p logs extracted_mails rules
```

### 3. 配置规则文件

确保 `rules/parse_rules.json` 文件存在：

```bash
# 如果不存在，创建示例规则
cat > rules/parse_rules.json << 'EOF'
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
EOF
```

### 4. 构建镜像

```bash
# 构建Docker镜像
docker-compose build
```

### 5. 启动服务

```bash
# 启动服务（前台运行，查看日志）
docker-compose up

# 或后台运行
docker-compose up -d
```

### 6. 查看日志

```bash
# 查看实时日志
docker-compose logs -f

# 查看最近100行日志
docker-compose logs --tail=100
```

---

## 管理命令

### 查看运行状态

```bash
# 查看容器状态
docker-compose ps

# 查看容器详情
docker inspect email-automation-service
```

### 停止和启动

```bash
# 停止服务
docker-compose stop

# 启动服务
docker-compose start

# 重启服务
docker-compose restart

# 停止并删除容器
docker-compose down

# 停止并删除容器及数据卷
docker-compose down -v
```

### 进入容器

```bash
# 进入容器Shell（调试用）
docker-compose exec email-service bash

# 查看容器内文件
docker-compose exec email-service ls -la /app/extracted_mails
```

---

## 数据持久化

### 挂载卷说明

服务使用以下卷进行数据持久化：

| 卷路径 | 容器路径 | 说明 |
|--------|----------|------|
| `./logs` | `/app/logs` | 日志文件目录 |
| `./extracted_mails` | `/app/extracted_mails` | 提取文件和数据库目录 |
| `./rules` | `/app/rules` | 规则配置文件目录 |

### 备份数据

```bash
# 备份数据库
cp extracted_mails/data.db extracted_mails/data.db.backup

# 备份整个目录
tar -czf backup-$(date +%Y%m%d).tar.gz extracted_mails/ logs/ rules/
```

### 恢复数据

```bash
# 恢复数据库
cp extracted_mails/data.db.backup extracted_mails/data.db

# 恢复整个目录
tar -xzf backup-20260311.tar.gz
```

---

## 常见问题

### 问题1: 容器无法启动

**症状**：
```
ERROR: for email-service  Cannot start service email-service: ...
```

**解决方案**：

1. 检查端口占用：
   ```bash
   # Windows
   netstat -ano | findstr :8000

   # Linux/Mac
   lsof -i :8000
   ```

2. 检查日志：
   ```bash
   docker-compose logs email-service
   ```

3. 检查配置文件：
   ```bash
   # 验证.env文件存在
   ls -la .env

   # 验证规则文件存在
   ls -la rules/parse_rules.json
   ```

### 问题2: 无法连接IMAP服务器

**症状**：
```
ERROR: IMAP 连接失败: [Errno 111] Connection refused
```

**解决方案**：

1. 检查网络连接：
   ```bash
   # 进入容器
   docker-compose exec email-service bash

   # 测试网络
   ping imap.example.com
   telnet imap.example.com 143
   telnet imap.example.com 993
   ```

2. 检查环境变量：
   ```bash
   docker-compose exec email-service env | grep IMAP
   ```

3. 检查防火墙设置

### 问题3: 文件权限错误

**症状**：
```
ERROR: 无法创建目录: Permission denied
```

**解决方案**：

1. 修改目录权限：
   ```bash
   chmod 755 logs/ extracted_mails/ rules/
   ```

2. 使用用户ID运行（Linux）：
   ```yaml
   # 在 docker-compose.yml 中添加
   user: "${UID}:${GID}"
   ```

### 问题4: 时区不正确

**症状**：定时任务执行时间不准确

**解决方案**：

检查时区配置：
```bash
docker-compose exec email-service date
docker-compose exec email-service env | grep TZ
```

修改 `.env` 文件：
```bash
TZ=Asia/Shanghai
```

重启服务：
```bash
docker-compose restart
```

---

## 生产环境优化

### 1. 资源限制

在 `docker-compose.yml` 中添加资源限制：

```yaml
services:
  email-service:
    # ... 其他配置
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
```

### 2. 日志轮转

已配置日志轮转（最大10MB，保留5个文件）：

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "5"
```

### 3. 健康检查

已配置健康检查（每30秒检查）：

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD pgrep -f "python.*main.py" || exit 1
```

查看健康状态：
```bash
docker inspect email-automation-service | grep -A 10 Health
```

### 4. 自动重启

已配置自动重启（除非手动停止）：

```yaml
restart: unless-stopped
```

---

## 监控和调试

### 查看资源使用

```bash
# 查看容器资源使用情况
docker stats email-automation-service

# 查看磁盘使用
docker-compose exec email-service du -sh /app/extracted_mails
```

### 查看日志

```bash
# 实时日志
docker-compose logs -f

# 按时间过滤
docker-compose logs --since 1h

# 按级别过滤
docker-compose logs | grep ERROR
docker-compose logs | grep INFO
```

### 调试模式

修改 `.env` 文件启用调试日志：

```bash
LOG_LEVEL=DEBUG
```

重启服务：
```bash
docker-compose restart
```

---

## 更新和升级

### 更新镜像

```bash
# 拉取最新代码
git pull

# 重新构建镜像
docker-compose build

# 重启服务
docker-compose down
docker-compose up -d
```

### 修改配置

```bash
# 编辑配置文件
vi .env

# 重启服务使配置生效
docker-compose restart
```

### 修改规则

```bash
# 编辑规则文件
vi rules/parse_rules.json

# 重启服务使规则生效
docker-compose restart
```

---

## 卸载

### 完全卸载

```bash
# 停止并删除容器和卷
docker-compose down -v

# 删除镜像
docker rmi expense-reimbursement-email-automation_email-service

# 删除数据和配置（谨慎！）
rm -rf logs/ extracted_mails/ .env
```

---

**相关文档**：
- [环境变量配置](../architecture/deployment.md#环境变量配置)
- [故障排查指南](../CLAUDE.md#故障排查)
- [主项目文档](../CLAUDE.md)
