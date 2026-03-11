# -*- coding: utf-8 -*-
"""测试 rule_002 修复后的匹配效果"""
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from config.settings import EXTRACT_ROOT_DIR, PARSE_RULES_JSON_PATH
from core.database import DatabaseManager
from core.rule_loader import RuleLoader
from core.models import ExtractedEmail, ExtractionHistory
from datetime import datetime
import imaplib
import email
from utils.header_decoder import decode_mail_header
from config.settings import IMAP_HOST, IMAP_USER, IMAP_PASS, MAIL_CHECK_FOLDER

print("=" * 60)
print("测试 rule_002 修复：匹配 12306 邮件")
print("=" * 60)

# 1. 加载规则
print(f"\n【步骤1】加载规则...")
rule_loader = RuleLoader(PARSE_RULES_JSON_PATH)
rule_002 = rule_loader.get_rule_by_id("rule_002")
print(f"✓ rule_002 配置：")
print(f"  发件人包含: {rule_002.match_conditions.get('sender_contains', [])}")

# 2. 连接邮箱
print(f"\n【步骤2】搜索 12306 邮件...")
mail_conn = imaplib.IMAP4_SSL(IMAP_HOST)
mail_conn.login(IMAP_USER, IMAP_PASS)
mail_conn.select(MAIL_CHECK_FOLDER)

# 搜索最近5天的所有邮件（包括已读）
from datetime import timedelta
since_date = (datetime.now() - timedelta(days=5)).strftime("%d-%b-%Y")
status, messages = mail_conn.search(None, 'ALL', f'SINCE {since_date}')
mail_ids = messages[0].split()
print(f"✓ 找到 {len(mail_ids)} 封邮件")

# 3. 查找 12306 邮件
print(f"\n【步骤3】查找 12306 邮件...")
found_12306 = []

for num in mail_ids[:50]:  # 只检查前50封
    status, data = mail_conn.fetch(num, '(RFC822)')
    msg = email.message_from_bytes(data[0][1])

    sender = decode_mail_header(msg.get("From", ""))
    subject = decode_mail_header(msg.get("Subject", ""))

    # 检查是否匹配
    matched = rule_002.match("", sender, "")
    if matched:
        found_12306.append({
            "sender": sender,
            "subject": subject
        })
        print(f"  ✓ 找到：{subject[:50]}...")
        print(f"    发件人: {sender}")

mail_conn.close()
mail_conn.logout()

# 4. 结果
print(f"\n【结果】")
print(f"  共找到 {len(found_12306)} 封 12306 邮件")

if found_12306:
    print(f"\n✅ rule_002 修复成功！")
    print(f"\n发件人示例：")
    for i, mail in enumerate(found_12306[:3], 1):
        print(f"  {i}. {mail['sender']}")
else:
    print(f"\n⚠️ 未找到 12306 邮件")
    print(f"   可能原因：")
    print(f"   1. 最近5天没有收到 12306 邮件")
    print(f"   2. 邮件在更早的时间")

print("\n" + "=" * 60)
