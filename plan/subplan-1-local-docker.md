# 子计划1：本地Docker化与邮箱提取验证

**目标**: 实现本地Docker容器化部署，验证核心提取功能

**预计工期**: 3-4天

---

## ✅ 已完成的步骤

### 阶段1：Docker镜像构建（已完成）

- [x] 创建 [Dockerfile](../Dockerfile) - Python 3.9-slim基础镜像
- [x] 创建 [.dockerignore](../.dockerignore) - 构建排除文件
- [x] 创建 [docker-compose.yml](../docker-compose.yml) - 单容器编排
- [x] 创建 [.entrypoint.sh](../.entrypoint.sh) - 启动脚本
- [x] 创建 [docs/DOCKER_DEPLOYMENT.md](../docs/DOCKER_DEPLOYMENT.md) - 部署文档

---

## 📋 待执行的步骤

### 阶段2：本地容器化测试（1-2天）

#### 步骤2.1：验证Docker环境
```bash
# 检查Docker和docker-compose版本
docker --version
docker-compose --version

# 验证配置文件语法
docker-compose config
```

**预期结果**:
- Docker版本 >= 20.10
- docker-compose版本 >= 1.29
- 配置文件无语法错误

#### 步骤2.2：构建Docker镜像
```bash
# 构建镜像
docker-compose build

# 查看构建的镜像
docker images | grep email-automation
```

**预期结果**:
- 镜像构建成功
- 镜像大小约200-400MB

#### 步骤2.3：配置环境变量
```bash
# 复制或创建.env文件
cp .env.example .env

# 编辑.env，填写邮箱配置
# IMAP_HOST=imap.example.com
# IMAP_USER=user@example.com
# IMAP_PASS=password
# ... 其他配置
```

**预期结果**:
- .env文件包含所有必需配置

#### 步骤2.4：启动容器（测试模式）
```bash
# 前台运行（查看日志）
docker-compose up

# 观察启动日志，确认：
# ✅ 规则配置文件已找到
# ✅ 目录已创建
# 📧 启动主程序...
```

**预期结果**:
- 容器成功启动
- 无ERROR级别的日志
- 主程序正常运行

#### 步骤2.5：验证功能清单

1. **容器健康检查**
   ```bash
   docker ps
   # 查看 STATUS 列，应为 "Up X minutes (healthy)"
   ```

2. **日志文件写入验证**
   ```bash
   ls -la logs/
   # 应该看到 app_*.log 文件
   cat logs/app_*.log | tail -20
   ```

3. **邮箱连接验证**（需要配置真实邮箱）
   ```bash
   docker-compose logs | grep "邮箱登录"
   # 预期: 【业务日志】邮箱登录成功
   ```

4. **数据库创建验证**
   ```bash
   ls -la extracted_mails/data.db
   # 应该看到数据库文件
   ```

5. **文件权限验证**
   ```bash
   ls -ld logs/ extracted_mails/
   # 权限应该正常
   ```

#### 步骤2.6：数据持久化测试

```bash
# 停止容器
docker-compose down

# 删除容器（保留数据卷）
docker-compose rm -f

# 重新启动
docker-compose up -d

# 验证数据是否保留
ls -la extracted_mails/data.db
cat logs/app_*.log | tail -5
```

**预期结果**:
- 数据库文件存在
- 日志文件保留

---

### 阶段3：生产环境优化（1天）

#### 步骤3.1：资源限制配置

在 [docker-compose.yml](../docker-compose.yml) 中添加：

```yaml
services:
  email-service:
    # ... 现有配置
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
```

#### 步骤3.2：添加监控脚本

创建 [scripts/monitor.sh](../scripts/monitor.sh)：

```bash
#!/bin/bash
# 容器监控脚本

echo "📊 容器资源使用情况："
docker stats email-automation-service --no-stream

echo ""
echo "💾 磁盘使用情况："
docker-compose exec email-service du -sh /app/extracted_mails

echo ""
echo "📝 最近日志："
docker-compose logs --tail=10 email-service
```

#### 步骤3.3：添加备份脚本

创建 [scripts/backup.sh](../scripts/backup.sh)：

```bash
#!/bin/bash
# 数据备份脚本

BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "📦 开始备份..."

# 备份数据库
cp extracted_mails/data.db "$BACKUP_DIR/data.db"

# 备份规则
cp -r rules "$BACKUP_DIR/"

# 备份日志（可选）
cp -r logs "$BACKUP_DIR/"

echo "✅ 备份完成: $BACKUP_DIR"
```

#### 步骤3.4：添加清理脚本

创建 [scripts/cleanup.sh](../scripts/cleanup.sh)：

```bash
#!/bin/bash
# 日志清理脚本

echo "🧹 清理旧日志文件..."

# 删除30天前的日志
find logs/ -name "*.log" -mtime +30 -delete

echo "✅ 清理完成"
```

---

### 阶段4：验证和文档（0.5天）

#### 步骤4.1：创建快速启动脚本

创建 [scripts/start.sh](../scripts/start.sh)：

```bash
#!/bin/bash
# 快速启动脚本

echo "🚀 启动邮件自动化服务..."

# 检查.env文件
if [ ! -f .env ]; then
    echo "❌ 错误: .env 文件不存在"
    echo "请先复制 .env.example 到 .env 并配置"
    exit 1
fi

# 检查规则文件
if [ ! -f rules/parse_rules.json ]; then
    echo "❌ 错误: 规则配置文件不存在"
    exit 1
fi

# 创建必要目录
mkdir -p logs extracted_mails

# 启动服务
docker-compose up -d

echo "✅ 服务已启动"
echo "查看日志: docker-compose logs -f"
```

#### 步骤4.2：创建停止脚本

创建 [scripts/stop.sh](../scripts/stop.sh)：

```bash
#!/bin/bash
# 停止服务脚本

echo "🛑 停止邮件自动化服务..."
docker-compose down
echo "✅ 服务已停止"
```

#### 步骤4.3：更新README.md

在项目README中添加Docker部署部分。

---

## 📊 完成标准

### 必须完成（P0）

- [ ] Docker镜像成功构建
- [ ] 容器可以正常启动
- [ ] 日志文件正常写入
- [ ] 数据库文件创建
- [ ] 数据持久化验证通过
- [ ] 部署文档完整

### 推荐完成（P1）

- [ ] 资源限制配置
- [ ] 监控脚本
- [ ] 备份脚本
- [ ] 清理脚本
- [ ] 快速启动/停止脚本

### 可选完成（P2）

- [ ] 性能基准测试
- [ ] 压力测试
- [ ] 自动化测试脚本

---

## ⚠️ 风险点

### 1. 网络配置问题

**风险**: 容器内无法访问外部IMAP服务器

**缓解**:
- 使用 `--network host` 模式（Linux）
- 配置DNS服务器
- 测试网络连通性

### 2. 文件权限问题

**风险**: 容器内用户权限与宿主机不匹配

**缓解**:
- 在entrypoint中配置uid/gid
- 使用 `USER` 指令指定用户
- 调整挂载目录权限

### 3. 时区问题

**风险**: 定时任务执行时间不准确

**缓解**:
- 设置 `TZ=Asia/Shanghai`
- 验证容器时区：`date`

---

## 📝 验证检查清单

执行以下命令验证部署成功：

```bash
# 1. 容器状态
docker-compose ps
# 预期: Up (healthy)

# 2. 日志检查
docker-compose logs | tail -20
# 预期: 无ERROR，有业务日志

# 3. 文件检查
ls -la logs/ extracted_mails/
# 预期: 目录存在，有文件

# 4. 健康检查
docker inspect email-automation-service | grep -A 5 Health
# 预期: Status: healthy

# 5. 资源使用
docker stats email-automation-service --no-stream
# 预期: CPU和内存使用正常
```

---

## 🎯 下一步

完成本计划后，可以进入：
- **子计划2**: GitHub Actions自动化执行（主要模式）
- **子计划3**: 本地Docker Web UI控制端

---

**相关文档**:
- [Docker部署指南](../docs/DOCKER_DEPLOYMENT.md)
- [主计划文件](./bubbly-booping-rossum.md)
