#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试基于邮件发送时间的去重优化

验证使用 mail_date 作为唯一ID的预检查去重流程。
"""
import sys
import io
from pathlib import Path

# 设置标准输出编码为 UTF-8 (Windows 中文显示修复)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from config.logger_config import init_logger
from core.database import DatabaseManager
from config.settings import EXTRACT_ROOT_DIR


def test_mail_date_dedup():
    """测试基于 mail_date 的去重"""
    print("\n" + "="*70)
    print("测试基于邮件发送时间的去重优化".center(70))
    print("="*70 + "\n")

    # 初始化日志
    logger, log_file = init_logger()

    # 数据库路径
    db_path = Path(EXTRACT_ROOT_DIR) / "data.db"
    print(f"📂 数据库路径: {db_path}")
    print(f"📂 数据库存在: {db_path.exists()}\n")

    if not db_path.exists():
        print("❌ 数据库文件不存在，请先运行主程序提取邮件")
        return

    # 初始化数据库
    db_manager = DatabaseManager(str(db_path))

    # 获取所有已提取的邮件记录
    all_emails = db_manager.get_all_extracted_emails(limit=100)

    print(f"📊 数据库中共有 {len(all_emails)} 条邮件记录\n")

    if not all_emails:
        print("⚠️  数据库中没有邮件记录")
        return

    print("="*70)
    print("邮件记录检查".center(70))
    print("="*70 + "\n")

    # 统计
    stats = {
        'total': len(all_emails),
        'has_mail_date': 0,
        'has_storage_path': 0,
        'files_exist': 0,
        'files_missing': 0
    }

    for idx, email_record in enumerate(all_emails, 1):
        print(f"【记录 {idx}】")
        print(f"  主题: {email_record.subject[:60]}...")
        print(f"  发件人: {email_record.sender[:40]}...")
        print(f"  规则ID: {email_record.rule_id}")

        # 检查 mail_date
        mail_date = email_record.mail_date
        if mail_date:
            stats['has_mail_date'] += 1
            print(f"  邮件发送时间: {mail_date}")
        else:
            print(f"  邮件发送时间: ⚠️  未设置")

        # 检查 storage_path
        storage_path = email_record.storage_path
        if storage_path:
            stats['has_storage_path'] += 1
            storage_exists = Path(storage_path).exists()
            status = "✅ 存在" if storage_exists else "❌ 不存在"
            print(f"  提取目录: {status}")
            print(f"    路径: {storage_path}")
        else:
            print(f"  提取目录: ⚠️  未设置")

        print()

    # 测试预检查功能
    print("="*70)
    print("测试预检查功能".center(70))
    print("="*70 + "\n")

    print("📋 调用 get_existing_mail_dates() 方法...")
    existing_dates = db_manager.get_existing_mail_dates()

    print(f"✅ 找到 {len(existing_dates)} 个已提取且文件存在的邮件发送时间:")
    for idx, date_str in enumerate(sorted(existing_dates), 1):
        print(f"  {idx}. {date_str}")

    print("\n" + "="*70)
    print("优化说明".center(70))
    print("="*70)
    print()
    print("✨ 新增字段:")
    print("  - mail_date: 邮件发送时间（作为唯一标识）")
    print()
    print("✨ 新增方法:")
    print("  - get_existing_mail_dates(): 获取所有已提取且文件存在的邮件发送时间集合")
    print()
    print("✨ 优化流程:")
    print("  1. 提取前预检查：调用 get_existing_mail_dates() 获取已存在文件的邮件日期集合")
    print("  2. 匹配邮件时：检查 mail_date 是否在已存在集合中")
    print("  3. 如果存在 → 跳过提取（避免重复）")
    print("  4. 如果不存在 → 提取到新的时间戳目录")
    print()
    print("✨ 优势:")
    print("  - 保留时间戳目录（每次运行独立）")
    print("  - 避免重复提取已存在的文件")
    print("  - 基于邮件发送时间去重，比 message_id 更可靠")
    print()
    print("="*70 + "\n")


if __name__ == "__main__":
    try:
        test_mail_date_dedup()
    except KeyboardInterrupt:
        print("\n用户手动终止程序")
    except Exception as e:
        print(f"\n❌ 程序异常：{str(e)}")
        import traceback
        traceback.print_exc()
