# -*- coding: utf-8 -*-
"""
测试诺诺网发票解析功能
"""
import sys
import io
from pathlib import Path

# 设置标准输出编码为 UTF-8 (Windows 中文显示修复)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.nuonuo_invoice_parser import NuonuoInvoiceParser

def test_extract_invoice_link():
    """测试提取发票链接"""
    print("=" * 60)
    print("🧪 测试1: 从HTML中提取发票链接")
    print("=" * 60)

    # 检查测试文件是否存在
    html_file = Path("extracted_mails/2026-03-11_161640/bodies/rule_003/280bace957d1.html")
    if not html_file.exists():
        print(f"❌ 测试文件不存在：{html_file}")
        print("请确保已运行邮件提取并生成了该HTML文件")
        return False

    # 读取HTML文件
    html_content = html_file.read_text(encoding='utf-8')
    print(f"✅ 成功读取HTML文件：{html_file}")
    print(f"   文件大小：{len(html_content)} 字节")
    print()

    # 创建解析器
    parser = NuonuoInvoiceParser()

    # 测试提取发票链接
    print("🔍 开始提取发票链接...")
    invoice_link = parser.extract_invoice_link(html_content)

    if invoice_link:
        print(f"✅ 成功找到发票链接：{invoice_link}")
        print()
        return invoice_link
    else:
        print("❌ 未找到发票链接")
        print()
        return None

def test_get_pdf_download_url(invoice_link: str):
    """测试获取PDF下载链接"""
    if not invoice_link:
        print("⏭️  跳过测试2（没有发票链接）")
        return None

    print("=" * 60)
    print("🧪 测试2: 获取PDF下载链接")
    print("=" * 60)

    parser = NuonuoInvoiceParser()

    print("🔍 开始获取PDF下载链接...")
    pdf_url = parser.get_pdf_download_url(invoice_link)

    if pdf_url:
        print(f"✅ 成功获取PDF下载链接：{pdf_url}")
        print()
        return pdf_url
    else:
        print("❌ 获取PDF下载链接失败")
        print()
        return None

def test_download_invoice_pdf(invoice_link: str):
    """测试下载PDF文件"""
    if not invoice_link:
        print("⏭️  跳过测试3（没有发票链接）")
        return False

    print("=" * 60)
    print("🧪 测试3: 下载PDF文件")
    print("=" * 60)

    parser = NuonuoInvoiceParser()
    save_path = Path("test_invoice.pdf")

    # 删除旧的测试文件
    if save_path.exists():
        save_path.unlink()

    print(f"🔍 开始下载PDF到：{save_path}")
    success = parser.download_invoice_pdf(invoice_link, save_path)

    if success:
        print(f"✅ PDF下载成功")
        print(f"   文件路径：{save_path.absolute()}")
        print(f"   文件大小：{save_path.stat().st_size} 字节")
        print()

        # 清理测试文件
        if save_path.exists():
            save_path.unlink()
            print(f"🧹 已清理测试文件")
        print()

        return True
    else:
        print("❌ PDF下载失败")
        print()
        return False

def main():
    """主测试函数"""
    print()
    print("🚀 诺诺网发票解析功能测试")
    print()

    # 测试1: 提取发票链接
    invoice_link = test_extract_invoice_link()

    # 测试2: 获取PDF下载链接
    pdf_url = test_get_pdf_download_url(invoice_link)

    # 测试3: 下载PDF文件
    # success = test_download_invoice_pdf(invoice_link)

    # 总结
    print("=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    if invoice_link:
        print("✅ 测试1通过：成功提取发票链接")
    else:
        print("❌ 测试1失败：无法提取发票链接")

    if pdf_url:
        print("✅ 测试2通过：成功获取PDF下载链接")
    else:
        print("❌ 测试2失败：无法获取PDF下载链接")

    # if success:
    #     print("✅ 测试3通过：成功下载PDF文件")
    # else:
    #     print("❌ 测试3失败：无法下载PDF文件")

    print()
    print("🎉 测试完成！")
    print()

if __name__ == "__main__":
    main()
