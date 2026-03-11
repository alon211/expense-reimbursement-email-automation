#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
打包提取结果
用于上传到GitHub Artifacts
"""
import sys
import argparse
import shutil
import json
from pathlib import Path
from datetime import datetime


def package_results(source_dir: Path, output_base_dir: Path) -> Path:
    """
    打包提取结果

    Args:
        source_dir: 源目录（临时提取目录）
        output_base_dir: 输出基础目录

    Returns:
        Path: 输出目录路径
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    output_dir = output_base_dir / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"📦 开始打包提取结果...")
    print(f"📂 源目录: {source_dir}")
    print(f"📂 输出目录: {output_dir}")

    if not source_dir.exists():
        print(f"⚠️  源目录不存在：{source_dir}")
        # 创建空的输出目录
        return output_dir

    # 复制文件
    copied_count = 0
    for category in ["bodies", "attachments", "extracted", "nuonuo_invoices"]:
        src = source_dir / category
        if src.exists():
            dst = output_dir / category
            try:
                shutil.copytree(src, dst)
                file_count = len(list(dst.rglob("*")))
                print(f"✅ 已复制：{category} ({file_count} 个文件)")
                copied_count += 1
            except Exception as e:
                print(f"❌ 复制失败：{category}，错误：{e}")

    # 统计文件数量
    total_files = sum(len(list(output_dir.rglob("*"))) for _ in [0]) - 1  # 减1排除目录本身

    # 生成摘要
    summary = {
        "timestamp": timestamp,
        "total_files": total_files,
        "categories_copied": copied_count,
        "categories": []
    }

    for category in ["bodies", "attachments", "extracted", "nuonuo_invoices"]:
        cat_dir = output_dir / category
        if cat_dir.exists():
            file_count = len(list(cat_dir.rglob("*")))
            summary["categories"].append({
                "name": category,
                "file_count": file_count
            })

    summary_file = output_dir / "summary.json"
    try:
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        print(f"✅ 已生成摘要：{summary_file}")
    except Exception as e:
        print(f"❌ 生成摘要失败：{e}")

    print(f"\n📊 打包统计：")
    print(f"   - 总文件数: {total_files}")
    print(f"   - 复制类别: {copied_count}/4")
    print(f"   - 输出目录: {output_dir}")

    return output_dir


def main():
    parser = argparse.ArgumentParser(description='打包提取结果')
    parser.add_argument('--source-dir', required=True, help='源目录路径')
    parser.add_argument('--output-dir', default='/tmp/extraction_output', help='输出目录路径')

    args = parser.parse_args()

    source_dir = Path(args.source_dir)
    output_base_dir = Path(args.output_dir)

    # 确保输出基础目录存在
    output_base_dir.mkdir(parents=True, exist_ok=True)

    output_dir = package_results(source_dir, output_base_dir)

    return 0


if __name__ == "__main__":
    sys.exit(main())
