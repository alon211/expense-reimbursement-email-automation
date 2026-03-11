# GitHub Secrets 配置指南

## 🔐 配置GitHub Secrets

### 为什么需要配置Secrets？

根据 [敏感信息安全管控](../architecture/config/sensitive-data.md) 的指导：

- ✅ **必须**：邮箱密码等敏感信息只存储在GitHub Secrets，绝不放在本地 `.env` 文件中
- ✅ **必须**：GitHub Secrets采用加密存储，仅在Actions执行时临时解密
- ✅ **必须**：使用授权码/应用专用密码，不要使用邮箱登录密码
- ❌ **禁止**：在代码中硬编码密码
- ❌ **禁止**：在Docker参数中传递密码
- ❌ **禁止**：在日志中打印密码

---

## 📋 配置步骤

### 1. 打开Secrets配置页面

在浏览器中访问：
```
https://github.com/alon211/expense-reimbursement-email-automation/settings/secrets/actions
```

或者：
1. 打开仓库页面：https://github.com/alon211/expense-reimbursement-email-automation
2. 点击 **Settings**（设置）
3. 左侧菜单点击 **Secrets and variables** → **Actions**
4. 点击 **New repository secret** 按钮

### 2. 添加必需的Secrets

点击 **New repository secret** 按钮，逐个添加以下Secrets：

#### 必需Secrets（Required）

| Secret名称 | 说明 | 示例值 | 如何获取 |
|-----------|------|--------|----------|
| `IMAP_HOST` | IMAP服务器地址 | `imap.qq.com` | 邮箱服务商提供 |
| `IMAP_USER` | 邮箱账号 | `user@qq.com` | 您的邮箱地址 |
| `IMAP_PASS` | 邮箱密码或授权码 | `authorization_code` | 邮箱设置中生成 |

#### 可选Secrets（Optional）

| Secret名称 | 说明 | 示例值 | 如何获取 |
|-----------|------|--------|----------|
| `DINGTALK_WEBHOOK` | 钉钉Webhook URL | `https://oapi.dingtalk.com/robot/send?access_token=xxx` | 钉钉机器人设置 |
| `DINGTALK_SECRET` | 钉钉签名密钥 | `SECxxxxxxxxxxx` | 钉钉机器人安全设置 |

---

## 📧 常见邮箱配置

### QQ邮箱

```
IMAP_HOST = imap.qq.com
IMAP_PASS = 授权码（需要在QQ邮箱设置中生成）
```

**获取授权码步骤**：
1. 登录QQ邮箱网页版
2. 点击 **设置** → **账户**
3. 找到 **POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务**
4. 开启 **IMAP/SMTP服务**
5. 按照提示发送短信
6. 生成授权码（16位字符）

**注意**：
- ❌ 不要使用QQ登录密码
- ✅ 必须使用授权码

### 163邮箱

```
IMAP_HOST = imap.163.com
IMAP_PASS = 授权码（需要在163邮箱设置中生成）
```

**获取授权码步骤**：
1. 登录163邮箱网页版
2. 点击 **设置** → **POP3/SMTP/IMAP**
3. 开启 **IMAP服务**
4. 设置客户端授权密码
5. 保存授权码

### Gmail

```
IMAP_HOST = imap.gmail.com
IMAP_PASS = 应用专用密码（需要在Google账户设置中生成）
```

**获取应用专用密码步骤**：
1. 登录Google账户
2. 开启两步验证（2-Step Verification）
3. 进入 **安全性** → **应用专用密码**
4. 选择 **邮件** → **Windows计算机**
5. 生成密码（16位字符）

### 企业邮箱

联系您的邮箱管理员获取：
- IMAP服务器地址
- 端口号（通常是993）
- 密码或授权码

---

## ⚠️ 安全注意事项

### DO's（应该做的）

- ✅ 使用授权码/应用专用密码，而不是邮箱登录密码
- ✅ 定期更换Secrets（建议每3-6个月）
- ✅ 为不同的仓库使用不同的授权码
- ✅ 启用GitHub仓库的"Secrets扫描"功能
- ✅ 使用最小权限的GitHub Personal Access Token

### DON'Ts（不应该做的）

- ❌ 不要将邮箱登录密码作为 `IMAP_PASS`
- ❌ 不要在代码中硬编码密码
- ❌ 不要在 `.env` 文件中存储密码（本地环境除外）
- ❌ 不要在日志、注释、文档中暴露Secrets
- ❌ 不要将Secrets提交到Git仓库

---

## 🔍 验证配置

配置完成后，可以通过以下方式验证：

### 方法1：手动触发Workflow

1. 打开仓库的 **Actions** 标签
2. 选择 **Email Extraction** 工作流
3. 点击 **Run workflow**
4. 选择参数（如 `time_range_days: 20`）
5. 点击 **Run workflow** 按钮

查看执行日志，应该看到：
```
✅ GitHub Secrets配置验证通过
✅ 所有必需的Secrets已配置
```

### 方法2：使用Python脚本触发

```bash
python scripts/trigger_workflow.py \
  --token "$GITHUB_TOKEN" \
  --repo "alon211/expense-reimbursement-email-automation" \
  --time-range-days 20 \
  --wait
```

### 方法3：使用GitHub CLI

```bash
# 登录GitHub
gh auth login

# 触发workflow
gh workflow run email-extraction.yml -f time_range_days=20

# 查看运行状态
gh run list

# 查看详细日志
gh run view <run-id> --log
```

---

## 🚨 常见问题

### Q1: workflow失败，提示"缺少必需的Secrets"

**原因**：未配置 `IMAP_HOST`、`IMAP_USER`、`IMAP_PASS`

**解决**：按照上述步骤添加这三个Secrets

### Q2: 邮箱连接失败，提示"认证失败"

**原因**：
- 使用了邮箱登录密码而不是授权码
- 授权码已过期
- 授权码输入错误

**解决**：
- 重新生成授权码
- 确认使用的是授权码，不是登录密码
- 检查授权码是否正确复制（无多余空格）

### Q3: QQ邮箱提示"请使用授权码"

**原因**：QQ邮箱要求使用授权码，不允许使用登录密码

**解决**：按照上述QQ邮箱配置步骤生成授权码

### Q4: Gmail提示"应用专用密码已禁用"

**原因**：未开启两步验证

**解决**：
1. 登录Google账户
2. 开启两步验证（2-Step Verification）
3. 生成应用专用密码

### Q5: 如何查看Secrets是否配置成功？

在GitHub仓库页面：
1. 进入 **Settings** → **Secrets and variables** → **Actions**
2. 查看Secrets列表
3. 确认 `IMAP_HOST`、`IMAP_USER`、`IMAP_PASS` 已存在

**注意**：Secrets的值在配置后无法查看，只能更新或删除

---

## 📚 相关文档

- [GitHub Actions 使用指南](GITHUB_ACTIONS_USAGE.md)
- [敏感信息安全管控](../architecture/config/sensitive-data.md)
- [系统架构总览](../architecture/system-overview.md)
- [部署架构](../architecture/deployment.md)

---

**最后更新**: 2026-03-11
