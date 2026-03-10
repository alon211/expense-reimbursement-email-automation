# -*- coding: utf-8 -*-
"""配置管理模块

从 .env 文件读取环境变量，进行类型转换和校验。
"""
import os
import sys
import re
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()


def validate_email_format(email_str: str) -> bool:
    """校验邮箱地址格式是否合法"""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email_str) is not None


def validate_config():
    """严格校验所有配置，不满足则退出程序"""
    # 使用独立的 logger 避免循环依赖
    import logging
    logger = logging.getLogger("ConfigChecker")
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)

    # 1. 校验必填核心配置
    required_configs = {
        "IMAP_HOST": IMAP_HOST,
        "IMAP_USER": IMAP_USER,
        "IMAP_PASS": IMAP_PASS,
        "LOG_DIR": LOG_DIR,
        "PARSE_RULES_JSON_PATH": PARSE_RULES_JSON_PATH,
        "EXTRACT_ROOT_DIR": EXTRACT_ROOT_DIR
    }

    missing_configs = [
        key for key, value in required_configs.items()
        if not isinstance(value, str) or value.strip() == ""
    ]

    if missing_configs:
        logger.error(f"【配置错误】以下必填配置项未设置或为空：{', '.join(missing_configs)}，请检查.env文件")
        sys.exit(1)

    # 2. 校验邮箱地址格式
    if not validate_email_format(IMAP_USER):
        logger.error(f"【配置错误】邮箱地址格式不合法：{IMAP_USER}，请检查.env中的IMAP_USER配置")
        sys.exit(1)

    logger.info("✅ 所有配置校验通过")


# ===================== 读取环境变量 =====================
# 邮箱配置
IMAP_HOST = os.getenv("IMAP_HOST", "")
IMAP_USER = os.getenv("IMAP_USER", "")
IMAP_PASS = os.getenv("IMAP_PASS", "")
MAIL_CHECK_FOLDER = os.getenv("MAIL_CHECK_FOLDER", "INBOX").strip() or "INBOX"
MAIL_SEARCH_CRITERIA = os.getenv("MAIL_SEARCH_CRITERIA", "UNSEEN").strip() or "UNSEEN"

# 定时配置
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "60"))
TIME_ZONE = os.getenv("TIME_ZONE", "Asia/Shanghai").strip() or "Asia/Shanghai"

# 日志配置
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").strip().upper() or "INFO"
LOG_DIR = os.getenv("LOG_DIR", "./logs").strip() or "./logs"
LOG_MAX_SIZE = int(os.getenv("LOG_MAX_SIZE", str(10 * 1024 * 1024)))
LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "5"))

# 推送配置（钉钉）
DINGTALK_WEBHOOK = os.getenv("DINGTALK_WEBHOOK", "")
DINGTALK_SECRET = os.getenv("DINGTALK_SECRET", "")
PUSH_SWITCH = os.getenv("PUSH_SWITCH", "True").lower() == "true"

# 解析 & 存储配置
PARSE_RULES_JSON_PATH = os.getenv("PARSE_RULES_JSON_PATH", "./rules/parse_rules.json")
EXTRACT_ROOT_DIR = os.getenv("EXTRACT_ROOT_DIR", "./extracts")

# 执行配置校验
validate_config()
