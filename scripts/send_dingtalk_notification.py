#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发送钉钉通知
"""
import sys
import argparse
import hmac
import hashlib
import base64
import time
import requests
from urllib.parse import quote
import json


def send_dingtalk(webhook_url: str, secret: str, summary: str):
    """
    发送钉钉消息

    Args:
        webhook_url: 钉钉Webhook URL
        secret: 钉钉签名密钥
        summary: 摘要信息（JSON字符串）

    Raises:
        requests.HTTPError: 发送失败
        json.JSONDecodeError: JSON解析失败
    """
    # 生成签名
    timestamp = str(round(time.time() * 1000))
    secret_enc = secret.encode('utf-8')
    string_to_sign = f'{timestamp}\n{secret}'
    string_to_sign_enc = string_to_sign.encode('utf-8')
    hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
    sign = quote(base64.b64encode(hmac_code))

    # 构建URL
    url = f"{webhook_url}&timestamp={timestamp}&sign={sign}"

    # 解析摘要信息
    try:
        summary_data = json.loads(summary)
    except json.JSONDecodeError:
        # 如果不是JSON，直接使用原始字符串
        summary_data = {"raw": summary}

    # 构建消息内容
    content_lines = ["✅ 邮件提取完成", ""]

    if isinstance(summary_data, dict):
        # 提取关键字段
        if summary_data.get("matched_count") is not None:
            content_lines.append(f"📧 匹配邮件: {summary_data['matched_count']} 封")

        if summary_data.get("time_range_days"):
            content_lines.append(f"⏱️  时间范围: {summary_data['time_range_days']} 天")

        if summary_data.get("executed_at"):
            content_lines.append(f"🕐 执行时间: {summary_data['executed_at']}")

        if summary_data.get("success") is not None:
            status = "成功" if summary_data['success'] else "失败"
            content_lines.append(f"📊 状态: {status}")

    content = "\n".join(content_lines)

    # 构建消息
    data = {
        "msgtype": "text",
        "text": {
            "content": content
        }
    }

    # 发送
    response = requests.post(url, json=data)
    response.raise_for_status()

    result = response.json()
    if result.get("errcode") == 0:
        print("✅ 钉钉通知已发送")
    else:
        print(f"⚠️  钉钉通知返回错误: {result}")


def main():
    parser = argparse.ArgumentParser(description='发送钉钉通知')
    parser.add_argument('--webhook', required=True, help='钉钉Webhook URL')
    parser.add_argument('--secret', required=True, help='钉钉签名密钥')
    parser.add_argument('--summary', required=True, help='摘要信息（JSON字符串）')

    args = parser.parse_args()

    try:
        send_dingtalk(args.webhook, args.secret, args.summary)
        return 0
    except Exception as e:
        print(f"❌ 发送钉钉通知失败: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
