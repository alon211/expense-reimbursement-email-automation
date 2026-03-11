# -*- coding: utf-8 -*-
"""测试主程序中的数据库清空配置集成"""
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from config.settings import EXTRACT_ROOT_DIR, CLEAR_DB_ON_STARTUP
from core.database import DatabaseManager
from core.models import ExtractedEmail, ExtractionHistory
from datetime import datetime


def simulate_main_startup():
    """模拟主程序启动时的数据库初始化流程"""
    print("=" * 60)
    print("主程序启动流程模拟")
    print("=" * 60)

    print(f"\n【配置检查】")
    print(f"  CLEAR_DB_ON_STARTUP = {CLEAR_DB_ON_STARTUP}")

    # 初始化数据库
    print(f"\n【数据库初始化】")
    db_path = Path(EXTRACT_ROOT_DIR) / "data.db"
    db = DatabaseManager(str(db_path))
    print(f"  ✓ 数据库初始化成功")

    # 根据配置决定是否清空数据库
    if CLEAR_DB_ON_STARTUP:
        print(f"\n⚠️  配置要求启动时清空数据库（CLEAR_DB_ON_STARTUP=True）")
        stats_before = db.get_statistics()
        print(f"  清空前统计：{stats_before['total_emails']} 封邮件，{stats_before['total_history']} 条历史")

        result = db.clear_all_data()

        print(f"  已清空：{result['emails_deleted']} 封邮件，{result['history_deleted']} 条历史")
        print(f"  ✅ 数据库已清空，将重新处理所有匹配的邮件")
    else:
        print(f"\n  启动时保留数据库（CLEAR_DB_ON_STARTUP=False）")
        stats = db.get_statistics()
        print(f"  当前数据库：{stats['total_emails']} 封邮件，{stats['total_history']} 条历史")

    # 如果数据库为空，添加测试数据以便下次测试
    stats = db.get_statistics()
    if stats['total_emails'] == 0:
        print(f"\n【添加测试数据】（为了下次测试）")
        for i in range(2):
            email_record = ExtractedEmail(
                message_id=f"<startup.test.{i}@example.com>",
                subject=f"启动测试邮件 {i}",
                sender=f"test{i}@example.com",
                rule_id="rule_001",
                extracted_at=datetime.now(),
                storage_path="",
                attachment_count=0,
                body_file_path=""
            )
            db.add_extracted_email(email_record)
        print(f"  ✓ 已添加 2 条测试数据")

    print(f"\n" + "=" * 60)
    print(f"测试完成")
    print(f"=" * 60)
    print(f"\n提示：")
    print(f"1. 当前配置：CLEAR_DB_ON_STARTUP={CLEAR_DB_ON_STARTUP}")
    print(f"2. 要测试清空功能，请在 .env 中设置 CLEAR_DB_ON_STARTUP=True")
    print(f"3. 然后运行 python main.py 查看清空日志")
    print(f"=" * 60)


if __name__ == "__main__":
    simulate_main_startup()
