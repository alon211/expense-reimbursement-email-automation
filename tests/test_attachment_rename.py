# -*- coding: utf-8 -*-
"""
测试附件重命名功能
"""
import sys
import io
import tempfile
from pathlib import Path

# 设置标准输出编码为 UTF-8 (Windows 中文显示修复)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.email_extractor import EmailExtractor


def test_unique_filename_generation():
    """测试唯一文件名生成"""
    extractor = EmailExtractor()

    # 创建临时目录
    with tempfile.TemporaryDirectory() as test_dir:
        test_path = Path(test_dir)

        # 场景1: 文件不存在，使用原文件名
        result1 = extractor._get_unique_filename(test_path, "invoice.pdf")
        assert result1 == test_path / "invoice.pdf"
        print("✅ 场景1通过: 文件不存在，使用原文件名")

        # 创建文件
        (test_path / "invoice.pdf").touch()

        # 场景2: 文件已存在，添加序号
        result2 = extractor._get_unique_filename(test_path, "invoice.pdf")
        assert result2 == test_path / "invoice_1.pdf"
        print("✅ 场景2通过: 文件已存在，重命名为 invoice_1.pdf")

        # 创建第二个文件
        (test_path / "invoice_1.pdf").touch()

        # 场景3: 继续递增
        result3 = extractor._get_unique_filename(test_path, "invoice.pdf")
        assert result3 == test_path / "invoice_2.pdf"
        print("✅ 场景3通过: 继续递增为 invoice_2.pdf")

        # 场景4: 不同文件名，不冲突
        result4 = extractor._get_unique_filename(test_path, "contract.pdf")
        assert result4 == test_path / "contract.pdf"
        print("✅ 场景4通过: 不同文件名不冲突")

        # 场景5: 连续创建多个同名文件
        (test_path / "invoice_2.pdf").touch()
        (test_path / "invoice_3.pdf").touch()
        result5 = extractor._get_unique_filename(test_path, "invoice.pdf")
        assert result5 == test_path / "invoice_4.pdf"
        print("✅ 场景5通过: 连续创建多个同名文件")

        # 场景6: 无扩展名文件
        (test_path / "README").touch()
        result6 = extractor._get_unique_filename(test_path, "README")
        assert result6 == test_path / "README_1"
        print("✅ 场景6通过: 无扩展名文件重命名")

        # 场景7: 多个扩展名
        (test_path / "file.tar.gz").touch()
        result7 = extractor._get_unique_filename(test_path, "file.tar.gz")
        assert result7 == test_path / "file.tar_1.gz"
        print("✅ 场景7通过: 多个扩展名文件重命名")

    print("\n✅ 所有测试通过！")


def test_edge_cases():
    """测试边界情况"""
    extractor = EmailExtractor()

    with tempfile.TemporaryDirectory() as test_dir:
        test_path = Path(test_dir)

        # 场景1: 中文文件名
        result1 = extractor._get_unique_filename(test_path, "发票.pdf")
        assert result1 == test_path / "发票.pdf"
        (test_path / "发票.pdf").touch()
        result2 = extractor._get_unique_filename(test_path, "发票.pdf")
        assert result2 == test_path / "发票_1.pdf"
        print("✅ 边界测试1: 中文文件名支持")

        # 场景2: 特殊字符文件名
        result3 = extractor._get_unique_filename(test_path, "file(1).pdf")
        assert result3 == test_path / "file(1).pdf"
        (test_path / "file(1).pdf").touch()
        result4 = extractor._get_unique_filename(test_path, "file(1).pdf")
        assert result4 == test_path / "file(1)_1.pdf"
        print("✅ 边界测试2: 特殊字符文件名支持")

        # 场景3: 空目录测试
        result5 = extractor._get_unique_filename(test_path, "newfile.txt")
        assert result5 == test_path / "newfile.txt"
        print("✅ 边界测试3: 空目录文件创建")

    print("\n✅ 所有边界测试通过！")


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 开始附件重命名功能测试")
    print("=" * 60)
    print()

    test_unique_filename_generation()
    print()
    test_edge_cases()

    print()
    print("=" * 60)
    print("🎉 全部测试完成！")
    print("=" * 60)
