#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理临时文件脚本
用于GitHub Actions环境
"""
import sys
import argparse
import shutil
from pathlib import Path


def cleanup_temp_dirs(temp_dir: Path, keep_output: bool = False):
    """
    清理临时目录

    Args:
        temp_dir: 临时目录路径
        keep_output: 是否保留输出目录
    """
    if not temp_dir.exists():
        print(f"⚠️  临时目录不存在：{temp_dir}")
        return

    print(f"🧹 开始清理临时目录：{temp_dir}")

    # 清理子目录
    cleaned_count = 0
    for subdir in ["bodies", "attachments", "extracted", "nuonuo_invoices"]:
        subdir_path = temp_dir / subdir
        if subdir_path.exists():
            try:
                shutil.rmtree(subdir_path)
                print(f"✅ 已清理：{subdir_path}")
                cleaned_count += 1
            except Exception as e:
                print(f"❌ 清理失败：{subdir_path}，错误：{e}")

    # 清理数据库
    db_file = temp_dir / "data.db"
    if db_file.exists():
        try:
            db_file.unlink()
            print(f"✅ 已清理：{db_file}")
            cleaned_count += 1
        except Exception as e:
            print(f"❌ 清理失败：{db_file}，错误：{e}")

    if not keep_output:
        # 清理整个临时目录
        try:
            shutil.rmtree(temp_dir)
            print(f"✅ 已清空临时目录：{temp_dir}")
        except Exception as e:
            print(f"❌ 清空目录失败：{temp_dir}，错误：{e}")
    else:
        print(f"⏸️  保留输出目录：{temp_dir}")

    print(f"\n📊 清理统计：共清理 {cleaned_count} 项")


def main():
    parser = argparse.ArgumentParser(description='清理临时文件')
    parser.add_argument('--temp-dir', default='/tmp/extraction_temp', help='临时目录路径')
    parser.add_argument('--keep-output', action='store_true', help='保留输出目录')

    args = parser.parse_args()

    temp_dir = Path(args.temp_dir)
    cleanup_temp_dirs(temp_dir, args.keep_output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
