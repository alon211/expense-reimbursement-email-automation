# -*- coding: utf-8 -*-
"""测试数据库清空配置功能"""
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from config.settings import EXTRACT_ROOT_DIR, CLEAR_DB_ON_STARTUP
from core.database import DatabaseManager
from core.models import ExtractedEmail, ExtractionHistory
from datetime import datetime


def test_clear_db_function():
    """测试数据库清空功能"""
    print("=" * 60)
    print("数据库清空功能测试")
    print("=" * 60)

    # 显示当前配置
    print(f"\n【当前配置】")
    print(f"  CLEAR_DB_ON_STARTUP = {CLEAR_DB_ON_STARTUP}")
    print(f"  说明：{'启动时会清空数据库' if CLEAR_DB_ON_STARTUP else '启动时保留数据库'}")

    # 初始化数据库
    db_path = Path(EXTRACT_ROOT_DIR) / "data.db"
    db = DatabaseManager(str(db_path))

    # 查看当前状态
    print(f"\n【步骤1】查看数据库初始状态...")
    stats = db.get_statistics()
    print(f"  邮件记录：{stats['total_emails']} 条")
    print(f"  历史记录：{stats['total_history']} 条")

    # 添加测试数据
    if stats['total_emails'] == 0:
        print(f"\n【步骤2】添加测试数据...")
        for i in range(3):
            email_record = ExtractedEmail(
                message_id=f"<test.{i}@example.com>",
                subject=f"测试邮件 {i}",
                sender=f"sender{i}@example.com",
                rule_id="rule_001",
                extracted_at=datetime.now(),
                storage_path="",
                attachment_count=0,
                body_file_path=""
            )
            db.add_extracted_email(email_record)

            history = ExtractionHistory(
                message_id=f"<test.{i}@example.com>",
                rule_id="rule_001",
                action="test"
            )
            db.add_extraction_history(history)

        stats = db.get_statistics()
        print(f"  ✓ 已添加 3 条测试数据")
        print(f"  邮件记录：{stats['total_emails']} 条")
        print(f"  历史记录：{stats['total_history']} 条")

    # 测试清空功能
    print(f"\n【步骤3】测试清空功能...")
    print(f"  调用 db.clear_all_data()...")

    result = db.clear_all_data()

    print(f"  ✓ 清空完成")
    print(f"  删除邮件记录：{result['emails_deleted']} 条")
    print(f"  删除历史记录：{result['history_deleted']} 条")

    # 验证清空结果
    print(f"\n【步骤4】验证清空结果...")
    stats = db.get_statistics()
    print(f"  邮件记录：{stats['total_emails']} 条")
    print(f"  历史记录：{stats['total_history']} 条")

    if stats['total_emails'] == 0 and stats['total_history'] == 0:
        print(f"  ✅ 数据库已完全清空")
    else:
        print(f"  ❌ 清空失败，数据库仍有数据")

    print(f"\n" + "=" * 60)
    print(f"配置说明")
    print(f"=" * 60)
    print(f"")
    print(f"在 .env 文件中设置：")
    print(f"  CLEAR_DB_ON_STARTUP=True   # 启动时清空数据库")
    print(f"  CLEAR_DB_ON_STARTUP=False  # 启动时保留数据库（默认）")
    print(f"")
    print(f"⚠️  警告：设置为 True 会删除所有已提取的邮件记录！")
    print(f"           建议仅在开发和测试时使用。")
    print(f"=" * 60)


if __name__ == "__main__":
    test_clear_db_function()
