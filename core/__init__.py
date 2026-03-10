# -*- coding: utf-8 -*-
"""核心业务模块

包含邮件拉取、解析和钉钉推送等核心业务逻辑。
"""
from .email_fetcher import decode_mail_header, parse_reimbursement_mail, fetch_reimbursement_mails
from .dingtalk_notifier import send_dingtalk_message
from .rule_loader import Rule, RuleLoader
from .database import DatabaseManager
from .models import ExtractedEmail, ExtractionHistory

__all__ = [
    'decode_mail_header',
    'parse_reimbursement_mail',
    'fetch_reimbursement_mails',
    'send_dingtalk_message',
    'Rule',
    'RuleLoader',
    'DatabaseManager',
    'ExtractedEmail',
    'ExtractionHistory',
]
