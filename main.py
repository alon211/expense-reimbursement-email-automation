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
    CHECK_INTERVAL, TIME_ZONE, LOG_LEVEL, EXTRACT_ROOT_DIR, CLEAR_DB_ON_STARTUP
)
from config.logger_config import init_logger
from core.email_fetcher import fetch_reimbursement_mails, send_mail_summary_notification
from core.database import DatabaseManager
from core.models import ExtractedEmail, ExtractionHistory
from core.rule_loader import RuleLoader
from utils.file_utils import check_file_exists
from pathlib import Path

# 初始化日志
try:
    logger, log_file = init_logger()
except Exception as e:
    print(f"日志初始化失败：{e}")
    sys.exit(1)


def main():
    """主循环：定时检查邮件"""
    tz = pytz.timezone(TIME_ZONE)

    logger.info("\n===== 报销邮件自动化服务启动 =====")
    logger.debug(f"【调试日志】Python版本：{sys.version}，日志级别：{LOG_LEVEL}")
    logger.info(f"【系统日志】时区：{TIME_ZONE} | 检查间隔：{CHECK_INTERVAL}秒")
    logger.info(f"【系统日志】日志文件：{log_file}")
    logger.info(f"【系统日志】提取目录：{EXTRACT_ROOT_DIR}")

    # 初始化数据库
    db_path = Path(EXTRACT_ROOT_DIR) / "data.db"
    logger.info(f"【系统日志】数据库路径：{db_path}")
    try:
        db = DatabaseManager(str(db_path))
        logger.info("✅ 数据库初始化成功")

        # 根据配置决定是否清空数据库
        if CLEAR_DB_ON_STARTUP:
            logger.warning("⚠️  配置要求启动时清空数据库（CLEAR_DB_ON_STARTUP=True）")
            stats_before = db.get_statistics()
            logger.info(f"【系统日志】清空前统计：{stats_before['total_emails']} 封邮件，{stats_before['total_history']} 条历史")

            result = db.clear_all_data()

            logger.info(f"【系统日志】已清空：{result['emails_deleted']} 封邮件，{result['history_deleted']} 条历史")
            logger.info("✅ 数据库已清空，将重新处理所有匹配的邮件")
        else:
            logger.info("【系统日志】保留数据库记录（CLEAR_DB_ON_STARTUP=False）")

    except Exception as e:
        logger.error(f"❌ 数据库初始化失败：{e}")
        sys.exit(1)

    # 加载规则获取时间范围
    try:
        from config.settings import PARSE_RULES_JSON_PATH
        rule_loader = RuleLoader(PARSE_RULES_JSON_PATH)
        logger.info(f"【系统日志】解析规则：{len(rule_loader.get_enabled_rules())} 条，时间范围：{rule_loader.parse_time_range_days} 天")
    except Exception as e:
        logger.warning(f"⚠️ 加载规则失败：{e}")
        rule_loader = None

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

            # 拉取匹配的邮件（带去重检查）
            matched_mails = fetch_reimbursement_mails(logger, db_manager=db)

            # 处理匹配的邮件
            if matched_mails:
                logger.info(f"【业务日志】发现 {len(matched_mails)} 封新邮件，开始处理...")

                for mail_data in matched_mails:
                    message_id = mail_data['message_id']
                    subject = mail_data['subject']
                    sender = mail_data['sender']
                    matched_rules = mail_data.get('matched_rules', [])

                    # 获取主规则ID（使用第一个匹配的规则）
                    primary_rule_id = matched_rules[0].rule_id if matched_rules else "unknown"

                    # 获取提取结果（TODO 3）
                    extraction = mail_data.get('extraction', {})
                    storage_path = extraction.get('storage_path', '')
                    body_file_path = extraction.get('body_file_path', '')
                    attachment_count = extraction.get('attachment_count', 0)
                    attachment_paths = extraction.get('attachment_paths', [])

                    # 创建提取记录
                    try:
                        email_record = ExtractedEmail(
                            message_id=message_id,
                            subject=subject,
                            sender=sender,
                            rule_id=primary_rule_id,
                            extracted_at=datetime.now(),
                            storage_path=storage_path,  # ✅ TODO 3 已实现
                            attachment_count=attachment_count,  # ✅ TODO 3 已实现
                            body_file_path=body_file_path  # ✅ TODO 3 已实现
                        )

                        # 检查记录是否已存在，如果存在则更新，否则插入
                        existing_record = db.get_extracted_email(message_id)
                        if existing_record:
                            # 记录已存在，更新文件路径
                            success = db.update_extracted_email(email_record)
                            if success:
                                logger.info(f"【业务日志】已更新邮件提取记录：message_id={message_id}，主题={subject}")
                                logger.debug(f"【业务日志】  新提取目录：{storage_path}")
                                logger.debug(f"【业务日志】  新正文文件：{body_file_path}")
                                logger.debug(f"【业务日志】  新附件数量：{attachment_count}")
                            else:
                                logger.error(f"【错误日志】更新邮件记录失败：{message_id}")
                        else:
                            # 记录不存在，插入新记录
                            record_id = db.add_extracted_email(email_record)
                            logger.info(f"【业务日志】已记录邮件提取：ID={record_id}，主题={subject}")
                            logger.debug(f"【业务日志】  提取目录：{storage_path}")
                            logger.debug(f"【业务日志】  正文文件：{body_file_path}")
                            logger.debug(f"【业务日志】  附件数量：{attachment_count}")

                        # 添加提取历史
                        history = ExtractionHistory(
                            message_id=message_id,
                            rule_id=primary_rule_id,
                            action="matched"
                        )
                        db.add_extraction_history(history)
                    except Exception as e:
                        logger.error(f"【错误日志】记录邮件失败：{e}")

                # 发送汇总通知
                time_range_days = rule_loader.parse_time_range_days if rule_loader else 30
                send_mail_summary_notification(matched_mails, time_range_days, logger)
            else:
                logger.info("【业务日志】未发现新邮件")

        except Exception as e:
            logger.error(f"【错误日志】主循环异常：{str(e)}")
            import traceback
            logger.error(f"【错误日志】异常堆栈：{traceback.format_exc()}")

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