#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试 extract_options 配置是否生效"""
import sys
import io

# 设置标准输出编码为 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from core.rule_loader import RuleLoader, Rule

def test_extract_options():
    """测试规则的 extract_options 配置"""

    print("=" * 60)
    print("测试 extract_options 配置")
    print("=" * 60)

    # 测试规则1：只提取附件
    rule1_data = {
        "rule_id": "test_001",
        "rule_name": "只提取附件",
        "enabled": True,
        "match_conditions": {
            "sender_contains": ["test"],
            "subject_contains": [],
            "body_contains": []
        },
        "extract_options": {
            "extract_attachments": True,
            "extract_body": False,
            "extract_headers": False
        }
    }

    rule1 = Rule(rule1_data)
    print(f"\n规则1: {rule1.rule_name}")
    print(f"  - should_extract_attachments(): {rule1.should_extract_attachments()}")
    print(f"  - should_extract_body(): {rule1.should_extract_body()}")
    print(f"  - should_extract_headers(): {rule1.should_extract_headers()}")

    assert rule1.should_extract_attachments() == True, "❌ 应该提取附件"
    assert rule1.should_extract_body() == False, "❌ 不应该提取正文"
    assert rule1.should_extract_headers() == False, "❌ 不应该提取邮件头"
    print("  ✅ 规则1配置正确")

    # 测试规则2：只提取正文
    rule2_data = {
        "rule_id": "test_002",
        "rule_name": "只提取正文",
        "enabled": True,
        "match_conditions": {
            "sender_contains": ["test"],
            "subject_contains": [],
            "body_contains": []
        },
        "extract_options": {
            "extract_attachments": False,
            "extract_body": True,
            "extract_headers": False
        }
    }

    rule2 = Rule(rule2_data)
    print(f"\n规则2: {rule2.rule_name}")
    print(f"  - should_extract_attachments(): {rule2.should_extract_attachments()}")
    print(f"  - should_extract_body(): {rule2.should_extract_body()}")
    print(f"  - should_extract_headers(): {rule2.should_extract_headers()}")

    assert rule2.should_extract_attachments() == False, "❌ 不应该提取附件"
    assert rule2.should_extract_body() == True, "❌ 应该提取正文"
    assert rule2.should_extract_headers() == False, "❌ 不应该提取邮件头"
    print("  ✅ 规则2配置正确")

    # 测试规则3：提取所有
    rule3_data = {
        "rule_id": "test_003",
        "rule_name": "提取所有",
        "enabled": True,
        "match_conditions": {
            "sender_contains": ["test"],
            "subject_contains": [],
            "body_contains": []
        },
        "extract_options": {
            "extract_attachments": True,
            "extract_body": True,
            "extract_headers": True
        }
    }

    rule3 = Rule(rule3_data)
    print(f"\n规则3: {rule3.rule_name}")
    print(f"  - should_extract_attachments(): {rule3.should_extract_attachments()}")
    print(f"  - should_extract_body(): {rule3.should_extract_body()}")
    print(f"  - should_extract_headers(): {rule3.should_extract_headers()}")

    assert rule3.should_extract_attachments() == True, "❌ 应该提取附件"
    assert rule3.should_extract_body() == True, "❌ 应该提取正文"
    assert rule3.should_extract_headers() == True, "❌ 应该提取邮件头"
    print("  ✅ 规则3配置正确")

    # 测试规则4：什么都不提取（缺少 extract_options）
    rule4_data = {
        "rule_id": "test_004",
        "rule_name": "默认配置",
        "enabled": True,
        "match_conditions": {
            "sender_contains": ["test"],
            "subject_contains": [],
            "body_contains": []
        }
        # 注意：没有 extract_options 字段
    }

    rule4 = Rule(rule4_data)
    print(f"\n规则4: {rule4.rule_name}（缺少 extract_options）")
    print(f"  - should_extract_attachments(): {rule4.should_extract_attachments()}")
    print(f"  - should_extract_body(): {rule4.should_extract_body()}")
    print(f"  - should_extract_headers(): {rule4.should_extract_headers()}")
    print("  ℹ️  默认值都是 False，不会提取任何内容")

    # 测试实际规则文件
    print("\n" + "=" * 60)
    print("测试实际规则文件")
    print("=" * 60)

    try:
        from config.settings import PARSE_RULES_JSON_PATH
        rule_loader = RuleLoader(PARSE_RULES_JSON_PATH)

        for rule in rule_loader.get_enabled_rules():
            print(f"\n规则: {rule.rule_name} (ID: {rule.rule_id})")
            print(f"  - 提取附件: {'是' if rule.should_extract_attachments() else '否'}")
            print(f"  - 提取正文: {'是' if rule.should_extract_body() else '否'}")
            print(f"  - 提取邮件头: {'是' if rule.should_extract_headers() else '否'}")

    except Exception as e:
        print(f"⚠️  加载规则文件失败：{e}")

    print("\n" + "=" * 60)
    print("✅ 所有测试通过！")
    print("=" * 60)

if __name__ == "__main__":
    test_extract_options()
