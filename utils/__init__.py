# -*- coding: utf-8 -*-
"""工具模块

提供通用工具函数，如邮件头解码、文件操作等。
"""
from .header_decoder import decode_mail_header
from .file_utils import ensure_log_dir, check_file_exists, normalize_path

__all__ = [
    'decode_mail_header',
    'ensure_log_dir',
    'check_file_exists',
    'normalize_path',
]
