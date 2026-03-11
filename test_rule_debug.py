#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试压缩文件解压流程"""
import sys
import io

# 设置标准输出编码为 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from core.rule_loader import Rule
from pathlib import Path


def test_rule_config():
    """测试规则配置"""
    print("=" * 60)
    print("测试规则配置")
    print("=" * 60)

    # 创建一个测试规则
    rule_data = {
        "rule_id": "rule_002",
        "rule_name": "12306提取",
        "enabled": True,
        "match_conditions": {
            "sender_contains": ["12306", "didifapiao", "reservation"],
            "subject_contains": [],
            "body_contains": []
        },
        "extract_options": {
            "extract_attachments": True,
            "extract_body": False,
            "extract_headers": False,
            "extract_archives": True,
            "archive_password": "",
            "allowed_archive_types": [".zip", ".rar", ".7z", ".tar.gz", ".tar.bz2"]
        }
    }

    rule = Rule(rule_data)

    print(f"\n规则信息：")
    print(f"  - 规则ID: {rule.rule_id}")
    print(f"  - 规则名称: {rule.rule_name}")
    print(f"  - 是否启用: {rule.enabled}")
    print(f"\n提取选项：")
    print(f"  - 提取附件: {rule.should_extract_attachments()}")
    print(f"  - 提取正文: {rule.should_extract_body()}")
    print(f"  - 提取邮件头: {rule.should_extract_headers()}")
    print(f"  - 解压压缩文件: {rule.should_extract_archives()}")
    print(f"  - 压缩包密码: '{rule.get_archive_password()}'")
    print(f"  - 允许的格式: {rule.get_allowed_archive_types()}")

    # 验证方法返回值类型
    assert isinstance(rule.should_extract_attachments(), bool), "should_extract_attachments 应该返回布尔值"
    assert isinstance(rule.should_extract_body(), bool), "should_extract_body 应该返回布尔值"
    assert isinstance(rule.should_extract_archives(), bool), "should_extract_archives 应该返回布尔值"

    print("\n✅ 规则配置验证通过")

    # 测试 extract_options 字典
    print(f"\n原始 extract_options 字典：")
    print(f"  {rule.extract_options}")

    # 检查 extract_options 中是否有 extract_archives 字段
    if 'extract_archives' in rule.extract_options:
        print(f"\n✅ extract_archives 字段存在，值：{rule.extract_options['extract_archives']}")
    else:
        print(f"\n❌ extract_archives 字段不存在！")
        print(f"可用的字段：{list(rule.extract_options.keys())}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_rule_config()
