# -*- coding: utf-8 -*-
"""临时测试规则 - 匹配当前邮箱中的邮件

使用方法：
1. 运行此脚本查看规则是否匹配
2. 如果匹配成功，可以手动添加到 parse_rules.json
"""
import json
from pathlib import Path

# 临时测试规则 - 匹配 GitHub 邮件
test_rule = {
    "rule_id": "test_github",
    "rule_name": "GitHub邮件测试",
    "enabled": True,
    "description": "测试规则 - 匹配GitHub通知邮件",
    "match_conditions": {
        "sender_contains": ["github"],
        "subject_contains": [],
        "body_contains": []
    },
    "extract_options": {
        "extract_attachments": False,
        "extract_body": False,
        "extract_headers": False
    },
    "output_subdir": "test"
}

# 临时测试规则 - 匹配招商银行
test_rule_2 = {
    "rule_id": "test_cmb",
    "rule_name": "招商银行测试",
    "enabled": True,
    "description": "测试规则 - 匹配招商银行邮件",
    "match_conditions": {
        "sender_contains": ["招商银行"],
        "subject_contains": [],
        "body_contains": []
    },
    "extract_options": {
        "extract_attachments": False,
        "extract_body": False,
        "extract_headers": False
    },
    "output_subdir": "test"
}

print("=" * 60)
print("临时测试规则")
print("=" * 60)
print("\n要测试数据库功能，请临时添加以下规则到 parse_rules.json：\n")
print(json.dumps(test_rule, indent=2, ensure_ascii=False))
print("\n或：\n")
print(json.dumps(test_rule_2, indent=2, ensure_ascii=False))
print("\n" + "=" * 60)
print("操作步骤：")
print("1. 打开 rules/parse_rules.json")
print("2. 在 rules 数组中添加上述测试规则")
print("3. 运行 python main.py")
print("4. 查看 extracted_mails/data.db 是否有记录")
print("5. 测试完成后删除测试规则")
print("=" * 60)
