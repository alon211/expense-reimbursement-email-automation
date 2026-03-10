# -*- coding: utf-8 -*-
"""数据库集成测试

测试数据库与配置的集成使用。
"""
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from config.settings import EXTRACT_ROOT_DIR
from core.database import DatabaseManager
from core.models import ExtractedEmail, ExtractionHistory
from datetime import datetime


def test_integration():
    """测试数据库与配置集成"""
    print("=" * 60)
    print("数据库集成测试")
    print("=" * 60)

    # 1. 检查配置
    print(f"\n【配置检查】提取根目录：{EXTRACT_ROOT_DIR}")

    # 2. 创建数据库路径
    db_path = Path(EXTRACT_ROOT_DIR) / "data.db"
    print(f"【数据库路径】{db_path}")

    # 3. 初始化数据库
    print(f"\n【初始化数据库】")
    db = DatabaseManager(str(db_path))
    print(f"✓ 数据库初始化成功")

    # 4. 测试实际使用场景：模拟邮件提取流程
    print(f"\n【模拟邮件提取流程】")

    # 模拟第一封邮件
    message_id_1 = "<msg001@example.com>"
    print(f"\n1. 检查邮件是否已提取：{message_id_1}")
    if not db.is_email_extracted(message_id_1):
        print(f"   → 未提取，开始处理...")

        # 添加提取记录
        email_record = ExtractedEmail(
            message_id=message_id_1,
            subject="差旅费报销单",
            sender="finance@company.com",
            rule_id="rule_001",
            extracted_at=datetime.now(),
            storage_path=str(Path(EXTRACT_ROOT_DIR) / "2026-03-11_120000"),
            attachment_count=3,
            body_file_path=str(Path(EXTRACT_ROOT_DIR) / "2026-03-11_120000" / "bodies" / "rule_001" / "msg001.txt")
        )
        record_id = db.add_extracted_email(email_record)
        print(f"   ✓ 已添加提取记录（ID: {record_id}）")

        # 添加历史
        history = ExtractionHistory(
            message_id=message_id_1,
            rule_id="rule_001",
            action="extracted_with_attachments"
        )
        db.add_extraction_history(history)
        print(f"   ✓ 已添加提取历史")

    # 5. 尝试重复提取（应该被阻止）
    print(f"\n2. 模拟重复提取：{message_id_1}")
    if db.is_email_extracted(message_id_1):
        print(f"   → ⚠ 邮件已提取，跳过处理")
    else:
        print(f"   → 开始处理...")

    # 6. 模拟第二封邮件
    message_id_2 = "<msg002@rails.com>"
    print(f"\n3. 处理新邮件：{message_id_2}")
    if not db.is_email_extracted(message_id_2):
        email_record = ExtractedEmail(
            message_id=message_id_2,
            subject="12306 订单通知",
            sender="12306@rails.com",
            rule_id="rule_002",
            extracted_at=datetime.now(),
            storage_path=str(Path(EXTRACT_ROOT_DIR) / "2026-03-11_120001"),
            attachment_count=1,
            body_file_path=str(Path(EXTRACT_ROOT_DIR) / "2026-03-11_120001" / "bodies" / "rule_002" / "msg002.txt")
        )
        db.add_extracted_email(email_record)
        print(f"   ✓ 已添加邮件记录")

    # 7. 查看所有提取记录
    print(f"\n4. 查看所有提取记录：")
    all_emails = db.get_all_extracted_emails(limit=10)
    for email in all_emails:
        print(f"   - [{email.id}] {email.subject}")
        print(f"     发件人: {email.sender}")
        print(f"     规则: {email.rule_id}")
        print(f"     附件数: {email.attachment_count}")

    # 8. 获取统计信息
    print(f"\n5. 数据库统计：")
    stats = db.get_statistics()
    print(f"   - 总邮件数: {stats['total_emails']}")
    print(f"   - 按规则分组:")
    for rule_id, count in stats['by_rule'].items():
        print(f"     • {rule_id}: {count} 封")

    # 9. 清理测试数据
    print(f"\n【清理测试数据】")
    if db_path.exists():
        db_path.unlink()
        print(f"✓ 已删除测试数据库")

    print("\n" + "=" * 60)
    print("集成测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    test_integration()
