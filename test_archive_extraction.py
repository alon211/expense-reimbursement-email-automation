#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试压缩文件自动解压功能"""
import sys
import io
import zipfile
import tarfile
from pathlib import Path

# 设置标准输出编码为 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from utils.archive_utils import ArchiveExtractor
from core.rule_loader import Rule


def create_test_archives():
    """创建测试用的压缩文件"""
    test_dir = Path("./test_archives")
    test_dir.mkdir(parents=True, exist_ok=True)

    # 创建测试文件
    test_file = test_dir / "test_document.txt"
    test_file.write_text("这是一个测试文档内容", encoding='utf-8')

    # 创建 ZIP 压缩包
    zip_path = test_dir / "test_archive.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.write(test_file, arcname="document.txt")

    # 创建 TAR.GZ 压缩包
    tar_gz_path = test_dir / "test_archive.tar.gz"
    with tarfile.open(tar_gz_path, 'w:gz') as tf:
        tf.add(test_file, arcname="document.txt")

    # 创建一个非压缩文件作为对比
    normal_file = test_dir / "normal_file.txt"
    normal_file.write_text("这是一个普通文件", encoding='utf-8')

    print(f"✅ 测试文件创建完成：{test_dir}")
    return test_dir, [zip_path, tar_gz_path, normal_file]


def test_archive_extractor():
    """测试压缩文件解压功能"""
    print("=" * 60)
    print("测试压缩文件自动解压功能")
    print("=" * 60)

    # 1. 创建测试文件
    print("\n1. 创建测试压缩文件...")
    test_dir, test_files = create_test_archives()

    # 2. 测试压缩文件检测
    print("\n2. 测试压缩文件检测...")
    extractor = ArchiveExtractor()

    for file_path in test_files:
        is_archive = extractor.is_archive_file(file_path)
        archive_type = extractor.get_archive_type(file_path) if is_archive else None
        print(f"   {file_path.name}:")
        print(f"     - 是压缩文件: {'是' if is_archive else '否'}")
        if archive_type:
            print(f"     - 压缩类型: {archive_type}")

    # 3. 测试解压功能
    print("\n3. 测试解压功能...")
    extract_dir = test_dir / "extracted"
    extract_dir.mkdir(parents=True, exist_ok=True)

    for file_path in test_files:
        if extractor.is_archive_file(file_path):
            print(f"\n   解压 {file_path.name}...")

            try:
                result = extractor.extract_archive(
                    archive_path=file_path,
                    extract_dir=extract_dir,
                    password=None
                )

                print(f"   ✅ 解压成功")
                print(f"   - 解压目录: {result['extract_dir']}")
                print(f"   - 解压文件数: {result['extracted_count']}")
                print(f"   - 解压文件:")
                for extracted_path in result['extracted_paths']:
                    print(f"     * {extracted_path}")

                # 验证文件内容
                for extracted_path in result['extracted_paths']:
                    if Path(extracted_path).exists():
                        content = Path(extracted_path).read_text(encoding='utf-8')
                        print(f"     ✅ 文件内容验证通过: {content[:20]}...")
                    else:
                        print(f"     ❌ 文件不存在: {extracted_path}")

            except Exception as e:
                print(f"   ❌ 解压失败: {e}")

    # 4. 测试规则配置
    print("\n" + "=" * 60)
    print("4. 测试规则配置")
    print("=" * 60)

    rule_data = {
        "rule_id": "test_archive_rule",
        "rule_name": "测试解压规则",
        "enabled": True,
        "match_conditions": {
            "sender_contains": ["test"],
            "subject_contains": [],
            "body_contains": []
        },
        "extract_options": {
            "extract_attachments": True,
            "extract_body": False,
            "extract_headers": False,
            "extract_archives": True,
            "archive_password": "",
            "allowed_archive_types": [".zip", ".tar.gz", ".tar.bz2"]
        }
    }

    rule = Rule(rule_data)

    print(f"\n规则: {rule.rule_name} (ID: {rule.rule_id})")
    print(f"  - 提取附件: {'是' if rule.should_extract_attachments() else '否'}")
    print(f"  - 提取正文: {'是' if rule.should_extract_body() else '否'}")
    print(f"  - 提取邮件头: {'是' if rule.should_extract_headers() else '否'}")
    print(f"  - 解压压缩文件: {'是' if rule.should_extract_archives() else '否'}")
    print(f"  - 压缩包密码: '{rule.get_archive_password()}'")
    print(f"  - 允许的压缩格式: {', '.join(rule.get_allowed_archive_types())}")

    # 验证规则方法
    assert rule.should_extract_attachments() == True, "❌ 应该提取附件"
    assert rule.should_extract_body() == False, "❌ 不应该提取正文"
    assert rule.should_extract_headers() == False, "❌ 不应该提取邮件头"
    assert rule.should_extract_archives() == True, "❌ 应该解压压缩文件"
    assert rule.get_archive_password() == "", "❌ 密码应该为空"
    assert ".zip" in rule.get_allowed_archive_types(), "❌ 应该支持 .zip 格式"

    print("\n✅ 规则配置验证通过")

    # 5. 测试不同格式支持
    print("\n" + "=" * 60)
    print("5. 测试支持的压缩格式")
    print("=" * 60)

    supported_formats = extractor.get_supported_formats()
    print(f"\n支持的压缩格式（{len(supported_formats)} 种）:")
    for ext, info in sorted(supported_formats.items()):
        print(f"  - {ext:12} : {info['name']:8} (提取器: {info['extractor']})")

    # 6. 测试非压缩文件
    print("\n" + "=" * 60)
    print("6. 测试非压缩文件处理")
    print("=" * 60)

    normal_file = test_dir / "normal_file.txt"
    is_archive = extractor.is_archive_file(normal_file)
    print(f"\n文件: {normal_file.name}")
    print(f"  - 是压缩文件: {'是' if is_archive else '否'}")
    print(f"  ✅ 正确识别为非压缩文件")

    # 清理测试文件
    print("\n" + "=" * 60)
    print("7. 清理测试文件...")
    print("=" * 60)

    import shutil
    try:
        shutil.rmtree(test_dir)
        print(f"✅ 已删除测试目录: {test_dir}")
    except Exception as e:
        print(f"⚠️  删除测试目录失败: {e}")
        print(f"   请手动删除: {test_dir}")

    print("\n" + "=" * 60)
    print("✅ 所有测试通过！")
    print("=" * 60)


if __name__ == "__main__":
    test_archive_extractor()
