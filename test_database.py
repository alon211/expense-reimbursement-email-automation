# -*- coding: utf-8 -*-
"""数据库模块测试脚本

测试 DatabaseManager 的各项功能。
"""
import sys
import io
from pathlib import Path
from datetime import datetime

# 设置 UTF-8 编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from core.database import DatabaseManager
from core.models import ExtractedEmail, ExtractionHistory


def test_database():
    """测试数据库功能"""
    print("=" * 60)
    print("开始测试数据库模块")
    print("=" * 60)

    # 使用测试数据库
    test_db_path = "./extracted_mails/test.db"

    # 如果测试数据库已存在，先删除
    if Path(test_db_path).exists():
        Path(test_db_path).unlink()
        print(f"✓ 已删除旧的测试数据库：{test_db_path}")

    # 初始化数据库
    print("\n【测试1】初始化数据库...")
    db = DatabaseManager(test_db_path)
    print(f"✓ 数据库初始化成功：{test_db_path}")

    # 测试去重检查
    print("\n【测试2】测试去重功能...")
    test_message_id = "<test.message.123@example.com>"
    is_extracted = db.is_email_extracted(test_message_id)
    print(f"✓ 检查邮件 {test_message_id} 是否已提取：{is_extracted}（应该是 False）")

    # 添加测试记录
    print("\n【测试3】添加邮件提取记录...")
    email_record = ExtractedEmail(
        message_id=test_message_id,
        subject="测试邮件主题",
        sender="test@example.com",
        rule_id="rule_001",
        extracted_at=datetime.now(),
        storage_path="./extracted_mails/2026-03-11_120000",
        attachment_count=2,
        body_file_path="./extracted_mails/2026-03-11_120000/bodies/rule_001/test.txt"
    )
    record_id = db.add_extracted_email(email_record)
    print(f"✓ 成功添加邮件记录，ID：{record_id}")

    # 再次检查去重
    print("\n【测试4】再次检查去重...")
    is_extracted = db.is_email_extracted(test_message_id)
    print(f"✓ 检查邮件是否已提取：{is_extracted}（应该是 True）")

    # 获取邮件记录
    print("\n【测试5】获取邮件记录...")
    retrieved_email = db.get_extracted_email(test_message_id)
    if retrieved_email:
        print(f"✓ 成功获取邮件记录：")
        print(f"  - 主题：{retrieved_email.subject}")
        print(f"  - 发件人：{retrieved_email.sender}")
        print(f"  - 规则ID：{retrieved_email.rule_id}")
        print(f"  - 附件数：{retrieved_email.attachment_count}")
    else:
        print("✗ 获取邮件记录失败")

    # 添加提取历史
    print("\n【测试6】添加提取历史...")
    history = ExtractionHistory(
        message_id=test_message_id,
        rule_id="rule_001",
        action="extracted",
        created_at=datetime.now()
    )
    history_id = db.add_extraction_history(history)
    print(f"✓ 成功添加历史记录，ID：{history_id}")

    # 获取历史记录
    print("\n【测试7】获取提取历史...")
    history_list = db.get_extraction_history(test_message_id)
    print(f"✓ 找到 {len(history_list)} 条历史记录")
    for h in history_list:
        print(f"  - 规则ID：{h.rule_id}，操作：{h.action}")

    # 添加多条记录用于统计测试
    print("\n【测试8】添加更多测试记录...")
    for i in range(3):
        email = ExtractedEmail(
            message_id=f"<test.message.{i}@example.com>",
            subject=f"测试邮件 {i}",
            sender=f"sender{i}@example.com",
            rule_id="rule_002" if i > 0 else "rule_001",
            extracted_at=datetime.now()
        )
        db.add_extracted_email(email)
    print("✓ 已添加 3 条额外记录")

    # 获取统计信息
    print("\n【测试9】获取统计信息...")
    stats = db.get_statistics()
    print(f"✓ 数据库统计：")
    print(f"  - 总邮件数：{stats['total_emails']}")
    print(f"  - 历史记录数：{stats['total_history']}")
    print(f"  - 按规则分组：{stats['by_rule']}")

    # 获取所有记录
    print("\n【测试10】获取所有邮件记录...")
    all_emails = db.get_all_extracted_emails(limit=10)
    print(f"✓ 找到 {len(all_emails)} 条记录")
    for email in all_emails:
        print(f"  - [{email.id}] {email.subject} ({email.sender})")

    # 测试删除记录
    print("\n【测试11】测试删除记录...")
    deleted = db.delete_email_record(test_message_id)
    print(f"✓ 删除结果：{deleted}")
    is_extracted = db.is_email_extracted(test_message_id)
    print(f"  删除后是否还存在：{is_extracted}（应该是 False）")

    # 清理测试数据库
    print("\n【测试12】清理测试数据库...")
    if Path(test_db_path).exists():
        Path(test_db_path).unlink()
        print(f"✓ 已删除测试数据库：{test_db_path}")

    print("\n" + "=" * 60)
    print("所有测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    test_database()
