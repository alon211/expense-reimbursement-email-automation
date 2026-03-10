# -*- coding: utf-8 -*-
import imaplib
import email
import time
import logging
import os
import json
import hmac
import hashlib
import base64
import urllib.parse
import requests
from email.header import decode_header
from logging.handlers import RotatingFileHandler
from datetime import datetime
import pytz

# 加载配置
from config import *

# ===================== 日志初始化 =====================
def init_logger():
    # 创建日志目录
    log_dir = os.path.dirname(LOG_FILE)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 配置日志格式
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台日志
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)
    
    # 文件日志（按大小切割）
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=LOG_MAX_SIZE,
        backupCount=LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setFormatter(log_format)
    
    # 初始化logger
    logger = logging.getLogger("ReimbursementMailFetcher")
    logger.setLevel(LOG_LEVEL)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

# 初始化日志
logger = init_logger()

# ===================== 推送工具（钉钉） =====================
def send_dingtalk_message(content):
    """发送钉钉消息"""
    if not PUSH_SWITCH:
        return
    
    try:
        timestamp = str(round(time.time() * 1000))
        secret_enc = DINGTALK_SECRET.encode('utf-8')
        string_to_sign = f'{timestamp}\n{DINGTALK_SECRET}'
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        
        headers = {'Content-Type': 'application/json;charset=utf-8'}
        data = {
            "msgtype": "text",
            "text": {
                "content": f"【报销邮件提醒】{content}"
            }
        }
        
        # 拼接签名（如果有secret）
        url = f"{DINGTALK_WEBHOOK}&timestamp={timestamp}&sign={sign}" if DINGTALK_SECRET else DINGTALK_WEBHOOK
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        if response.status_code == 200 and response.json().get("errcode") == 0:
            logger.info("钉钉消息推送成功")
        else:
            logger.error(f"钉钉消息推送失败：{response.text}")
    except Exception as e:
        logger.error(f"钉钉推送异常：{str(e)}")

# ===================== 邮件解析工具 =====================
def decode_mail_header(header):
    """解码邮件头（处理中文乱码）"""
    decoded, encoding = decode_header(header)[0]
    if encoding:
        return decoded.decode(encoding)
    return str(decoded)

def parse_reimbursement_mail(msg):
    """解析报销邮件内容（可根据你的需求自定义）"""
    # 提取核心信息
    subject = decode_mail_header(msg.get("Subject", "无主题"))
    sender = decode_mail_header(msg.get("From", "未知发件人"))
    date = decode_mail_header(msg.get("Date", "未知时间"))
    
    # 提取邮件正文（简单版，可根据需求扩展）
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                body = part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8')
                break
    else:
        body = msg.get_payload(decode=True).decode(msg.get_content_charset() or 'utf-8')
    
    # 筛选报销相关邮件（可自定义关键词）
    reimbursement_keywords = ["报销", "费用", "发票", "Reimbursement", "Expense"]
    if any(keyword in subject or keyword in body for keyword in reimbursement_keywords):
        logger.info(f"发现报销邮件：主题={subject}，发件人={sender}")
        return {
            "subject": subject,
            "sender": sender,
            "date": date,
            "body": body[:200] + "..." if len(body) > 200 else body  # 截断长正文
        }
    return None

# ===================== 核心邮件拉取函数 =====================
def fetch_reimbursement_mails():
    """拉取报销相关邮件"""
    mail_conn = None
    try:
        # 连接IMAP服务器
        logger.info(f"开始连接IMAP服务器：{IMAP_HOST}")
        mail_conn = imaplib.IMAP4_SSL(IMAP_HOST)
        
        # 登录
        mail_conn.login(IMAP_USER, IMAP_PASS)
        logger.info("邮箱登录成功")
        
        # 选择文件夹
        mail_conn.select(MAIL_CHECK_FOLDER)
        logger.info(f"选中文件夹：{MAIL_CHECK_FOLDER}")
        
        # 搜索邮件
        status, messages = mail_conn.search(None, MAIL_SEARCH_CRITERIA)
        if status != 'OK':
            logger.warning("未找到符合条件的邮件")
            return
        
        # 解析每封邮件
        mail_count = 0
        reimbursement_mails = []
        for num in messages[0].split():
            status, data = mail_conn.fetch(num, '(RFC822)')
            msg = email.message_from_bytes(data[0][1])
            
            # 解析报销邮件
            reimbursement_mail = parse_reimbursement_mail(msg)
            if reimbursement_mail:
                reimbursement_mails.append(reimbursement_mail)
                mail_count += 1
                
                # 标记为已读（可选）
                mail_conn.store(num, '+FLAGS', '\\Seen')
        
        # 推送提醒
        if reimbursement_mails:
            push_content = f"共发现{mail_count}封报销相关邮件：\n"
            for mail in reimbursement_mails:
                push_content += f"- 主题：{mail['subject']}（发件人：{mail['sender']}）\n"
            send_dingtalk_message(push_content)
        else:
            logger.info("本次未发现报销相关邮件")
        
    except Exception as e:
        logger.error(f"拉取邮件异常：{str(e)}")
        send_dingtalk_message(f"邮件拉取失败：{str(e)}")
    finally:
        if mail_conn:
            mail_conn.close()
            mail_conn.logout()
            logger.info("邮箱连接已关闭")

# ===================== 定时任务主循环 =====================
def main():
    """主函数：定时拉取邮件"""
    # 设置时区
    tz = pytz.timezone(TIME_ZONE)
    logger.info(f"报销邮件拉取服务启动（Python 3.12），时区：{TIME_ZONE}，检查间隔：{CHECK_INTERVAL}秒")
    
    # 无限循环定时执行
    while True:
        try:
            current_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"\n=== 开始新一轮邮件检查：{current_time} ===")
            fetch_reimbursement_mails()
        except Exception as e:
            logger.error(f"主循环异常：{str(e)}")
        
        # 等待下一次执行
        logger.info(f"等待{CHECK_INTERVAL}秒后进行下一次检查...")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()