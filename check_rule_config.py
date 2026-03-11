# -*- coding: utf-8 -*-
"""检查规则配置是否正确加载"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.rule_loader import RuleLoader

print("=" * 60)
print("🔍 检查规则配置")
print("=" * 60)

# 加载规则
loader = RuleLoader("rules/parse_rules.json")

# 检查rule_003
rule_003 = None
for rule in loader.rules:
    if rule.rule_id == "rule_003":
        rule_003 = rule
        break

if not rule_003:
    print("❌ 未找到rule_003")
    sys.exit(1)

print(f"✅ 找到规则：{rule_003.rule_name}")
print(f"   是否启用：{rule_003.enabled}")
print()

# 检查extract_options
print("📋 extract_options:")
for key, value in rule_003.extract_options.items():
    print(f"   - {key}: {value}")
print()

# 检查诺诺网发票提取方法
print("🔍 检查诺诺网发票提取方法:")
print(f"   hasattr(rule_003, 'should_extract_nuonuo_invoice'): {hasattr(rule_003, 'should_extract_nuonuo_invoice')}")

if hasattr(rule_003, 'should_extract_nuonuo_invoice'):
    should_extract = rule_003.should_extract_nuonuo_invoice()
    print(f"   should_extract_nuonuo_invoice(): {should_extract}")
else:
    print(f"   ❌ 规则对象没有should_extract_nuonuo_invoice方法")

print()

# 测试其他方法
if hasattr(rule_003, 'get_nuonuo_anchor_text'):
    anchor_text = rule_003.get_nuonuo_anchor_text()
    print(f"   get_nuonuo_anchor_text(): '{anchor_text}'")

if hasattr(rule_003, 'get_nuonuo_download_options'):
    options = rule_003.get_nuonuo_download_options()
    print(f"   get_nuonuo_download_options(): {options}")

print()
print("=" * 60)
