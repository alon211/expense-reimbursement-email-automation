#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""调试数据库路径记录

检查数据库中的 storage_path 和 body_file_path 字段值。
"""
import sys
import io
import sqlite3
from pathlib import Path

# 设置标准输出编码为 UTF-8 (Windows 中文显示修复)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from config.settings import EXTRACT_ROOT_DIR

# 数据库路径
db_path = Path(EXTRACT_ROOT_DIR) / "data.db"
print(f"数据库路径: {db_path}")
print(f"数据库存在: {db_path.exists()}\n")

if not db_path.exists():
    print("❌ 数据库文件不存在，无法检查")
    sys.exit(1)

# 连接数据库
conn = sqlite3.connect(str(db_path))
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# 查询所有邮件记录
cursor.execute("SELECT * FROM extracted_emails")
rows = cursor.fetchall()

print(f"📊 数据库中共有 {len(rows)} 条邮件记录\n")

print("="*80)
print("数据库记录详细检查".center(80))
print("="*80 + "\n")

for idx, row in enumerate(rows, 1):
    print(f"【记录 {idx}】")
    print(f"  ID: {row['id']}")
    print(f"  Message-ID: {row['message_id']}")
    print(f"  主题: {row['subject'][:60]}...")
    print(f"  发件人: {row['sender'][:50]}...")
    print(f"  规则ID: {row['rule_id']}")
    print(f"  提取时间: {row['extracted_at']}")

    # 检查路径字段
    storage_path = row['storage_path']
    body_file_path = row['body_file_path']

    print(f"\n  路径字段检查:")
    if storage_path:
        storage_exists = Path(storage_path).exists()
        status = "✅ 存在" if storage_exists else "❌ 不存在"
        print(f"    storage_path: {status}")
        print(f"    值: {storage_path}")
    else:
        print(f"    storage_path: ⚠️  空值（NULL）")

    if body_file_path:
        body_exists = Path(body_file_path).exists()
        status = "✅ 存在" if body_exists else "❌ 不存在"
        print(f"    body_file_path: {status}")
        print(f"    值: {body_file_path}")
    else:
        print(f"    body_file_path: ⚠️  空值（NULL）")

    print(f"\n  附件数量: {row['attachment_count']}")
    print("-"*80)

conn.close()

print("\n" + "="*80)
print("结论".center(80))
print("="*80 + "\n")

# 检查是否有空路径
empty_storage = sum(1 for row in rows if not row['storage_path'])
empty_body = sum(1 for row in rows if not row['body_file_path'])

print(f"📊 路径字段统计:")
print(f"  空的 storage_path: {empty_storage}/{len(rows)}")
print(f"  空的 body_file_path: {empty_body}/{len(rows)}")

if empty_storage == len(rows) and empty_body == len(rows):
    print("\n⚠️  所有记录的路径字段都是空的！")
    print("📝 可能原因：邮件提取时没有正确记录文件路径")
    print("📝 建议：检查邮件提取逻辑是否正确调用了 add_extracted_email 方法")
else:
    print("\n✅ 部分记录有路径信息")
