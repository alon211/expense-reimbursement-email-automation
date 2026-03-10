# -*- coding: utf-8 -*-
"""配置模块

提供配置管理和日志初始化功能。
"""
from .settings import *
from .logger_config import init_logger

__all__ = [
    'init_logger',
    # IMAP 配置
    'IMAP_HOST', 'IMAP_USER', 'IMAP_PASS', 'MAIL_CHECK_FOLDER', 'MAIL_SEARCH_CRITERIA',
    # 定时配置
    'CHECK_INTERVAL', 'TIME_ZONE',
    # 日志配置
    'LOG_LEVEL', 'LOG_DIR', 'LOG_MAX_SIZE', 'LOG_BACKUP_COUNT',
    # 钉钉配置
    'DINGTALK_WEBHOOK', 'DINGTALK_SECRET', 'PUSH_SWITCH',
    # 其他配置
    'PARSE_RULES_JSON_PATH', 'EXTRACT_ROOT_DIR',
]
