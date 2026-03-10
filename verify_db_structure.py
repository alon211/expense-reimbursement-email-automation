# -*- coding: utf-8 -*-
"""验证数据库结构"""
import sys
import io
import sqlite3
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 创建测试数据库
db_path = "./extracted_mails/verify.db"

if Path(db_path).exists():
    Path(db_path).unlink()

from core.database import DatabaseManager

db = DatabaseManager(db_path)

print("验证数据库表结构：")
print("=" * 60)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 获取所有表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()

print("\n1. 数据库表：")
for table in tables:
    print(f"   - {table[0]}")

print("\n2. extracted_emails 表结构：")
cursor.execute("PRAGMA table_info(extracted_emails)")
columns = cursor.fetchall()
for col in columns:
    print(f"   - {col[1]} ({col[2]})")

print("\n3. extraction_history 表结构：")
cursor.execute("PRAGMA table_info(extraction_history)")
columns = cursor.fetchall()
for col in columns:
    print(f"   - {col[1]} ({col[2]})")

print("\n4. 索引：")
cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")
indexes = cursor.fetchall()
for idx in indexes:
    print(f"   - {idx[0]}")

conn.close()

# 清理
Path(db_path).unlink()
print(f"\n✓ 验证完成，已清理测试数据库")
