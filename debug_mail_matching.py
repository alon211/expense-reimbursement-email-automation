# -*- coding: utf-8 -*-
"""邮件匹配调试工具

显示所有邮件的详细信息，帮助调试规则匹配问题。
"""
import sys
import io
import imaplib
import email
from datetime import datetime, timedelta
from utils.header_decoder import decode_mail_header
from core.rule_loader import RuleLoader
from config.settings import IMAP_HOST, IMAP_USER, IMAP_PASS, MAIL_CHECK_FOLDER, MAIL_SEARCH_CRITERIA, PARSE_RULES_JSON_PATH

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


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
    try:
        return payload.decode(charset or 'utf-8', errors='ignore')
    except:
        return "正文解析失败"


def get_mail_body(msg):
    """提取邮件正文"""
    body = ""
    try:
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
        body = f"正文解析失败: {e}"
    return body


def debug_mail_matching():
    """调试邮件匹配"""
    print("=" * 80)
    print("邮件匹配调试工具")
    print("=" * 80)

    # 加载规则
    print(f"\n【加载规则】{PARSE_RULES_JSON_PATH}")
    rule_loader = RuleLoader(PARSE_RULES_JSON_PATH)
    print(f"规则数量：{len(rule_loader.get_enabled_rules())}")
    for rule in rule_loader.get_enabled_rules():
        print(f"  - {rule.rule_id}: {rule.rule_name}")
        print(f"    发件人包含: {rule.match_conditions.get('sender_contains', [])}")
        print(f"    主题包含: {rule.match_conditions.get('subject_contains', [])}")
        print(f"    正文包含: {rule.match_conditions.get('body_contains', [])}")

    # 连接邮箱
    print(f"\n【连接邮箱】{IMAP_HOST}")
    mail_conn = imaplib.IMAP4_SSL(IMAP_HOST)
    mail_conn.login(IMAP_USER, IMAP_PASS)
    mail_conn.select(MAIL_CHECK_FOLDER)

    # 搜索邮件（最近5天）
    since_date = (datetime.now() - timedelta(days=5)).strftime("%d-%b-%Y")
    print(f"\n【搜索邮件】条件：{MAIL_SEARCH_CRITERIA} SINCE {since_date}")

    status, messages = mail_conn.search(None, MAIL_SEARCH_CRITERIA, f'SINCE {since_date}')
    if status != 'OK':
        print("未找到邮件")
        return

    mail_ids = messages[0].split()
    print(f"找到邮件：{len(mail_ids)} 封\n")

    # 解析每封邮件
    matched_count = 0
    for i, num in enumerate(mail_ids, 1):
        status, data = mail_conn.fetch(num, '(RFC822)')
        msg = email.message_from_bytes(data[0][1])

        message_id = decode_mail_header(msg.get("Message-ID", ""))
        subject = decode_mail_header(msg.get("Subject", "(无主题)"))
        sender = decode_mail_header(msg.get("From", "(未知发件人)"))
        body = get_mail_body(msg)
        body_preview = body[:100].replace('\n', ' ') if len(body) > 100 else body.replace('\n', ' ')

        # 检查规则匹配
        matched_rules = rule_loader.match_rules(subject, sender, body)

        print(f"【邮件 {i}/{len(mail_ids)}】编号: {num.decode()}")
        print(f"  Message-ID: {message_id[:60]}...")
        print(f"  主题: {subject}")
        print(f"  发件人: {sender}")
        print(f"  正文预览: {body_preview}...")

        if matched_rules:
            matched_count += 1
            rule_names = ", ".join([r.rule_name for r in matched_rules])
            print(f"  ✅ 匹配规则: {rule_names}")
        else:
            print(f"  ❌ 未匹配任何规则")

        print()

    mail_conn.close()
    mail_conn.logout()

    print("=" * 80)
    print(f"总结：共 {len(mail_ids)} 封邮件，匹配 {matched_count} 封")
    print("=" * 80)


if __name__ == "__main__":
    try:
        debug_mail_matching()
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
