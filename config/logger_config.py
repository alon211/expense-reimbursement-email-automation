# -*- coding: utf-8 -*-
"""日志配置模块

提供日志初始化功能，支持实时刷盘和多级别日志输出。
"""
import logging
import os
import sys
import atexit
from datetime import datetime
from .settings import LOG_LEVEL, LOG_DIR


def generate_log_filename() -> str:
    """生成日志文件名：日期+时分秒+日志等级"""
    current_time = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{current_time}_{LOG_LEVEL.upper()}.log"


def init_logger():
    """
    初始化日志系统

    特性：
    1. 强制所有模式下日志实时刷盘
    2. 校验Handler级别配置，确保与Logger匹配
    3. 重写Handler的emit方法，强制刷新
    4. 注册退出钩子，确保程序退出时刷盘
    5. 生产环境（INFO级别）时控制台不输出日志

    Returns:
        tuple: (logger, log_file) - 日志对象和日志文件路径
    """
    # ========== 日志目录校验 ==========
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR, exist_ok=True)
        print(f"日志目录不存在，已创建：{LOG_DIR}")

    if not os.access(LOG_DIR, os.W_OK):
        print(f"错误：日志目录 {LOG_DIR} 无写入权限！")
        sys.exit(1)

    # ========== 日志文件路径生成 ==========
    log_file = os.path.join(
        LOG_DIR,
        generate_log_filename()
    ).replace("\\", "/")  # 统一路径分隔符
    print(f"日志文件路径：{log_file}")

    # ========== 判断运行环境 ==========
    is_production = LOG_LEVEL.upper() == "INFO"
    if is_production:
        print(f"运行环境：生产环境（日志级别={LOG_LEVEL}，控制台无输出）")
    else:
        print(f"运行环境：开发环境（日志级别={LOG_LEVEL}，控制台有输出）")

    # ========== 日志格式配置 ==========
    log_format = logging.Formatter(
        '%(asctime)s - %(process)d - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # ========== 控制台处理器（生产环境禁用） ==========
    console_handler = None
    if not is_production:
        # 开发环境：控制台输出所有日志
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_format)
        console_handler.setLevel(LOG_LEVEL)
        console_handler.flush = sys.stdout.flush

        # 重写控制台Handler（确保同步）
        original_console_emit = console_handler.emit

        def console_emit_with_flush(record):
            original_console_emit(record)
            console_handler.flush()

        console_handler.emit = console_emit_with_flush
    else:
        # 生产环境：控制台不输出日志（只输出到文件）
        print("【生产环境】控制台日志已禁用，所有日志仅输出到文件")

    # ========== 文件处理器（核心：强制实时写入） ==========
    log_file_obj = open(
        log_file,
        mode='a',
        encoding='utf-8',
        buffering=1  # 行缓冲
    )
    # 初始刷盘
    log_file_obj.flush()
    os.fsync(log_file_obj.fileno())

    file_handler = logging.StreamHandler(log_file_obj)
    file_handler.setFormatter(log_format)
    file_handler.setLevel(logging.DEBUG)  # 接收所有级别，由Logger最终过滤

    # ========== 强制刷盘函数 ==========
    def force_flush():
        """强制日志写入磁盘"""
        if log_file_obj and not log_file_obj.closed:
            log_file_obj.flush()
            os.fsync(log_file_obj.fileno())

    file_handler.flush = force_flush

    # ========== 重写emit方法，强制刷新 ==========
    original_file_emit = file_handler.emit

    def file_emit_with_flush(record):
        original_file_emit(record)
        force_flush()

    file_handler.emit = file_emit_with_flush

    # ========== 初始化Logger ==========
    logger = logging.getLogger("ReimbursementMailFetcher")
    logger.setLevel(LOG_LEVEL)  # 最终过滤级别
    logger.handlers.clear()

    # 只在开发环境添加控制台处理器
    if console_handler:
        logger.addHandler(console_handler)

    # 文件处理器始终添加
    logger.addHandler(file_handler)

    logger.propagate = False  # 禁止向上传播

    # ========== 注册退出钩子 ==========
    def exit_flush():
        """程序退出时强制刷盘"""
        if not is_production:
            print("\n程序退出，强制刷新日志...")
        force_flush()
        if log_file_obj and not log_file_obj.closed:
            log_file_obj.close()
        for h in logger.handlers:
            h.close()

    atexit.register(exit_flush)

    # 预写入测试日志
    logger.debug(f"日志初始化完成，文件路径：{log_file}")
    logger.info("测试日志：文件中应显示此内容")

    if not is_production:
        logger.info("【开发环境】此日志应在控制台和文件中同时显示")

    return logger, log_file
