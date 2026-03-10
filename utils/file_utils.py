# -*- coding: utf-8 -*-
"""文件工具模块

提供文件操作相关的工具函数。
"""
import os
import logging

logger = logging.getLogger("FileUtils")


def ensure_log_dir(log_dir: str) -> bool:
    """
    确保日志目录存在并可写

    Args:
        log_dir: 日志目录路径

    Returns:
        bool: 目录是否可用
    """
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
        logger.info(f"日志目录不存在，已创建：{log_dir}")

    if not os.access(log_dir, os.W_OK):
        logger.error(f"错误：日志目录 {log_dir} 无写入权限！")
        return False

    return True


def check_file_exists(file_path: str) -> bool:
    """
    检查文件是否存在

    Args:
        file_path: 文件路径

    Returns:
        bool: 文件是否存在
    """
    return os.path.exists(file_path) and os.path.isfile(file_path)


def normalize_path(path: str) -> str:
    """
    规范化路径分隔符（统一为正斜杠）

    Args:
        path: 原始路径

    Returns:
        str: 规范化后的路径
    """
    return path.replace("\\", "/")
