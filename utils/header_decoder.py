# -*- coding: utf-8 -*-
"""邮件头解码工具

提供邮件头解码功能，处理各种编码格式。
"""
from email.header import decode_header
import logging

logger = logging.getLogger("HeaderDecoder")


def decode_mail_header(header: str) -> str:
    """
    解码邮件头

    Args:
        header: 邮件头字符串（可能包含编码）

    Returns:
        str: 解码后的字符串

    Examples:
        >>> decode_mail_header("=?UTF-8?B?5rWL6K+V?=")
        '测试'
    """
    try:
        decoded, encoding = decode_header(header)[0]
        if encoding:
            return decoded.decode(encoding)
        return str(decoded)
    except Exception as e:
        logger.error(f"【解析错误】邮件头解码失败：{str(e)}")
        return "未知内容"
