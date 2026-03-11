#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试数据库清理功能

测试场景：
1. 场景 1：正常清理（文件存在）→ 验证不会误删有效记录
2. 场景 2：清理无效记录（文件不存在）→ 验证正确删除无效记录
3. 场景 3：自动清理功能（get_existing_mail_dates）→ 验证预检查逻辑
"""
import sys
import io
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# 设置标准输出编码为 UTF-8 (Windows 中文显示修复)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from core.database import DatabaseManager
from core.models import ExtractedEmail, ExtractionHistory


def create_temp_test_env():
    """创建临时测试环境"""
    temp_dir = Path(tempfile.mkdtemp())
    test_db_path = temp_dir / "test.db"
    test_storage_dir = temp_dir / "storage"
    test_storage_dir.mkdir()

    return temp_dir, test_db_path, test_storage_dir


def test_scenario_1_normal_cleanup():
    """场景 1：正常清理（文件存在）"""
    print("\n" + "=" * 60)
    print("测试场景 1：正常清理（文件存在）")
    print("=" * 60)

    temp_dir, test_db_path, test_storage_dir = create_temp_test_env()

    try:
        db = DatabaseManager(str(test_db_path))

        # 创建 3 条记录，文件都存在
        for i in range(1, 4):
            message_id = f"test_msg_{i}"
            storage_path = test_storage_dir / f"email_{i}"
            storage_path.mkdir()
            body_file = storage_path / "body.html"
            body_file.write_text(f"<body>Email {i}</body>")

            email_record = ExtractedEmail(
                message_id=message_id,
                subject=f"Test Email {i}",
                sender="test@example.com",
                rule_id="rule_001",
                mail_date=f"2026-03-11 10:{30+i}:00",
                extracted_at=datetime.now(),
                storage_path=str(storage_path),
                attachment_count=0,
                body_file_path=str(body_file)
            )
            db.add_extracted_email(email_record)

            # 添加历史记录
            history = ExtractionHistory(
                message_id=message_id,
                rule_id="rule_001",
                action="matched"
            )
            db.add_extraction_history(history)

        # 验证初始状态
        stats_before = db.get_statistics()
        print(f"\n📊 清理前统计：")
        print(f"  邮件记录数: {stats_before['total_emails']}")
        print(f"  历史记录数: {stats_before['total_history']}")

        # 执行清理
        deleted_count = db.clean_invalid_records()

        # 验证清理后状态
        stats_after = db.get_statistics()
        print(f"\n📊 清理后统计：")
        print(f"  邮件记录数: {stats_after['total_emails']}")
        print(f"  历史记录数: {stats_after['total_history']}")
        print(f"  删除记录数: {deleted_count}")

        # 断言
        assert deleted_count == 0, "不应该删除任何记录"
        assert stats_after['total_emails'] == 3, "应该保留 3 条邮件记录"
        assert stats_after['total_history'] == 3, "应该保留 3 条历史记录"

        print("\n✅ 测试通过：没有误删有效记录")

    finally:
        shutil.rmtree(temp_dir)


def test_scenario_2_cleanup_invalid():
    """场景 2：清理无效记录（文件不存在）"""
    print("\n" + "=" * 60)
    print("测试场景 2：清理无效记录（文件不存在）")
    print("=" * 60)

    temp_dir, test_db_path, test_storage_dir = create_temp_test_env()

    try:
        db = DatabaseManager(str(test_db_path))

        # 记录 1：文件存在
        storage_path_1 = test_storage_dir / "email_1"
        storage_path_1.mkdir()
        body_file_1 = storage_path_1 / "body.html"
        body_file_1.write_text("<body>Email 1</body>")

        email_1 = ExtractedEmail(
            message_id="test_msg_valid",
            subject="Valid Email",
            sender="test@example.com",
            rule_id="rule_001",
            mail_date="2026-03-11 10:30:00",
            extracted_at=datetime.now(),
            storage_path=str(storage_path_1),
            attachment_count=0,
            body_file_path=str(body_file_1)
        )
        db.add_extracted_email(email_1)
        db.add_extraction_history(ExtractionHistory(
            message_id="test_msg_valid",
            rule_id="rule_001",
            action="matched"
        ))

        # 记录 2：文件不存在
        email_2 = ExtractedEmail(
            message_id="test_msg_invalid_1",
            subject="Invalid Email 1",
            sender="test@example.com",
            rule_id="rule_001",
            mail_date="2026-03-11 10:31:00",
            extracted_at=datetime.now(),
            storage_path=str(test_storage_dir / "nonexistent_1"),
            attachment_count=0,
            body_file_path=str(test_storage_dir / "nonexistent_1_body.html")
        )
        db.add_extracted_email(email_2)
        db.add_extraction_history(ExtractionHistory(
            message_id="test_msg_invalid_1",
            rule_id="rule_001",
            action="matched"
        ))

        # 记录 3：文件不存在
        email_3 = ExtractedEmail(
            message_id="test_msg_invalid_2",
            subject="Invalid Email 2",
            sender="test@example.com",
            rule_id="rule_001",
            mail_date="2026-03-11 10:32:00",
            extracted_at=datetime.now(),
            storage_path=str(test_storage_dir / "nonexistent_2"),
            attachment_count=0,
            body_file_path=str(test_storage_dir / "nonexistent_2_body.html")
        )
        db.add_extracted_email(email_3)
        db.add_extraction_history(ExtractionHistory(
            message_id="test_msg_invalid_2",
            rule_id="rule_001",
            action="matched"
        ))

        # 验证初始状态
        stats_before = db.get_statistics()
        print(f"\n📊 清理前统计：")
        print(f"  邮件记录数: {stats_before['total_emails']}")
        print(f"  历史记录数: {stats_before['total_history']}")

        # 执行清理
        deleted_count = db.clean_invalid_records()

        # 验证清理后状态
        stats_after = db.get_statistics()
        print(f"\n📊 清理后统计：")
        print(f"  邮件记录数: {stats_after['total_emails']}")
        print(f"  历史记录数: {stats_after['total_history']}")
        print(f"  删除记录数: {deleted_count}")

        # 断言
        assert deleted_count == 2, f"应该删除 2 条无效记录，实际删除 {deleted_count} 条"
        assert stats_after['total_emails'] == 1, "应该保留 1 条有效邮件记录"

        # 验证历史记录也被正确删除
        history_list = db.get_extraction_history("test_msg_valid")
        assert len(history_list) == 1, "有效记录的历史应该被保留"

        history_invalid_1 = db.get_extraction_history("test_msg_invalid_1")
        history_invalid_2 = db.get_extraction_history("test_msg_invalid_2")
        assert len(history_invalid_1) == 0, "无效记录 1 的历史应该被删除"
        assert len(history_invalid_2) == 0, "无效记录 2 的历史应该被删除"

        print("\n✅ 测试通过：正确删除了 2 条无效记录及其关联历史")

    finally:
        shutil.rmtree(temp_dir)


def test_scenario_3_auto_cleanup():
    """场景 3：预检查自动清理"""
    print("\n" + "=" * 60)
    print("测试场景 3：预检查自动清理（get_existing_mail_dates）")
    print("=" * 60)

    temp_dir, test_db_path, test_storage_dir = create_temp_test_env()

    try:
        db = DatabaseManager(str(test_db_path))

        # 记录 1：文件存在
        storage_path_1 = test_storage_dir / "email_1"
        storage_path_1.mkdir()
        body_file_1 = storage_path_1 / "body.html"
        body_file_1.write_text("<body>Email 1</body>")

        email_1 = ExtractedEmail(
            message_id="test_msg_valid",
            subject="Valid Email",
            sender="test@example.com",
            rule_id="rule_001",
            mail_date="2026-03-11 10:30:00",
            extracted_at=datetime.now(),
            storage_path=str(storage_path_1),
            attachment_count=0,
            body_file_path=str(body_file_1)
        )
        db.add_extracted_email(email_1)
        db.add_extraction_history(ExtractionHistory(
            message_id="test_msg_valid",
            rule_id="rule_001",
            action="matched"
        ))

        # 记录 2：文件不存在
        email_2 = ExtractedEmail(
            message_id="test_msg_invalid",
            subject="Invalid Email",
            sender="test@example.com",
            rule_id="rule_001",
            mail_date="2026-03-11 10:31:00",
            extracted_at=datetime.now(),
            storage_path=str(test_storage_dir / "nonexistent"),
            attachment_count=0,
            body_file_path=str(test_storage_dir / "nonexistent_body.html")
        )
        db.add_extracted_email(email_2)
        db.add_extraction_history(ExtractionHistory(
            message_id="test_msg_invalid",
            rule_id="rule_001",
            action="matched"
        ))

        # 验证初始状态
        stats_before = db.get_statistics()
        print(f"\n📊 预检查前统计：")
        print(f"  邮件记录数: {stats_before['total_emails']}")
        print(f"  历史记录数: {stats_before['total_history']}")

        # 执行预检查（自动清理）
        existing_dates = db.get_existing_mail_dates()

        # 验证预检查后状态
        stats_after = db.get_statistics()
        print(f"\n📊 预检查后统计：")
        print(f"  邮件记录数: {stats_after['total_emails']}")
        print(f"  历史记录数: {stats_after['total_history']}")
        print(f"  已提取且文件存在的邮件: {len(existing_dates)}")
        print(f"  mail_date 集合: {existing_dates}")

        # 断言
        assert len(existing_dates) == 1, "应该返回 1 个有效 mail_date"
        assert "2026-03-11 10:30:00" in existing_dates, "应该包含有效记录的 mail_date"
        assert stats_after['total_emails'] == 1, "应该自动删除无效记录，只保留 1 条"

        # 验证历史记录也被自动删除
        history_valid = db.get_extraction_history("test_msg_valid")
        history_invalid = db.get_extraction_history("test_msg_invalid")
        assert len(history_valid) == 1, "有效记录的历史应该被保留"
        assert len(history_invalid) == 0, "无效记录的历史应该被自动删除"

        print("\n✅ 测试通过：自动清理功能正常工作")

    finally:
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    try:
        test_scenario_1_normal_cleanup()
        test_scenario_2_cleanup_invalid()
        test_scenario_3_auto_cleanup()

        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n❌ 测试失败：{e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试异常：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
