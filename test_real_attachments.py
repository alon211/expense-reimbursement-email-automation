#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试实际附件的解压功能"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from pathlib import Path
from core.email_extractor import EmailExtractor
from core.rule_loader import Rule

# 测试规则配置
rule_config = {
    "rule_id": "test_rule",
    "rule_name": "测试规则",
    "enabled": True,
    "extract_options": {
        "extract_attachments": True,
        "extract_body": False,
        "extract_headers": False,
        "extract_archives": True,
        "archive_password": "",
        "allowed_archive_types": [".zip", ".rar", ".7z", ".tar.gz", ".tar.bz2"]
    }
}

rule = Rule(rule_config)

# 测试附件目录
attachment_dir = Path("extracted_mails/2026-03-11_134524/attachments/rule_002")

if not attachment_dir.exists():
    print(f"❌ 附件目录不存在：{attachment_dir}")
    sys.exit(1)

print(f"✅ 附件目录存在：{attachment_dir}")

# 列出所有附件
attachments = list(attachment_dir.glob("*"))
print(f"\n📋 找到 {len(attachments)} 个文件：")
for att in attachments:
    if att.is_file():
        print(f"  - {att.name} ({att.stat().st_size} bytes)")

# 查找压缩文件
from utils.archive_utils import ArchiveExtractor

archive_extractor = ArchiveExtractor()
archive_files = []

print(f"\n📦 检查压缩文件：")
for att in attachments:
    if att.is_file():
        is_archive = archive_extractor.is_archive_file(att.name)
        archive_type = archive_extractor.get_archive_type(att.name)
        if is_archive:
            print(f"  ✅ {att.name} - 压缩文件 ({archive_type})")
            archive_files.append(att)
        else:
            print(f"  ❌ {att.name} - 非压缩文件")

if not archive_files:
    print(f"\n❌ 没有找到压缩文件")
    sys.exit(1)

print(f"\n🔧 测试解压功能：")

extractor = EmailExtractor()

# 测试解压
result = extractor.process_archived_attachments(
    attachment_paths=[str(f) for f in archive_files],
    rule=rule,
    extraction_dir=attachment_dir.parent
)

print(f"\n📊 解压结果：")
print(f"  发现压缩包：{result['archive_count']} 个")
print(f"  解压文件数：{result['extracted_count']} 个")
print(f"  解压路径：{result['extracted_paths'][:3]}..." if len(result['extracted_paths']) > 3 else f"  解压路径：{result['extracted_paths']}")

# 检查解压后的目录
print(f"\n📂 检查解压目录：")
for archive_file in archive_files:
    extract_dir = archive_file.parent / f"{archive_file.name}/"
    if extract_dir.exists():
        extracted_files = list(extract_dir.rglob("*"))
        extracted_files = [f for f in extracted_files if f.is_file()]
        print(f"  ✅ {archive_file.name}/ - {len(extracted_files)} 个文件")
    else:
        print(f"  ❌ {archive_file.name}/ - 目录不存在")
