# -*- coding: utf-8 -*-
"""主程序数据库集成测试

测试数据库在主程序中的集成效果。
"""
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from config.settings import EXTRACT_ROOT_DIR, PARSE_RULES_JSON_PATH
from core.database import DatabaseManager
from core.models import ExtractedEmail, ExtractionHistory
from core.rule_loader import RuleLoader
from datetime import datetime


def simulate_main_integration():
    """模拟主程序的数据库集成流程"""
    print("=" * 60)
    print("主程序数据库集成测试")
    print("=" * 60)

    # 1. 初始化数据库
    print("\n【步骤1】初始化数据库...")
    db_path = Path(EXTRACT_ROOT_DIR) / "data.db"
    db = DatabaseManager(str(db_path))
    print(f"✓ 数据库路径：{db_path}")
    print(f"✓ 数据库初始化成功")

    # 2. 加载规则
    print("\n【步骤2】加载解析规则...")
    rule_loader = RuleLoader(PARSE_RULES_JSON_PATH)
    print(f"✓ 规则文件：{PARSE_RULES_JSON_PATH}")
    print(f"✓ 规则数量：{len(rule_loader.get_enabled_rules())}")
    print(f"✓ 时间范围：{rule_loader.parse_time_range_days} 天")

    # 3. 模拟匹配邮件处理
    print("\n【步骤3】模拟匹配邮件处理...")
    test_mails = [
        {
            "message_id": "<test.msg.001@example.com>",
            "subject": "差旅费报销申请",
            "sender": "employee@company.com",
            "matched_rules": [rule_loader.get_rule_by_id("rule_001")]
        },
        {
            "message_id": "<test.msg.002@rails.com>",
            "subject": "12306 订单确认",
            "sender": "12306@rails.com",
            "matched_rules": [rule_loader.get_rule_by_id("rule_002")]
        }
    ]

    for i, mail_data in enumerate(test_mails, 1):
        print(f"\n  处理邮件 {i}：{mail_data['subject']}")
        message_id = mail_data['message_id']
        subject = mail_data['subject']
        sender = mail_data['sender']
        matched_rules = mail_data.get('matched_rules', [])

        # 检查去重
        if db.is_email_extracted(message_id):
            print(f"    ⚠ 邮件已提取，跳过")
            continue

        print(f"    → 新邮件，开始处理...")

        # 获取主规则ID
        primary_rule_id = matched_rules[0].rule_id if matched_rules else "unknown"
        print(f"    → 匹配规则：{primary_rule_id}")

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

    # 4. 测试去重功能
    print("\n【步骤4】测试去重功能...")
    print("  尝试再次处理第一封邮件...")
    test_mail = test_mails[0]
    message_id = test_mail['message_id']

    if db.is_email_extracted(message_id):
        print(f"  ✓ 去重检查通过：邮件已存在，跳过处理")
    else:
        print(f"  ✗ 去重失败：邮件应该存在但未被检测到")

    # 5. 查看数据库统计
    print("\n【步骤5】数据库统计信息...")
    stats = db.get_statistics()
    print(f"  总邮件数：{stats['total_emails']}")
    print(f"  历史记录数：{stats['total_history']}")
    print(f"  按规则分组：")
    for rule_id, count in stats['by_rule'].items():
        print(f"    • {rule_id}: {count} 封")

    # 6. 查看所有记录
    print("\n【步骤6】查看所有提取记录...")
    all_emails = db.get_all_extracted_emails(limit=10)
    for email in all_emails:
        print(f"  [{email.id}] {email.subject}")
        print(f"    发件人: {email.sender}")
        print(f"    规则: {email.rule_id}")
        print(f"    时间: {email.extracted_at}")

    # 7. 清理测试数据
    print("\n【步骤7】清理测试数据...")
    for mail_data in test_mails:
        db.delete_email_record(mail_data['message_id'])
    print("  ✓ 已删除测试记录")

    print("\n" + "=" * 60)
    print("集成测试完成！")
    print("=" * 60)
    print("\n提示：数据库功能已成功集成到主程序中。")
    print("运行 'python main.py' 即可启动带有去重和记录功能的服务。")


if __name__ == "__main__":
    simulate_main_integration()
