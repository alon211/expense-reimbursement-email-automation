# -*- coding: utf-8 -*-
"""报销邮件自动化服务 - 主程序入口

定时检查邮箱中的报销邮件，并通过钉钉推送通知。
"""
import time
import sys
import os
import pytz
import io
from datetime import datetime

# 设置标准输出编码为 UTF-8 (Windows 中文显示修复)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 导入配置模块
from config.settings import (
    CHECK_INTERVAL, TIME_ZONE, LOG_LEVEL
)
from config.logger_config import init_logger
from core.email_fetcher import fetch_reimbursement_mails
from utils.file_utils import check_file_exists

# 初始化日志
try:
    logger, log_file = init_logger()
except Exception as e:
    print(f"日志初始化失败：{e}")
    sys.exit(1)


def main():
    """主循环：定时检查邮件"""
    tz = pytz.timezone(TIME_ZONE)

    logger.info("\n===== 报销邮件拉取服务启动 =====")
    logger.debug(f"【调试日志】Python版本：{sys.version}，日志级别：{LOG_LEVEL}")
    logger.info(f"【系统日志】时区：{TIME_ZONE} | 检查间隔：{CHECK_INTERVAL}秒")
    logger.info(f"【系统日志】日志文件：{log_file}")
    logger.info("===============================\n")

    # 验证日志文件写入正常
    if check_file_exists(log_file):
        file_size = os.path.getsize(log_file)
        if file_size > 0:
            logger.info("✅ 日志文件写入正常")
        else:
            logger.warning("⚠️ 日志文件为空，请检查权限")
    else:
        logger.error("❌ 日志文件未创建，请检查路径/权限")

    # 定时任务主循环
    while True:
        try:
            current_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"\n=== 开始新一轮邮件检查：{current_time} ===")
            fetch_reimbursement_mails(logger)
        except Exception as e:
            logger.error(f"【错误日志】主循环异常：{str(e)}")

        logger.info(f"等待{CHECK_INTERVAL}秒后进行下一次检查...")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    # 测试日志写入
    print("\n=== 测试日志写入 ===")
    logger.debug("📝 DEBUG：控制台和文件都应看到")
    logger.info("📝 INFO：控制台和文件都应看到")
    logger.error("📝 ERROR：控制台和文件都应看到")

    # 强制刷盘
    for handler in logger.handlers:
        handler.flush()

    # 验证日志文件
    if os.path.exists(log_file):
        file_size = os.path.getsize(log_file)
        print(f"日志文件已创建，大小：{file_size} 字节")
        if file_size > 0:
            print("✅ 日志文件写入成功！")
        else:
            print("❌ 日志文件为空，请检查权限/路径！")
    else:
        print("❌ 日志文件未创建，请检查路径/权限！")

    try:
        main()
    except KeyboardInterrupt:
        logger.info("【系统日志】用户手动终止程序，正在退出...")
        # 强制刷盘
        for handler in logger.handlers:
            handler.flush()
    except Exception as e:
        logger.error(f"【错误日志】程序异常退出：{str(e)}")
        for handler in logger.handlers:
            handler.flush()
        sys.exit(1)