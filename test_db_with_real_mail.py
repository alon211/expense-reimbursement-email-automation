# -*- coding: utf-8 -*-
"""测试数据库功能 - 使用真实邮件"""
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from config.settings import EXTRACT_ROOT_DIR
from core.database import DatabaseManager
from core.email_fetcher import fetch_reimbursement_mails
from core.rule_loader import RuleLoader
from pathlib import Path

print("=" * 60)
print("测试数据库功能 - 使用真实邮件")
print("=" * 60)

# 1. 初始化数据库
print("\n【步骤1】初始化数据库...")
db_path = Path(EXTRACT_ROOT_DIR) / "data.db"
db = DatabaseManager(str(db_path))
print(f"✓ 数据库路径：{db_path}")

# 2. 查看当前记录数
stats = db.get_statistics()
print(f"\n【步骤2】当前数据库状态...")
print(f"  总邮件数：{stats['total_emails']}")
print(f"  历史记录数：{stats['total_history']}")

# 3. 加载规则
print(f"\n【步骤3】加载规则...")
rule_loader = RuleLoader("./rules/parse_rules.json")
print(f"✓ 规则数量：{len(rule_loader.get_enabled_rules())}")
for rule in rule_loader.get_enabled_rules():
    status = "✓" if rule.enabled else "✗"
    print(f"  {status} {rule.rule_id}: {rule.rule_name}")

# 4. 拉取邮件（带去重）
print(f"\n【步骤4】拉取邮件（带去重检查）...")
matched_mails = fetch_reimbursement_mails(db_manager=db)

if matched_mails:
    print(f"\n✓ 发现 {len(matched_mails)} 封新邮件！")

    # 5. 写入数据库
    print(f"\n【步骤5】写入数据库...")
    from datetime import datetime
    from core.models import ExtractedEmail, ExtractionHistory

    for i, mail in enumerate(matched_mails, 1):
        message_id = mail['message_id']
        subject = mail['subject']
        sender = mail['sender']
        matched_rules = mail.get('matched_rules', [])

        # 获取主规则ID
        primary_rule_id = matched_rules[0].rule_id if matched_rules else "unknown"

        print(f"\n  处理邮件 {i}: {subject}")
        print(f"    Message-ID: {message_id[:60]}...")
        print(f"    发件人: {sender}")
        matched_rule_names = ", ".join([r.rule_name for r in matched_rules])
        print(f"    匹配规则: {matched_rule_names}")

        # 创建提取记录
        email_record = ExtractedEmail(
            message_id=message_id,
            subject=subject,
            sender=sender,
            rule_id=primary_rule_id,
            extracted_at=datetime.now(),
            storage_path="",  # 待实现
            attachment_count=0,  # 待实现
            body_file_path=""  # 待实现
        )
        record_id = db.add_extracted_email(email_record)
        print(f"    ✓ 已记录到数据库（ID: {record_id}）")

        # 添加提取历史
        history = ExtractionHistory(
            message_id=message_id,
            rule_id=primary_rule_id,
            action="matched"
        )
        db.add_extraction_history(history)
        print(f"    ✓ 已添加提取历史")

    # 6. 查看数据库统计
    print(f"\n【步骤6】数据库更新后统计...")
    stats = db.get_statistics()
    print(f"  总邮件数：{stats['total_emails']}")
    print(f"  历史记录数：{stats['total_history']}")
    print(f"  按规则分组：")
    for rule_id, count in stats['by_rule'].items():
        print(f"    • {rule_id}: {count} 封")

    print(f"\n【步骤6】查看所有记录...")
    all_emails = db.get_all_extracted_emails(limit=10)
    for email in all_emails:
        print(f"  [{email.id}] {email.subject} - {email.rule_id}")

    print("\n✅ 数据库功能测试成功！")
else:
    print("\n⚠️  未发现匹配的邮件")
    print("   检查：")
    print("   1. 规则配置是否正确")
    print("   2. 邮箱中是否有匹配的邮件")
    print("   3. 邮件是否已经被提取过了（去重）")

print("\n" + "=" * 60)
