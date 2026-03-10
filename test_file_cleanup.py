#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试文件不存在时自动清理数据库记录"""
import sys
import io
from pathlib import Path

# 设置标准输出编码为 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from core.database import DatabaseManager
from core.models import ExtractedEmail
from datetime import datetime

def test_file_cleanup():
    """测试文件不存在时自动清理数据库记录"""
    print("=" * 60)
    print("测试文件不存在时自动清理数据库记录")
    print("=" * 60)

    # 创建测试数据库
    db_path = "./test_file_cleanup.db"
    db = DatabaseManager(db_path)

    # 清空测试数据
    db.clear_all_data()

    # 创建测试记录（文件不存在的路径）
    print("\n1. 创建测试记录（文件不存在）...")
    test_record = ExtractedEmail(
        message_id="test_message_001@example.com",
        subject="测试邮件",
        sender="test@example.com",
        rule_id="rule_002",
        mail_date="Mon, 10 Mar 2026 10:00:00 +0000",
        extracted_at=datetime.now(),
        storage_path="./non_existent_dir/2026-03-10_100000",  # 不存在的路径
        attachment_count=1,
        body_file_path="./non_existent_dir/bodies/test.html"  # 不存在的路径
    )

    record_id = db.add_extracted_email(test_record)
    print(f"   ✅ 已插入测试记录，ID={record_id}")

    # 创建另一个测试记录（文件存在的路径）
    print("\n2. 创建测试记录（文件存在）...")
    # 先创建一个真实存在的文件
    real_file = Path("./test_real_file.txt")
    real_file.write_text("test content")

    test_record2 = ExtractedEmail(
        message_id="test_message_002@example.com",
        subject="测试邮件2",
        sender="test2@example.com",
        rule_id="rule_002",
        mail_date="Mon, 11 Mar 2026 10:00:00 +0000",
        extracted_at=datetime.now(),
        storage_path="./test_real_dir",  # 不存在的目录
        attachment_count=0,
        body_file_path=str(real_file)  # 存在的文件
    )

    record_id2 = db.add_extracted_email(test_record2)
    print(f"   ✅ 已插入测试记录2，ID={record_id2}")

    # 测试 get_existing_mail_dates()
    print("\n3. 测试 get_existing_mail_dates()...")
    existing_dates = db.get_existing_mail_dates()

    print(f"   找到 {len(existing_dates)} 个文件存在的邮件：")
    for date in existing_dates:
        print(f"     - {date}")

    # 验证清理结果
    print("\n4. 验证数据库记录...")
    record1 = db.get_extracted_email("test_message_001@example.com")
    record2 = db.get_extracted_email("test_message_002@example.com")

    print(f"   记录1（文件不存在）：")
    print(f"     - storage_path: '{record1.storage_path}'")
    print(f"     - body_file_path: '{record1.body_file_path}'")
    print(f"     - attachment_count: {record1.attachment_count}")
    if record1.storage_path == "" and record1.body_file_path == "" and record1.attachment_count == 0:
        print("     ✅ 文件路径已被正确清理")
    else:
        print("     ❌ 文件路径未被清理")

    print(f"\n   记录2（文件存在）：")
    print(f"     - storage_path: '{record2.storage_path}'")
    print(f"     - body_file_path: '{record2.body_file_path}'")
    if record2.body_file_path == str(real_file):
        print("     ✅ 文件路径保持不变（因为文件存在）")
    else:
        print("     ❌ 文件路径被错误修改")

    # 测试重新提取（应该能成功插入）
    print("\n5. 测试重新提取...")
    new_record = ExtractedEmail(
        message_id="test_message_001@example.com",  # 相同的 message_id
        subject="测试邮件（重新提取）",
        sender="test@example.com",
        rule_id="rule_002",
        mail_date="Mon, 10 Mar 2026 10:00:00 +0000",
        extracted_at=datetime.now(),
        storage_path="./new_extraction_dir",
        attachment_count=2,
        body_file_path="./new_extraction_dir/bodies/test.html"
    )

    # 应该是更新操作
    success = db.update_extracted_email(new_record)
    print(f"   更新记录：{'✅ 成功' if success else '❌ 失败'}")

    # 验证更新结果
    updated_record = db.get_extracted_email("test_message_001@example.com")
    print(f"   更新后的记录：")
    print(f"     - storage_path: '{updated_record.storage_path}'")
    print(f"     - attachment_count: {updated_record.attachment_count}")
    if updated_record.storage_path == "./new_extraction_dir" and updated_record.attachment_count == 2:
        print("     ✅ 记录更新成功")
    else:
        print("     ❌ 记录更新失败")

    # 清理测试文件
    print("\n6. 清理测试文件...")
    if real_file.exists():
        real_file.unlink()
        print("   ✅ 已删除测试文件")
    if Path(db_path).exists():
        Path(db_path).unlink()
        print("   ✅ 已删除测试数据库")

    print("\n" + "=" * 60)
    print("✅ 测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    test_file_cleanup()
