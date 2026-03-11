#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查数据库状态"""
import sys
import io
import os

# 设置标准输出编码为 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from config.settings import EXTRACT_ROOT_DIR
from core.database import DatabaseManager
from pathlib import Path


def check_database():
    """检查数据库状态"""
    print("=" * 60)
    print("检查数据库状态")
    print("=" * 60)

    db_path = os.path.join(EXTRACT_ROOT_DIR, "data.db")
    print(f"数据库路径：{db_path}")

    if not Path(db_path).exists():
        print("❌ 数据库文件不存在！")
        return

    db = DatabaseManager(db_path)

    # 获取统计信息
    stats = db.get_statistics()
    print(f"\n数据库统计：")
    print(f"  总邮件记录数：{stats['total_emails']}")
    print(f"  按规则分组：")
    for rule_id, count in stats['by_rule'].items():
        print(f"    - {rule_id}: {count} 条")
    print(f"  提取历史记录数：{stats['total_history']}")

    # 获取最近提取的邮件
    print(f"\n最近提取的邮件（前 5 条）：")
    recent_emails = db.get_all_extracted_emails(limit=5)
    for i, email in enumerate(recent_emails, 1):
        print(f"\n  {i}. 主题：{email.subject}")
        print(f"     发件人：{email.sender}")
        print(f"     日期：{email.mail_date}")
        print(f"     存储路径：{email.storage_path}")
        print(f"     正文文件：{email.body_file_path}")
        print(f"     附件数：{email.attachment_count}")

    # 检查文件是否存在
    print(f"\n检查文件是否存在...")
    invalid_count = 0
    for email in recent_emails:
        storage_exists = email.storage_path and Path(email.storage_path).exists()
        body_exists = email.body_file_path and Path(email.body_file_path).exists()

        if not storage_exists and not body_exists:
            invalid_count += 1
            print(f"  ⚠️  邮件 {email.subject} 的文件不存在")

    if invalid_count == 0:
        print(f"  ✅ 所有文件的文件都存在")
    else:
        print(f"  ❌ 发现 {invalid_count} 条记录的文件不存在")

    print("\n" + "=" * 60)
    print("✅ 检查完成")
    print("=" * 60)


if __name__ == "__main__":
    check_database()
