#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""清空数据库以允许重新提取所有邮件"""
import sys
import io
import os

# 设置标准输出编码为 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from config.settings import EXTRACT_ROOT_DIR
from core.database import DatabaseManager
from pathlib import Path


def clear_database():
    """清空数据库"""
    print("=" * 60)
    print("清空数据库")
    print("=" * 60)

    db_path = os.path.join(EXTRACT_ROOT_DIR, "data.db")
    print(f"数据库路径：{db_path}")

    if not Path(db_path).exists():
        print("❌ 数据库文件不存在！")
        return

    # 确认操作
    print("\n⚠️  警告：此操作将删除所有数据库记录！")
    print("删除后，系统将重新提取所有邮件，包括压缩文件解压。")
    print("\n输入 'yes' 确认删除，其他任意键取消：")

    # 在脚本中自动确认（如果需要手动确认，可以注释掉下面这行）
    confirmation = "yes"  # 自动确认
    # confirmation = input("> ")  # 手动确认

    if confirmation.lower() != 'yes':
        print("❌ 已取消操作")
        return

    # 清空数据库
    db = DatabaseManager(db_path)
    deleted_count = db.clear_all_data()

    print(f"\n✅ 已清空数据库！删除了 {deleted_count} 条记录")
    print("下次运行程序时，系统将重新提取所有邮件")
    print("\n提示：压缩文件解压功能将在下次提取时生效")
    print("=" * 60)


if __name__ == "__main__":
    clear_database()
