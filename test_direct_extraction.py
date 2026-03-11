# -*- coding: utf-8 -*-
"""直接测试extract_email_full函数"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

# 导入必要的模块
from core.rule_loader import RuleLoader
from core.email_extractor import extract_email_full
import email
from email import policy
from pathlib import Path as PathLib

print("=" * 60)
print("🧪 直接测试extract_email_full函数")
print("=" * 60)

# 1. 加载规则
print("\n1️⃣ 加载规则...")
rule_loader = RuleLoader("rules/parse_rules.json")
print(f"✅ 加载了 {len(rule_loader.get_enabled_rules())} 条规则")

# 2. 找到rule_003
rule_003 = None
for rule in rule_loader.rules:
    if rule.rule_id == "rule_003":
        rule_003 = rule
        break

if not rule_003:
    print("❌ 未找到rule_003")
    sys.exit(1)

print(f"✅ 规则：{rule_003.rule_name}")
print(f"   extract_nuonuo_invoice: {rule_003.extract_options.get('extract_nuonuo_invoice')}")

# 3. 读取一个真实的邮件文件
eml_file = Path("extracted_mails/2026-03-11_161640/bodies/rule_003/280bace957d1.html")
if not eml_file.exists():
    print(f"❌ 测试文件不存在：{eml_file}")
    sys.exit(1)

print(f"\n2️⃣ 读取HTML文件：{eml_file}")

# 4. 构造mail_data
print("\n3️⃣ 构造mail_data...")
mail_data = {
    'message_id': '<test@example.com>',
    'subject': '您收到一张【苏州恒泰酒店管理有限公司】开具的发票',
    'sender': '诺诺网',
    'date': '2026-03-11 16:16:40',
    'matched_rules': [rule_003]
}

# 5. 创建测试目录
extraction_dir = PathLib("test_extraction")
extraction_dir.mkdir(exist_ok=True)

# 6. 创建一个测试邮件对象
print("\n4️⃣ 创建测试邮件对象...")
msg = email.message.Message()
msg['Message-ID'] = mail_data['message_id']
msg['Subject'] = mail_data['subject']
msg['From'] = mail_data['sender']

# 7. 调用extract_email_full
print("\n5️⃣ 调用extract_email_full...")
try:
    result = extract_email_full(msg, mail_data, extraction_dir)
    print("\n✅ 提取完成！")
    print(f"   storage_path: {result.get('storage_path')}")
    print(f"   body_file_path: {result.get('body_file_path')}")
    print(f"   pdf_count: {result.get('pdf_count')}")
    print(f"   pdf_paths: {result.get('pdf_paths')}")
except Exception as e:
    print(f"\n❌ 提取失败：{e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
