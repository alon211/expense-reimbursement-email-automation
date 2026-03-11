#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""手动清理数据库中文件不存在的记录"""
import sys
import io

# 设置标准输出编码为 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from core.database import DatabaseManager


def clean_invalid_records():
    """清理所有文件不存在的数据库记录"""
    print("=" * 60)
    print("清理数据库中文件不存在的记录")
    print("=" * 60)

    # 创建数据库管理器（使用默认数据库路径）
    from config.settings import EXTRACT_ROOT_DIR
    import os
    db_path = os.path.join(EXTRACT_ROOT_DIR, "data.db")
    print(f"数据库路径：{db_path}")

    db = DatabaseManager(db_path)

    print("\n正在扫描数据库记录...")
    print("查找文件不存在的记录...\n")

    # 清理无效记录
    deleted_count = db.clean_invalid_records()

    print("\n" + "=" * 60)
    if deleted_count > 0:
        print(f"✅ 清理完成！已删除 {deleted_count} 条无效记录")
        print("下次运行程序时，这些邮件将被重新提取")
    else:
        print("✅ 没有发现无效记录，数据库状态良好")
    print("=" * 60)


if __name__ == "__main__":
    clean_invalid_records()
