#!/bin/bash
set -e

echo "🚀 启动邮件自动化服务..."
echo "时区: $TZ"
echo "检查间隔: $CHECK_INTERVAL 秒"
echo "日志级别: $LOG_LEVEL"

# 验证规则配置文件存在
if [ ! -f "./rules/parse_rules.json" ]; then
    echo "❌ 错误: 规则配置文件不存在 (./rules/parse_rules.json)"
    exit 1
fi
echo "✅ 规则配置文件已找到"

# 验证邮箱配置
if [ -z "$IMAP_HOST" ] || [ -z "$IMAP_USER" ] || [ -z "$IMAP_PASS" ]; then
    echo "⚠️  警告: 邮箱配置不完整"
    echo "IMAP_HOST: ${IMAP_HOST:0:8}..."
    echo "IMAP_USER: ${IMAP_USER}"
    echo "IMAP_PASS: ${IMAP_PASS:+********}"
fi

# 创建必要的目录
mkdir -p /app/logs /app/extracted_mails
echo "✅ 目录已创建"

# 显示配置信息
echo "========================================="
echo "邮箱服务器: ${IMAP_HOST:0:8}..."
echo "邮箱账号: ${IMAP_USER}"
echo "邮箱文件夹: ${MAIL_CHECK_FOLDER:-INBOX}"
echo "时间范围: ${PARSE_TIME_RANGE_DAYS:-20} 天"
echo "保存路径: ${EXTRACT_ROOT_DIR}"
echo "========================================="

echo "📧 启动主程序..."
exec python main.py
