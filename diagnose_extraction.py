# -*- coding: utf-8 -*-
"""诊断extract_email_full函数问题"""
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
from pathlib import Path

print("=" * 60)
print("🔍 诊断extract_email_full函数")
print("=" * 60)

# 1. 加载规则
print("\n1️⃣ 加载规则...")
try:
    rule_loader = RuleLoader("rules/parse_rules.json")
    print(f"✅ 规则加载成功")
    print(f"   规则数量：{len(rule_loader.rules)}")
    print(f"   启用规则：{len(rule_loader.get_enabled_rules())}")
except Exception as e:
    print(f"❌ 规则加载失败：{e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 2. 找到rule_003
print("\n2️⃣ 查找rule_003...")
rule_003 = None
for rule in rule_loader.rules:
    if rule.rule_id == "rule_003":
        rule_003 = rule
        break

if not rule_003:
    print("❌ 未找到rule_003")
    sys.exit(1)

print(f"✅ 找到rule_003：{rule_003.rule_name}")

# 3. 检查规则方法
print("\n3️⃣ 检查规则方法...")
print(f"   should_extract_body(): {rule_003.should_extract_body()}")
print(f"   hasattr(should_extract_nuonuo_invoice): {hasattr(rule_003, 'should_extract_nuonuo_invoice')}")

if hasattr(rule_003, 'should_extract_nuonuo_invoice'):
    result = rule_003.should_extract_nuonuo_invoice()
    print(f"   should_extract_nuonuo_invoice(): {result}")
else:
    print("   ❌ 没有should_extract_nuonuo_invoice方法")

# 4. 读取HTML文件
print("\n4️⃣ 读取HTML文件...")
html_file = Path("extracted_mails/2026-03-11_191854/bodies/rule_003/280bace957d1.html")
if not html_file.exists():
    print(f"❌ HTML文件不存在：{html_file}")
    # 尝试找到任何存在的HTML文件
    print("尝试查找其他HTML文件...")
    base_dir = Path("extracted_mails")
    if base_dir.exists():
        for time_dir in sorted(base_dir.iterdir(), reverse=True):
            bodies_dir = time_dir / "bodies" / "rule_003"
            if bodies_dir.exists():
                html_files = list(bodies_dir.glob("*.html"))
                if html_files:
                    html_file = html_files[0]
                    print(f"✅ 找到HTML文件：{html_file}")
                    break
    if not html_file.exists():
        sys.exit(1)

html_content = html_file.read_text(encoding='utf-8')
print(f"✅ HTML文件读取成功，大小：{len(html_content)} 字节")

# 5. 构造mail_data
print("\n5️⃣ 构造mail_data...")
mail_data = {
    'message_id': '<280bace957d7@example.com>',
    'subject': '您收到一张【苏州恒泰酒店管理有限公司】开具的发票',
    'sender': '诺诺网',
    'date': '2026-03-11 16:16:40',
    'matched_rules': [rule_003]
}

# 6. 创建提取目录
print("\n6️⃣ 创建提取目录...")
extraction_dir = Path("test_diagnose")
extraction_dir.mkdir(exist_ok=True)
print(f"✅ 提取目录：{extraction_dir}")

# 7. 构造一个简单的邮件对象
print("\n7️⃣ 构造邮件对象...")
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

msg = MIMEMultipart()
msg['Message-ID'] = mail_data['message_id']
msg['Subject'] = mail_data['subject']
msg['From'] = mail_data['sender']

# 添加一个简单的HTML body
html_payload = MIMEText("""
<html>
<body>
<span style="flex-shrink:0;color:#555;">点击链接查看发票：</span>
<a style="text-decoration: underline;color: #007AFF;" href="https://nnfp.jss.com.cn/6CHzJjzxJq-16Q3d">https://nnfp.jss.com.cn/6CHzJjzxJq-16Q3d</a>
</body>
</html>
""", 'html')
msg.attach(html_payload)

print(f"✅ 邮件对象创建成功")

# 8. 调用extract_email_full（带异常捕获）
print("\n8️⃣ 调用extract_email_full...")
print("-" * 60)

try:
    result = extract_email_full(msg, mail_data, extraction_dir)
    print("-" * 60)
    print("\n✅ extract_email_full执行完成")
    print(f"   storage_path: {result.get('storage_path')}")
    print(f"   body_file_path: {result.get('body_file_path')}")
    print(f"   attachment_count: {result.get('attachment_count')}")
    print(f"   pdf_count: {result.get('pdf_count', 'N/A')}")
    print(f"   pdf_paths: {result.get('pdf_paths', 'N/A')}")

    # 检查PDF文件
    pdf_dir = extraction_dir / "nuonuo_invoices" / "rule_003"
    if pdf_dir.exists():
        pdf_files = list(pdf_dir.glob("*.pdf"))
        print(f"\n📁 PDF目录：{pdf_dir}")
        print(f"   PDF文件数量：{len(pdf_files)}")
        for pdf_file in pdf_files:
            print(f"   - {pdf_file.name} ({pdf_file.stat().st_size} 字节)")
    else:
        print(f"\n❌ PDF目录不存在：{pdf_dir}")

except Exception as e:
    print("-" * 60)
    print(f"\n❌ extract_email_full执行失败：{e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
