# -*- coding: utf-8 -*-
"""邮件处理模块

提供邮件拉取、解析和处理功能。
"""
import imaplib
import email
import logging
from datetime import datetime, timedelta
from pathlib import Path
from utils.header_decoder import decode_mail_header
from core.dingtalk_notifier import send_dingtalk_message
from core.rule_loader import RuleLoader
from core.email_extractor import extract_email_full, EmailExtractor
from config.settings import (
    IMAP_HOST, IMAP_USER, IMAP_PASS, MAIL_CHECK_FOLDER, MAIL_SEARCH_CRITERIA,
    PARSE_RULES_JSON_PATH, EXTRACT_ROOT_DIR
)

logger = logging.getLogger("EmailFetcher")


def parse_reimbursement_mail(msg, rule_loader: RuleLoader, logger_instance: logging.Logger = None):
    """
    解析邮件，使用规则判断是否为目标邮件

    Args:
        msg: 邮件对象
        rule_loader: 规则加载器实例
        logger_instance: 日志对象（可选，用于解耦）

    Returns:
        dict|None: 如果匹配规则，返回包含 message_id、主题、发件人、日期、正文、匹配规则的字典；否则返回 None
    """
    log = logger_instance or logger

    # 提取邮件唯一标识
    message_id = decode_mail_header(msg.get("Message-ID", ""))
    if not message_id:
        # 如果没有 Message-ID，使用其他字段生成一个唯一标识
        subject = decode_mail_header(msg.get("Subject", ""))
        sender = decode_mail_header(msg.get("From", ""))
        date = decode_mail_header(msg.get("Date", ""))
        message_id = f"<auto_{hash(subject + sender + date)}@generated>"

    subject = decode_mail_header(msg.get("Subject", "无主题"))
    sender = decode_mail_header(msg.get("From", "未知发件人"))
    date = decode_mail_header(msg.get("Date", "未知时间"))

    # 提取邮件正文（支持多种编码容错）
    body = ""
    try:
        def decode_payload(payload, charset):
            """健壮的编码解码函数"""
            charsets = [charset, 'utf-8', 'gbk', 'gb2312', 'iso-8859-1']
            for cs in charsets:
                if not cs:
                    continue
                try:
                    return payload.decode(cs)
                except (UnicodeDecodeError, LookupError):
                    continue
            # 如果所有编码都失败，使用 ignore 错误模式
            try:
                return payload.decode(charset or 'utf-8', errors='ignore')
            except:
                return "正文编码解析失败"

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain" and not part.get_filename():
                    payload = part.get_payload(decode=True)
                    charset = part.get_content_charset()
                    body = decode_payload(payload, charset)
                    break
        else:
            payload = msg.get_payload(decode=True)
            charset = msg.get_content_charset()
            body = decode_payload(payload, charset)
    except Exception as e:
        log.error(f"【解析错误】邮件正文解析失败：{str(e)}")
        body = "正文解析失败"

    # 使用规则匹配
    matched_rules = rule_loader.match_rules(subject, sender, body)
    if matched_rules:
        rule_names = ", ".join([rule.rule_name for rule in matched_rules])
        log.info(f"【业务日志】发现目标邮件：主题={subject}，发件人={sender}，匹配规则={rule_names}")
        return {
            "message_id": message_id,
            "subject": subject,
            "sender": sender,
            "date": date,
            "body": body[:200] + "..." if len(body) > 200 else body,
            "matched_rules": matched_rules
        }

    return None


def fetch_reimbursement_mails(logger_instance: logging.Logger = None, db_manager=None):
    """
    拉取并处理目标邮件（基于规则匹配和时间范围）

    Args:
        logger_instance: 日志对象（用于解耦）
        db_manager: 数据库管理器实例（可选，用于去重和记录）

    Returns:
        list: 匹配的邮件列表，每个元素包含邮件信息和文件路径
    """
    log = logger_instance or logger
    mail_conn = None
    extraction_dir = None  # 提取目录

    try:
        # 初始化规则加载器
        log.debug(f"【调试日志】加载解析规则：{PARSE_RULES_JSON_PATH}")
        rule_loader = RuleLoader(PARSE_RULES_JSON_PATH)
        log.info(f"【业务日志】成功加载 {len(rule_loader.get_enabled_rules())} 条解析规则，时间范围：{rule_loader.parse_time_range_days} 天")

        # 创建提取目录（TODO 3）
        extractor = EmailExtractor()
        extraction_dir = extractor.create_extraction_dir()
        log.info(f"【业务日志】创建提取目录：{extraction_dir}")

        log.debug(f"【调试日志】开始连接IMAP服务器：{IMAP_HOST}")
        mail_conn = imaplib.IMAP4_SSL(IMAP_HOST)
        mail_conn.login(IMAP_USER, IMAP_PASS)
        log.info("【业务日志】邮箱登录成功")

        mail_conn.select(MAIL_CHECK_FOLDER)
        log.info(f"【业务日志】选中邮件文件夹：{MAIL_CHECK_FOLDER}")

        # 构建搜索条件（添加时间范围过滤）
        since_date = (datetime.now() - timedelta(days=rule_loader.parse_time_range_days)).strftime("%d-%b-%Y")
        search_criteria = f'({MAIL_SEARCH_CRITERIA} SINCE {since_date})'
        log.info(f"【业务日志】搜索条件：{search_criteria}（搜索最近 {rule_loader.parse_time_range_days} 天的邮件）")

        status, messages = mail_conn.search(None, MAIL_SEARCH_CRITERIA, f'SINCE {since_date}')
        if status != 'OK':
            log.info("【业务日志】未找到符合条件的邮件")
            return []

        mail_ids = messages[0].split()
        log.info(f"【业务日志】在时间范围内找到 {len(mail_ids)} 封邮件")

        matched_mails = []
        skipped_count = 0  # 已提取过的邮件数量

        # 逐个处理邮件
        for num in mail_ids:
            log.debug(f"【调试日志】开始解析邮件编号：{num}")
            status, data = mail_conn.fetch(num, '(RFC822)')
            msg = email.message_from_bytes(data[0][1])

            matched_mail = parse_reimbursement_mail(msg, rule_loader, log)
            if matched_mail:
                # 检查是否已提取且文件存在（增强版去重）
                if db_manager:
                    is_extracted, db_exists, storage_exists, body_exists = db_manager.is_email_extracted_with_files(matched_mail['message_id'])
                    if is_extracted:
                        log.info(f"【业务日志】邮件已提取且文件存在，跳过：{matched_mail['subject']}（数据库记录={db_exists}, 提取内容文件={storage_exists}, 邮件HTML={body_exists}）")
                        skipped_count += 1
                        continue
                    elif db_exists and not is_extracted:
                        log.warning(f"【业务日志】邮件有数据库记录但文件不存在，将重新提取：{matched_mail['subject']}")

                # TODO 3: 提取邮件内容（正文、附件）
                log.info(f"【提取器】开始提取邮件内容：{matched_mail['subject']}")
                extraction_result = extract_email_full(msg, matched_mail, extraction_dir)

                # 将提取结果添加到邮件数据中
                matched_mail['extraction'] = extraction_result
                matched_mail['msg_object'] = msg  # 保留原始邮件对象供后续使用

                matched_mails.append(matched_mail)
                # 标记为已读
                mail_conn.store(num, '+FLAGS', '\\Seen')
                log.debug(f"【调试日志】邮件{num}已标记为已读")

        # 记录统计信息
        total_matched = len(matched_mails)
        if skipped_count > 0:
            log.info(f"【业务日志】跳过 {skipped_count} 封已提取的邮件")

        return matched_mails

    except Exception as e:
        log.error(f"【错误日志】拉取邮件异常：{str(e)}")
        send_dingtalk_message(f"邮件拉取失败：{str(e)}")
        return []
    finally:
        if mail_conn:
            try:
                mail_conn.close()
                mail_conn.logout()
                log.info("【业务日志】邮箱连接已关闭")
            except Exception as e:
                log.error(f"【错误日志】关闭邮箱连接异常：{str(e)}")


def send_mail_summary_notification(matched_mails: list, time_range_days: int, logger_instance: logging.Logger = None):
    """
    发送匹配邮件的汇总通知

    Args:
        matched_mails: 匹配的邮件列表
        time_range_days: 时间范围（天数）
        logger_instance: 日志对象（用于解耦）
    """
    log = logger_instance or logger

    if matched_mails:
        push_content = f"共发现{len(matched_mails)}封目标邮件（最近{time_range_days}天）：\n"
        for mail in matched_mails:
            rule_names = ", ".join([rule.rule_name for rule in mail.get('matched_rules', [])])
            push_content += f"- 主题：{mail['subject']}\n  发件人：{mail['sender']}\n  匹配规则：{rule_names}\n"
        send_dingtalk_message(push_content)
        log.info(f"【业务日志】已发送 {len(matched_mails)} 封邮件的钉钉通知")
    else:
        log.info(f"【业务日志】本次检查未发现新邮件")

