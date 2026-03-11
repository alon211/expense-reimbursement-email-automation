# -*- coding: utf-8 -*-
"""检查数据库内容"""
import sys
import io
import sqlite3
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

db_path = Path("./extracted_mails/data.db")

print("=" * 60)
print("数据库内容检查")
print("=" * 60)

if not db_path.exists():
    print(f"\n❌ 数据库文件不存在：{db_path}")
    sys.exit(1)

print(f"\n✓ 数据库文件：{db_path}")
print(f"✓ 文件大小：{db_path.stat().st_size} 字节")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 查看表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print(f"\n【数据库表】")
for table in tables:
    print(f"  - {table[0]}")

# 查看记录数
cursor.execute("SELECT COUNT(*) FROM extracted_emails")
count = cursor.fetchone()[0]
print(f"\n【邮件记录数】{count} 条")

if count > 0:
    print("\n【邮件列表】")
    cursor.execute("SELECT id, message_id, subject, sender, rule_id, extracted_at FROM extracted_emails ORDER BY extracted_at DESC")
    rows = cursor.fetchall()
    for row in rows:
        print(f"\n  ID: {row[0]}")
        print(f"  Message-ID: {row[1]}")
        print(f"  主题: {row[2]}")
        print(f"  发件人: {row[3]}")
        print(f"  规则: {row[4]}")
        print(f"  时间: {row[5]}")

# 查看历史记录
cursor.execute("SELECT COUNT(*) FROM extraction_history")
history_count = cursor.fetchone()[0]
print(f"\n【历史记录数】{history_count} 条")

if history_count > 0:
    print("\n【历史记录】")
    cursor.execute("SELECT * FROM extraction_history ORDER BY created_at DESC LIMIT 10")
    rows = cursor.fetchall()
    for row in rows:
        print(f"  {row[4]} - {row[2]} - {row[3]}")

conn.close()

if count == 0 and history_count == 0:
    print("\n" + "=" * 60)
    print("⚠️  数据库为空")
    print("=" * 60)
    print("\n原因分析：")
    print("1. 本次运行的23封邮件都没有匹配任何规则")
    print("2. 查看日志第26-49行，解析了23封邮件但没有匹配")
    print("3. 只有匹配规则的邮件才会记录到数据库")
    print("\n建议：")
    print("1. 检查 rules/parse_rules.json 中的规则配置")
    print("2. 查看邮件内容是否匹配规则条件")
    print("3. 可以临时添加测试规则来验证功能")
