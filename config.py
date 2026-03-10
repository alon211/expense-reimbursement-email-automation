# -*- coding: utf-8 -*-
"""配置文件：修改这里的参数即可，不用动核心代码"""
import os

# ===================== 邮箱配置 =====================
IMAP_HOST = "imap.qq.com"  # 替换为你的邮箱IMAP地址（QQ: imap.qq.com, 企业微信: imap.weixin.qq.com）
IMAP_USER = "306068447@qq.com"  # 你的邮箱账号
IMAP_PASS = "bymbeazbocwybiab"   # 邮箱授权码（不是登录密码！）
MAIL_CHECK_FOLDER = "INBOX"       # 要检查的邮箱文件夹（默认收件箱）
MAIL_SEARCH_CRITERIA = 'UNSEEN'   # 搜索条件：UNSEEN=未读邮件，ALL=所有邮件

# ===================== 定时配置 =====================
CHECK_INTERVAL = 5  # 检查间隔（秒），默认1分钟
TIME_ZONE = "Asia/Shanghai"  # 时区

# ===================== 日志配置 =====================
LOG_LEVEL = "INFO"  # 日志级别：DEBUG/INFO/WARNING/ERROR
LOG_FILE = "/app/logs/reimbursement_mail.log"  # 容器内日志路径
LOG_MAX_SIZE = 10 * 1024 * 1024  # 单日志文件最大10MB
LOG_BACKUP_COUNT = 5  # 保留5个备份日志

# ===================== 推送配置（钉钉示例） =====================
# 可选：钉钉/企业微信/飞书/短信，这里以钉钉机器人为例
# DINGTALK_WEBHOOK = "https://oapi.dingtalk.com/robot/send?access_token=your_token"
# DINGTALK_SECRET = "your_secret"  # 可选：钉钉机器人加签密钥（如果开启了签名）
# PUSH_SWITCH = True  # 是否开启推送