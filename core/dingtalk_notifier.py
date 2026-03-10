# -*- coding: utf-8 -*-
"""钉钉通知模块

提供钉钉机器人消息推送功能，支持签名验证。
"""
import time
import hmac
import hashlib
import base64
import urllib.parse
import requests
import logging
from config.settings import DINGTALK_WEBHOOK, DINGTALK_SECRET, PUSH_SWITCH

logger = logging.getLogger("DingtalkNotifier")


def send_dingtalk_message(content: str) -> bool:
    """
    发送钉钉消息

    Args:
        content: 消息内容

    Returns:
        bool: 是否发送成功
    """
    if not PUSH_SWITCH:
        logger.info("推送开关已关闭，跳过钉钉消息发送")
        return True

    if not DINGTALK_WEBHOOK:
        logger.warning("钉钉 Webhook 未配置，跳过消息发送")
        return False

    try:
        # 构建请求数据
        data = {
            "msgtype": "text",
            "text": {
                "content": content
            }
        }

        # 如果配置了签名密钥，添加签名验证
        webhook_url = DINGTALK_WEBHOOK
        if DINGTALK_SECRET:
            timestamp = str(round(time.time() * 1000))
            secret_enc = bytes(DINGTALK_SECRET, 'utf-8')
            string_to_sign = f'{timestamp}\n{DINGTALK_SECRET}'
            hmac_code = hmac.new(
                secret_enc,
                string_to_sign.encode('utf-8'),
                digestmod=hashlib.sha256
            ).digest()
            sign = urllib.parse.quote(base64.b64encode(hmac_code))
            webhook_url = f"{DINGTALK_WEBHOOK}&timestamp={timestamp}&sign={sign}"

        # 发送请求
        response = requests.post(
            webhook_url,
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        # 检查响应
        result = response.json()
        if result.get("errcode") == 0:
            logger.info(f"钉钉消息发送成功：{content[:50]}...")
            return True
        else:
            logger.error(f"钉钉消息发送失败：{result.get('errmsg')}")
            return False

    except requests.RequestException as e:
        logger.error(f"钉钉消息发送异常（网络错误）：{str(e)}")
        return False
    except Exception as e:
        logger.error(f"钉钉消息发送异常：{str(e)}")
        return False
