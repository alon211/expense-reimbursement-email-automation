# -*- coding: utf-8 -*-
"""
GitHub API客户端
用于触发workflow和获取结果
"""
import requests
import time
from typing import Dict, Optional


class GitHubWorkflowClient:
    """GitHub Workflow API客户端"""

    def __init__(self, token: str, repo: str):
        """
        Args:
            token: GitHub Personal Access Token
            repo: 仓库格式 "username/repo"
        """
        self.token = token
        self.repo = repo
        self.api_base = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }

    def trigger_workflow(self, workflow_file: str, inputs: Dict = None, ref: str = "main") -> str:
        """
        触发workflow_dispatch事件

        Args:
            workflow_file: 工作流文件名（如 "email-extraction.yml"）
            inputs: 输入参数字典
            ref: 分支名称（默认 "main"）

        Returns:
            run_id: 工作流运行ID

        Raises:
            requests.HTTPError: API请求失败
        """
        url = f"{self.api_base}/repos/{self.repo}/actions/workflows/{workflow_file}/dispatches"

        payload = {"ref": ref}
        if inputs:
            payload["inputs"] = inputs

        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()

        # 获取最新的run_id
        time.sleep(2)  # 等待workflow创建
        run_id = self._get_latest_run_id()

        return run_id

    def get_workflow_status(self, run_id: str) -> Dict:
        """
        查询工作流状态

        Args:
            run_id: 工作流运行ID

        Returns:
            包含status、conclusion等信息的字典

        Raises:
            requests.HTTPError: API请求失败
        """
        url = f"{self.api_base}/repos/{self.repo}/actions/runs/{run_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_workflow_outputs(self, run_id: str, timeout: int = 600, poll_interval: int = 10) -> Dict:
        """
        获取工作流输出结果

        注意：需要在workflow完成后才能获取

        Args:
            run_id: 工作流运行ID
            timeout: 超时时间（秒，默认600秒=10分钟）
            poll_interval: 轮询间隔（秒，默认10秒）

        Returns:
            包含summary、detail、status等输出的字典

        Raises:
            Exception: workflow超时或失败
        """
        start_time = time.time()

        # 等待workflow完成
        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                raise Exception(f"Workflow执行超时（{timeout}秒）")

            status_data = self.get_workflow_status(run_id)
            workflow_status = status_data.get("status")

            if workflow_status == "completed":
                conclusion = status_data.get("conclusion")
                if conclusion == "success":
                    break
                else:
                    raise Exception(f"Workflow执行失败: {conclusion}")
            elif workflow_status in ["queued", "in_progress"]:
                print(f"⏳ Workflow状态: {workflow_status}（已运行 {int(elapsed)}秒）")
                time.sleep(poll_interval)
            else:
                raise Exception(f"Workflow状态异常: {workflow_status}")

        # 获取outputs
        outputs = status_data.get("outputs", {})
        return outputs

    def download_artifact(self, run_id: str, artifact_name: str, download_path: str = ".") -> str:
        """
        下载工作流Artifact

        Args:
            run_id: 工作流运行ID
            artifact_name: Artifact名称
            download_path: 下载保存路径

        Returns:
            下载的文件路径

        Raises:
            Exception: Artifact不存在或下载失败
        """
        # 获取Artifact列表
        url = f"{self.api_base}/repos/{self.repo}/actions/runs/{run_id}/artifacts"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()

        artifacts = response.json().get("artifacts", [])

        # 查找目标Artifact
        target_artifact = None
        for artifact in artifacts:
            if artifact["name"] == artifact_name:
                target_artifact = artifact
                break

        if not target_artifact:
            available = [a["name"] for a in artifacts]
            raise Exception(f"Artifact '{artifact_name}' 不存在。可用Artifacts: {available}")

        # 下载Artifact
        download_url = target_artifact["archive_download_url"]
        response = requests.get(download_url, headers=self.headers)
        response.raise_for_status()

        # 保存文件
        import os
        filename = f"{artifact_name}.zip"
        filepath = os.path.join(download_path, filename)

        with open(filepath, 'wb') as f:
            f.write(response.content)

        return filepath

    def _get_latest_run_id(self) -> str:
        """获取最新的工作流运行ID

        Returns:
            run_id: 工作流运行ID

        Raises:
            requests.HTTPError: API请求失败
            Exception: 没有找到工作流运行记录
        """
        url = f"{self.api_base}/repos/{self.repo}/actions/runs?per_page=1"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()

        workflow_runs = response.json().get("workflow_runs", [])
        if not workflow_runs:
            raise Exception("没有找到工作流运行记录")

        return str(workflow_runs[0]["id"])


# 使用示例
if __name__ == "__main__":
    import os

    # 从环境变量读取配置
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPO")

    if not token or not repo:
        print("❌ 请设置环境变量:")
        print("   export GITHUB_TOKEN=your_token")
        print("   export GITHUB_REPO=username/repo")
        exit(1)

    client = GitHubWorkflowClient(token=token, repo=repo)

    # 触发workflow
    run_id = client.trigger_workflow(
        workflow_file="email-extraction.yml",
        inputs={"time_range_days": "20"}
    )

    print(f"✅ Workflow已触发，run_id: {run_id}")

    # 等待并获取结果
    try:
        outputs = client.get_workflow_outputs(run_id)
        print(f"📊 提取结果: {outputs.get('summary')}")
    except Exception as e:
        print(f"❌ 获取结果失败: {e}")
