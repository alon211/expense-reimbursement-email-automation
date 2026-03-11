#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试 TODO 3：文件提取和分类存储功能

验证邮件正文、附件的提取和分类存储是否正常工作。
"""
import sys
import io
from pathlib import Path

# 设置标准输出编码为 UTF-8 (Windows 中文显示修复)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from config.logger_config import init_logger
from core.database import DatabaseManager
from config.settings import EXTRACT_ROOT_DIR


def test_todo3_extraction():
    """测试文件提取功能"""
    print("\n" + "="*70)
    print("测试 TODO 3：文件提取和分类存储".center(70))
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
        print("📝 请运行主程序：python main.py")
        return

    print("="*70)
    print("验证文件提取功能".center(70))
    print("="*70 + "\n")

    # 统计
    stats = {
        'total': len(all_emails),
        'has_storage_path': 0,
        'has_body_file': 0,
        'has_attachments': 0,
        'files_exist': 0,
        'files_missing': 0
    }

    for idx, email_record in enumerate(all_emails, 1):
        print(f"\n【记录 {idx}】")
        print(f"  主题: {email_record.subject[:60]}...")
        print(f"  发件人: {email_record.sender[:40]}...")
        print(f"  规则ID: {email_record.rule_id}")
        print(f"  提取时间: {email_record.extracted_at}")

        # 检查 storage_path
        storage_path = email_record.storage_path
        if storage_path:
            stats['has_storage_path'] += 1
            storage_exists = Path(storage_path).exists()
            status = "✅ 存在" if storage_exists else "❌ 不存在"
            print(f"  提取目录: {status}")
            print(f"    路径: {storage_path}")

            if storage_exists:
                # 检查子目录结构
                storage_dir = Path(storage_path)
                bodies_dir = storage_dir / "bodies"
                attachments_dir = storage_dir / "attachments"
                extracted_dir = storage_dir / "extracted"

                print(f"    目录结构:")
                print(f"      bodies/: {'✅' if bodies_dir.exists() else '❌'}")
                print(f"      attachments/: {'✅' if attachments_dir.exists() else '❌'}")
                print(f"      extracted/: {'✅' if extracted_dir.exists() else '❌'}")
        else:
            print(f"  提取目录: ⚠️  未设置（可能未实现文件提取）")

        # 检查 body_file_path
        body_file_path = email_record.body_file_path
        if body_file_path:
            stats['has_body_file'] += 1
            body_exists = Path(body_file_path).exists()
            status = "✅ 存在" if body_exists else "❌ 不存在"
            print(f"  邮件正文: {status}")
            print(f"    路径: {body_file_path}")
            if body_exists:
                file_size = Path(body_file_path).stat().st_size
                print(f"    大小: {file_size} 字节")
        else:
            print(f"  邮件正文: ⚠️  未设置")

        # 检查 attachment_count
        attachment_count = email_record.attachment_count or 0
        if attachment_count > 0:
            stats['has_attachments'] += 1
            print(f"  附件数量: {attachment_count}")
        else:
            print(f"  附件数量: 无")

        # 判断文件是否完整
        files_complete = (
            (storage_path and Path(storage_path).exists()) and
            (body_file_path and Path(body_file_path).exists())
        )

        if files_complete:
            stats['files_exist'] += 1
            print(f"  ✅ 状态: 文件提取完整")
        else:
            stats['files_missing'] += 1
            print(f"  ⚠️  状态: 文件提取不完整")

    # 统计汇总
    print("\n" + "="*70)
    print("统计汇总".center(70))
    print("="*70)
    print(f"\n📊 统计结果：")
    print(f"  总记录数: {stats['total']}")
    print(f"  有提取目录: {stats['has_storage_path']}/{stats['total']}")
    print(f"  有正文文件: {stats['has_body_file']}/{stats['total']}")
    print(f"  有附件: {stats['has_attachments']}/{stats['total']}")
    print(f"  ✅ 文件完整: {stats['files_exist']}/{stats['total']}")
    print(f"  ⚠️  文件缺失: {stats['files_missing']}/{stats['total']}")

    # 测试结论
    print("\n" + "="*70)
    print("测试结论".center(70))
    print("="*70 + "\n")

    if stats['files_exist'] == stats['total']:
        print("✅ TODO 3 实现成功！")
        print("✅ 所有邮件的文件提取完整")
        print("✅ 文件分类存储正常工作")
    elif stats['has_storage_path'] > 0:
        print("⚠️  TODO 3 部分实现")
        print(f"📝 {stats['files_exist']}/{stats['total']} 封邮件提取完整")
        print(f"📝 {stats['files_missing']} 封邮件需要重新提取")
    else:
        print("❌ TODO 3 未实现")
        print("📝 所有记录都没有文件路径信息")
        print("📝 请检查 main.py 中的 TODO 3 实现")

    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    try:
        test_todo3_extraction()
    except KeyboardInterrupt:
        print("\n用户手动终止程序")
    except Exception as e:
        print(f"\n❌ 程序异常：{str(e)}")
        import traceback
        traceback.print_exc()
