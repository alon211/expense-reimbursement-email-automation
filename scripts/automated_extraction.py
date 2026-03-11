#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化邮件提取并处理结果
完整流程：触发 → 等待 → 下载 → 解压 → 处理
"""
import os
import sys
import json
import zipfile
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.github_client import GitHubWorkflowClient


def automated_extraction(
    repo: str,
    token: str,
    time_range_days: int = 20,
    download_dir: str = "./downloads",
    extract: bool = True,
    list_files: bool = True
):
    """
    自动化提取流程

    Args:
        repo: GitHub仓库（username/repo）
        token: GitHub Personal Access Token
        time_range_days: 搜索时间范围（天）
        download_dir: 下载目录
        extract: 是否解压ZIP文件
        list_files: 是否列出文件清单

    Returns:
        dict: 提取结果信息
    """
    result = {
        "success": False,
        "run_id": None,
        "matched_count": 0,
        "download_path": None,
        "error": None
    }

    try:
        # 1. 创建客户端
        client = GitHubWorkflowClient(token=token, repo=repo)

        print("🚀 触发邮件提取...")
        print(f"📂 仓库: {repo}")
        print(f"⏱️  时间范围: {time_range_days} 天")

        # 2. 触发workflow
        run_id = client.trigger_workflow(
            workflow_file="email-extraction.yml",
            inputs={"time_range_days": str(time_range_days)}
        )

        result["run_id"] = run_id

        print(f"\n✅ Workflow已触发")
        print(f"📌 Run ID: {run_id}")
        print(f"🔗 查看详情: https://github.com/{repo}/actions/runs/{run_id}")

        # 3. 等待完成
        print(f"\n⏳ 等待执行完成（最长10分钟）...")
        outputs = client.get_workflow_outputs(run_id, timeout=600)

        # 4. 解析结果
        summary = json.loads(outputs.get("summary", "{}"))
        matched_count = summary.get("matched_count", 0)
        executed_at = summary.get("executed_at", "")

        result["matched_count"] = matched_count

        print(f"\n📊 提取完成：")
        print(f"   - 匹配邮件: {matched_count} 封")
        print(f"   - 执行时间: {executed_at}")

        # 5. 下载Artifact
        artifact_name = f"extraction-results-{run_id}"
        print(f"\n📥 下载结果...")

        download_path_obj = Path(download_dir)
        download_path_obj.mkdir(parents=True, exist_ok=True)

        zip_file = client.download_artifact(
            run_id=run_id,
            artifact_name=artifact_name,
            download_path=str(download_path_obj)
        )

        print(f"✅ 已下载: {zip_file}")
        result["download_path"] = str(zip_file)

        # 6. 解压
        if extract:
            extract_dir = download_path_obj / artifact_name
            extract_dir.mkdir(parents=True, exist_ok=True)

            print(f"\n📂 解压到: {extract_dir}")

            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)

            print(f"✅ 解压完成")

            # 7. 查看摘要
            summary_files = list(extract_dir.rglob("summary.json"))
            if summary_files:
                summary_file = summary_files[0]
                with open(summary_file, 'r', encoding='utf-8') as f:
                    summary_data = json.load(f)

                print(f"\n📋 提取摘要:")
                print(f"   - 时间戳: {summary_data.get('timestamp')}")
                print(f"   - 总文件数: {summary_data.get('total_files')}")
                print(f"   - 类别数: {summary_data.get('categories_copied')}")

            # 8. 列出文件
            if list_files:
                print(f"\n📎 文件清单:")

                # 遍历所有类别
                for category in ["bodies", "attachments", "extracted", "nuonuo_invoices"]:
                    category_dirs = list(extract_dir.rglob(category))
                    if category_dirs:
                        category_dir = category_dirs[0]
                        files = [f for f in category_dir.rglob("*") if f.is_file()]

                        if files:
                            print(f"\n   {category}/ ({len(files)} 个文件)")
                            for f in files[:10]:  # 只显示前10个
                                print(f"      - {f.name}")
                            if len(files) > 10:
                                print(f"      ... 还有 {len(files) - 10} 个文件")

        result["success"] = True

        print(f"\n✅ 流程完成！")
        return result

    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ 错误: {error_msg}")
        result["error"] = error_msg
        return result


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description='自动化邮件提取并处理结果')
    parser.add_argument('--repo', help='GitHub仓库 (username/repo)')
    parser.add_argument('--token', help='GitHub Personal Access Token')
    parser.add_argument('--time-range-days', type=int, default=20, help='搜索时间范围（天）')
    parser.add_argument('--download-dir', default='./downloads', help='下载目录')
    parser.add_argument('--no-extract', action='store_true', help='不解压ZIP文件')
    parser.add_argument('--no-list', action='store_true', help='不列出文件清单')

    args = parser.parse_args()

    # 从参数或环境变量读取配置
    repo = args.repo or os.environ.get("GITHUB_REPO")
    token = args.token or os.environ.get("GITHUB_TOKEN")

    if not token:
        print("❌ 请提供GitHub Token:")
        print("   方式1: --token YOUR_TOKEN")
        print("   方式2: export GITHUB_TOKEN=YOUR_TOKEN")
        return 1

    if not repo:
        print("❌ 请提供GitHub仓库:")
        print("   方式1: --repo username/repo")
        print("   方式2: export GITHUB_REPO=username/repo")
        return 1

    # 执行自动化提取
    result = automated_extraction(
        repo=repo,
        token=token,
        time_range_days=args.time_range_days,
        download_dir=args.download_dir,
        extract=not args.no_extract,
        list_files=not args.no_list
    )

    return 0 if result["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
