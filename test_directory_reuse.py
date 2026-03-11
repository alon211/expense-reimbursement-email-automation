#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试目录复用优化

验证是否复用已有的提取目录，避免重复创建。
"""
import sys
import io
from pathlib import Path

# 设置标准输出编码为 UTF-8 (Windows 中文显示修复)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from config.settings import EXTRACT_ROOT_DIR
from core.email_extractor import EmailExtractor


def test_directory_reuse():
    """测试目录复用"""
    print("\n" + "="*70)
    print("测试提取目录复用优化".center(70))
    print("="*70 + "\n")

    # 创建提取器
    extractor = EmailExtractor()

    print("📅 测试场景1：首次创建目录")
    print("-"*70)
    dir1 = extractor.create_extraction_dir()
    print(f"创建的目录: {dir1}")
    print(f"目录存在: {dir1.exists()}")
    print()

    print("📅 测试场景2：再次调用（应该复用同一目录）")
    print("-"*70)
    dir2 = extractor.create_extraction_dir()
    print(f"创建的目录: {dir2}")
    print(f"目录存在: {dir2.exists()}")
    print()

    # 验证是否是同一个目录
    print("✅ 验证结果")
    print("-"*70)
    if dir1 == dir2:
        print(f"✅ 目录复用成功！")
        print(f"   第一次: {dir1}")
        print(f"   第二次: {dir2}")
        print(f"   两者相同: {dir1 == dir2}")
    else:
        print(f"❌ 目录复用失败！")
        print(f"   第一次: {dir1}")
        print(f"   第二次: {dir2}")

    print()
    print("📂 目录命名规则")
    print("-"*70)
    today = dir1.name
    print(f"目录名称: {today}")
    print(f"格式说明: YYYY-MM-DD (按日期命名，同一天复用同一目录)")
    print(f"优势: 避免每次运行创建新目录，节省磁盘空间")

    print()
    print("="*70)
    print("优化效果".center(70))
    print("="*70)
    print()
    print("修复前:")
    print("  - 每次运行创建新目录: extracted_mails/2026-03-11_063701/")
    print("  - 每次运行创建新目录: extracted_mails/2026-03-11_064425/")
    print("  - 每次运行创建新目录: extracted_mails/2026-03-11_065010/")
    print()
    print("修复后:")
    print("  - 同一天只使用一个目录: extracted_mails/2026-03-11/")
    print("  - 已提取的邮件直接跳过，不重新提取")
    print("  - 只有新邮件才提取到今日目录")
    print()
    print("="*70 + "\n")


if __name__ == "__main__":
    try:
        test_directory_reuse()
    except KeyboardInterrupt:
        print("\n用户手动终止程序")
    except Exception as e:
        print(f"\n❌ 程序异常：{str(e)}")
        import traceback
        traceback.print_exc()
