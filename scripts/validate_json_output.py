#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证 JSON 输出格式
检查 GitHub Actions 输出是否符合要求
"""
import sys
import json
import subprocess
from pathlib import Path


def validate_json_format(text: str) -> bool:
    """验证文本是否为有效 JSON"""
    try:
        json.loads(text)
        return True
    except json.JSONDecodeError as e:
        print(f"❌ JSON 格式错误: {e}")
        return False


def test_github_output_format():
    """测试 GitHub Actions 输出格式"""
    # 测试数据
    test_result = {
        "success": True,
        "matched_count": 0,
        "executed_at": "2026-03-11T13:43:15.444426",
        "time_range_days": 7
    }

    result_str = json.dumps(test_result, ensure_ascii=False, indent=2)

    print("=== 测试 1: 直接输出格式（错误）===")
    print(f"summary={result_str}")
    print("❌ 问题：多行、包含特殊字符")
    print("    GitHub Actions 无法解析\n")

    print("=== 测试 2: Heredoc 格式（正确但复杂）===")
    print(f"summary<<EOF")
    print(result_str)
    print("EOF")
    print("✅ 正确：支持多行 JSON")
    print("⚠️  缺点：语法复杂，容易出错\n")

    print("=== 测试 3: 文件路径格式（推荐）===")
    print(f"summary_file=/tmp/extraction_summary.json")
    print("✅ 推荐：最可靠，无格式问题")
    print("✅ 优点：支持任意大小的 JSON\n")


def check_jq_installed():
    """检查 jq 是否安装"""
    try:
        result = subprocess.run(["jq", "--version"], capture_output=True, check=True)
        print(f"✅ jq 已安装: {result.stdout.decode().strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  jq 未安装，请安装：")
        print("   Windows: choco install jq")
        print("   macOS: brew install jq")
        print("   Linux: sudo apt-get install jq")
        return False


def test_json_file_output():
    """测试文件输出方案"""
    print("=== 测试 4: 文件输出方案验证 ===")

    # 创建临时目录
    temp_dir = Path("/tmp") if sys.platform != "win32" else Path("C:/temp")
    temp_dir.mkdir(parents=True, exist_ok=True)

    # 测试数据
    test_data = {
        "success": True,
        "matched_count": 2,
        "mails": [
            {"subject": "测试邮件1", "sender": "test1@example.com"},
            {"subject": "测试邮件2", "sender": "test2@example.com"}
        ]
    }

    # 写入文件
    test_file = temp_dir / "test_output.json"
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)

    print(f"✅ 测试文件创建成功: {test_file}")

    # 读取并验证
    with open(test_file, 'r', encoding='utf-8') as f:
        loaded_data = json.load(f)

    if loaded_data == test_data:
        print("✅ 文件读写验证通过")
    else:
        print("❌ 文件读写验证失败")

    # 清理
    test_file.unlink()
    print(f"✅ 临时文件已清理\n")


def main():
    # 设置标准输出编码为 UTF-8 (Windows 中文显示修复)
    import io
    import sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("🔍 GitHub Actions 输出格式验证工具")
    print("=" * 50)
    print()

    # 检查 jq
    jq_available = check_jq_installed()
    print()

    # 测试格式
    test_github_output_format()

    # 测试文件输出
    test_json_file_output()

    print("=" * 50)
    print("\n=== 建议 ===")
    print("1. ✅ 使用文件路径格式（最可靠）")
    print("2. ⚠️  如果需要直接输出，使用 Heredoc 格式")
    print("3. ❌ 绝不要直接将多行 JSON 写入 $GITHUB_OUTPUT")
    print("4. ✅ 所有复杂输出都应该先写入文件")
    print()
    print("=== 修复方案 ===")
    print("echo \"$RESULT\" > /tmp/extraction_result.json")
    print("echo \"detail_file=/tmp/extraction_result.json\" >> $GITHUB_OUTPUT")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
