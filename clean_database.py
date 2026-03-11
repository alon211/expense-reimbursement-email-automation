#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""手动清理数据库脚本

清空所有邮件记录和历史记录，重新开始。
"""
import sys
import io
from pathlib import Path

# 设置标准输出编码为 UTF-8 (Windows 中文显示修复)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from config.logger_config import init_logger
from core.database import DatabaseManager
from config.settings import EXTRACT_ROOT_DIR


def clean_database():
    """清理数据库"""
    print("\n" + "="*60)
    print("手动清理数据库".center(60))
    print("="*60 + "\n")

    # 初始化日志
    logger, log_file = init_logger()

    # 数据库路径
    db_path = Path(EXTRACT_ROOT_DIR) / "data.db"
    print(f"数据库路径: {db_path}")
    print(f"数据库存在: {db_path.exists()}\n")

    if not db_path.exists():
        print("❌ 数据库文件不存在，无需清理")
        return

    # 初始化数据库
    db_manager = DatabaseManager(str(db_path))

    # 获取清理前的统计信息
    print("="*60)
    print("清理前统计".center(60))
    print("="*60 + "\n")

    stats_before = db_manager.get_statistics()
    print(f"📊 清理前统计：")
    print(f"  邮件记录数: {stats_before['total_emails']}")
    print(f"  历史记录数: {stats_before['total_history']}")

    # 按规则统计
    if stats_before['by_rule']:
        print(f"\n  按规则统计:")
        for rule_id, count in stats_before['by_rule'].items():
            print(f"    {rule_id}: {count} 封")

    # 确认清理
    print("\n" + "="*60)
    print("确认操作".center(60))
    print("="*60 + "\n")

    print("⚠️  警告：此操作将清空所有邮件记录和历史记录！")
    print("📝 建议：在开发测试阶段，清理数据库可以重新开始提取邮件\n")

    # 直接清理（跳过确认，因为这是脚本）
    print("🔄 开始清理数据库...\n")

    # 执行清理
    result = db_manager.clear_all_data()

    # 显示清理结果
    print("="*60)
    print("清理结果".center(60))
    print("="*60 + "\n")

    print(f"✅ 清理完成！")
    print(f"  📧 已删除邮件记录: {result['emails_deleted']} 条")
    print(f"  📝 已删除历史记录: {result['history_deleted']} 条")

    # 验证清理结果
    print("\n" + "="*60)
    print("验证清理结果".center(60))
    print("="*60 + "\n")

    stats_after = db_manager.get_statistics()
    print(f"📊 清理后统计：")
    print(f"  邮件记录数: {stats_after['total_emails']}")
    print(f"  历史记录数: {stats_after['total_history']}")

    if stats_after['total_emails'] == 0 and stats_after['total_history'] == 0:
        print("\n✅ 数据库已完全清空")
        print("✅ 下次运行主程序将重新开始提取邮件")
    else:
        print("\n⚠️  数据库清理不完整，请检查")

    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    try:
        clean_database()
    except KeyboardInterrupt:
        print("\n\n用户手动终止清理操作")
    except Exception as e:
        print(f"\n❌ 清理过程中发生异常：{str(e)}")
        import traceback
        traceback.print_exc()
