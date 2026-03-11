#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
命令行工具：触发GitHub Actions workflow
"""
import sys
import argparse
import json
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.github_client import GitHubWorkflowClient


def main():
    parser = argparse.ArgumentParser(description='触发GitHub Actions工作流')
    parser.add_argument('--token', help='GitHub Personal Access Token（默认从环境变量GITHUB_TOKEN读取）')
    parser.add_argument('--repo', help='GitHub仓库 (username/repo)（默认从环境变量GITHUB_REPO读取）')
    parser.add_argument('--workflow', default='email-extraction.yml', help='工作流文件名')
    parser.add_argument('--time-range-days', type=int, default=20, help='搜索时间范围（天）')
    parser.add_argument('--rule-filter', help='规则ID过滤器（逗号分隔）')
    parser.add_argument('--wait', action='store_true', help='等待执行完成并获取结果')
    parser.add_argument('--timeout', type=int, default=600, help='等待超时时间（秒，默认600）')
    parser.add_argument('--download-artifacts', action='store_true', help='下载Artifacts到当前目录')

    args = parser.parse_args()

    # 从参数或环境变量读取配置
    token = args.token or os.environ.get("GITHUB_TOKEN")
    repo = args.repo or os.environ.get("GITHUB_REPO")

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

    # 创建客户端
    client = GitHubWorkflowClient(token=token, repo=repo)

    # 准备输入参数
    inputs = {"time_range_days": str(args.time_range_days)}
    if args.rule_filter:
        inputs["rule_filter"] = args.rule_filter

    # 触发workflow
    print(f"🚀 触发workflow: {args.workflow}")
    print(f"📂 仓库: {repo}")
    print(f"⏱️  时间范围: {args.time_range_days}天")
    if args.rule_filter:
        print(f"🔍 规则过滤: {args.rule_filter}")

    try:
        run_id = client.trigger_workflow(
            workflow_file=args.workflow,
            inputs=inputs
        )

        print(f"\n✅ Workflow已触发")
        print(f"📌 Run ID: {run_id}")
        print(f"🔗 查看详情: https://github.com/{repo}/actions/runs/{run_id}")

        # 等待完成
        if args.wait:
            print(f"\n⏳ 等待执行完成（最长{args.timeout}秒）...")

            outputs = client.get_workflow_outputs(run_id, timeout=args.timeout)

            print("\n📊 执行结果:")
            print(json.dumps(outputs, indent=2, ensure_ascii=False))

            # 下载Artifacts
            if args.download_artifacts:
                print(f"\n📥 下载Artifacts...")
                artifact_name = f"extraction-results-{run_id}"
                try:
                    filepath = client.download_artifact(run_id, artifact_name)
                    print(f"✅ 已下载: {filepath}")
                except Exception as e:
                    print(f"⚠️  下载Artifact失败: {e}")

            # 检查执行状态
            status = outputs.get("status", "")
            if status == "true" or status is True:
                print("\n✅ 执行成功")
                return 0
            else:
                print("\n❌ 执行失败")
                return 1

        return 0

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
