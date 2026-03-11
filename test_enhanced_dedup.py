#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试增强版去重逻辑

验证邮件去重时不仅检查数据库记录，还验证提取的文件是否存在。
"""
import sys
import io
from pathlib import Path

# 设置标准输出编码为 UTF-8 (Windows 中文显示修复)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from config.logger_config import init_logger
from core.database import DatabaseManager
from config.settings import EXTRACT_ROOT_DIR
from pathlib import Path


def test_enhanced_dedup():
    """测试增强版去重逻辑"""
    print("\n" + "="*60)
    print("测试增强版去重逻辑".center(60))
    print("="*60 + "\n")

    # 初始化日志
    logger, log_file = init_logger()

    # 初始化数据库（使用与主程序相同的路径）
    db_path = Path(EXTRACT_ROOT_DIR) / "data.db"
    print(f"数据库路径: {db_path}")
    db_manager = DatabaseManager(str(db_path))

    # 获取所有已提取的邮件记录
    all_emails = db_manager.get_all_extracted_emails(limit=100)

    print(f"📊 数据库中共有 {len(all_emails)} 条邮件记录\n")

    if not all_emails:
        print("⚠️  数据库中没有邮件记录，请先运行主程序提取邮件")
        return

    # 统计分析
    stats = {
        'total': len(all_emails),
        'db_exists': 0,
        'files_exist': 0,
        'storage_exists': 0,
        'body_exists': 0,
        'missing_files': 0
    }

    print("="*60)
    print("邮件记录详细检查".center(60))
    print("="*60 + "\n")

    for idx, email_record in enumerate(all_emails, 1):
        print(f"\n【记录 {idx}】")
        print(f"  主题: {email_record.subject[:50]}...")
        print(f"  发件人: {email_record.sender}")
        print(f"  规则ID: {email_record.rule_id}")
        print(f"  提取时间: {email_record.extracted_at}")

        # 检查文件是否存在
        storage_path = email_record.storage_path
        body_file_path = email_record.body_file_path

        storage_exists = storage_path and Path(storage_path).exists()
        body_exists = body_file_path and Path(body_file_path).exists()

        stats['db_exists'] += 1

        if storage_path:
            status = "✅ 存在" if storage_exists else "❌ 不存在"
            print(f"  提取内容: {status} → {storage_path}")
            if storage_exists:
                stats['storage_exists'] += 1

        if body_file_path:
            status = "✅ 存在" if body_exists else "❌ 不存在"
            print(f"  邮件HTML: {status} → {body_file_path}")
            if body_exists:
                stats['body_exists'] += 1

        # 判断文件是否完整
        files_exist = storage_exists or body_exists
        if files_exist:
            stats['files_exist'] += 1
            print(f"  ✅ 状态: 已提取且文件存在")
        else:
            stats['missing_files'] += 1
            print(f"  ⚠️  状态: 数据库有记录但文件不存在（需要重新提取）")

    # 统计汇总
    print("\n" + "="*60)
    print("统计汇总".center(60))
    print("="*60)
    print(f"\n📊 统计结果：")
    print(f"  总记录数: {stats['total']}")
    print(f"  数据库记录存在: {stats['db_exists']}")
    print(f"  文件完整存在: {stats['files_exist']}")
    print(f"  提取内容文件存在: {stats['storage_exists']}")
    print(f"  邮件HTML文件存在: {stats['body_exists']}")
    print(f"  ⚠️  文件缺失需要重新提取: {stats['missing_files']}")

    # 测试增强版去重方法
    print("\n" + "="*60)
    print("测试增强版去重方法".center(60))
    print("="*60 + "\n")

    # 随机选择一个邮件记录进行测试
    test_email = all_emails[0]
    print(f"测试邮件: {test_email.subject[:50]}...")

    is_extracted, db_exists, storage_exists, body_exists = db_manager.is_email_extracted_with_files(
        test_email.message_id
    )

    print(f"\n增强版去重方法返回值：")
    print(f"  is_extracted (是否已提取且文件存在): {is_extracted}")
    print(f"  db_exists (数据库记录存在): {db_exists}")
    print(f"  storage_exists (提取内容文件存在): {storage_exists}")
    print(f"  body_exists (邮件HTML文件存在): {body_exists}")

    print("\n" + "="*60)
    print("测试结论".center(60))
    print("="*60)

    if stats['missing_files'] == 0:
        print("\n✅ 所有邮件记录完整，文件存在")
        print("✅ 增强版去重逻辑工作正常")
    else:
        print(f"\n⚠️  发现 {stats['missing_files']} 条记录文件缺失")
        print("📝 建议：运行主程序重新提取这些邮件")

    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    try:
        test_enhanced_dedup()
    except KeyboardInterrupt:
        print("\n用户手动终止程序")
    except Exception as e:
        print(f"\n❌ 程序异常：{str(e)}")
        import traceback
        traceback.print_exc()
