# -*- coding: utf-8 -*-
"""邮件提取和文件存储模块

实现邮件正文、附件的提取和分类存储功能。
"""
import os
import email
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Optional
from email.header import decode_header

from config.settings import EXTRACT_ROOT_DIR


logger = logging.getLogger("EmailExtractor")


class EmailExtractor:
    """邮件提取器：负责提取和保存邮件内容"""

    def __init__(self, root_dir: str = None):
        """
        初始化邮件提取器

        Args:
            root_dir: 提取根目录，默认从配置读取
        """
        self.root_dir = Path(root_dir or EXTRACT_ROOT_DIR)
        self.root_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"【提取器初始化】根目录：{self.root_dir}")

    def create_extraction_dir(self) -> Path:
        """
        创建本次提取的存储目录

        Returns:
            Path: 提取目录路径（格式：extracted_mails/2026-03-11_143020）
        """
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        extraction_dir = self.root_dir / timestamp
        extraction_dir.mkdir(parents=True, exist_ok=True)

        # 创建子目录
        (extraction_dir / "bodies").mkdir(exist_ok=True)
        (extraction_dir / "attachments").mkdir(exist_ok=True)
        (extraction_dir / "extracted").mkdir(exist_ok=True)

        logger.info(f"【提取器】创建提取目录：{extraction_dir}")
        return extraction_dir

    def save_email_body(self, msg: email.message.Message, rule_id: str, extraction_dir: Path, message_id: str) -> str:
        """
        保存邮件正文HTML

        Args:
            msg: 邮件对象
            rule_id: 匹配的规则ID
            extraction_dir: 提取目录
            message_id: 邮件唯一标识

        Returns:
            str: 保存的文件路径
        """
        # 创建规则目录
        rule_dir = extraction_dir / "bodies" / rule_id
        rule_dir.mkdir(parents=True, exist_ok=True)

        # 生成文件名（使用 message_id 的哈希值避免文件名过长）
        import hashlib
        safe_message_id = hashlib.md5(message_id.encode()).hexdigest()[:12]
        filename = f"{safe_message_id}.html"
        file_path = rule_dir / filename

        # 提取HTML内容
        html_content = self._extract_html_content(msg)

        # 保存文件
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.debug(f"【提取器】保存邮件正文：{file_path}")
            return str(file_path)
        except Exception as e:
            logger.error(f"【提取器】保存正文失败：{e}")
            return ""

    def extract_attachments(self, msg: email.message.Message, rule_id: str, extraction_dir: Path, message_id: str) -> Tuple[int, List[str]]:
        """
        提取并保存邮件附件

        Args:
            msg: 邮件对象
            rule_id: 匹配的规则ID
            extraction_dir: 提取目录
            message_id: 邮件唯一标识

        Returns:
            tuple: (附件数量, 附件文件路径列表)
        """
        # 创建规则目录
        rule_dir = extraction_dir / "attachments" / rule_id
        rule_dir.mkdir(parents=True, exist_ok=True)

        attachments = []
        attachment_count = 0

        # 遍历邮件的所有部分
        for part in msg.walk():
            # 跳过非附件部分
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue

            # 解码文件名
            filename = part.get_filename()
            if filename:
                filename = self._decode_filename(filename)
                logger.debug(f"【提取器】发现附件：{filename}")

                # 保存附件
                filepath = rule_dir / filename
                try:
                    with open(filepath, 'wb') as f:
                        f.write(part.get_payload(decode=True))
                    attachments.append(str(filepath))
                    attachment_count += 1
                    logger.info(f"【提取器】保存附件：{filepath}")
                except Exception as e:
                    logger.error(f"【提取器】保存附件失败：{filename}，错误：{e}")

        # 输出附件汇总日志
        if attachment_count > 0:
            logger.info(f"【提取器】✅ 成功提取 {attachment_count} 个附件到：{rule_dir}")
            for idx, att_path in enumerate(attachments, 1):
                logger.info(f"【提取器】  附件{idx}: {att_path}")

        return attachment_count, attachments

    def save_extracted_content(self, mail_data: dict, rule_id: str, extraction_dir: Path, message_id: str) -> str:
        """
        保存提取的结构化内容（JSON格式）

        Args:
            mail_data: 提取的邮件数据
            rule_id: 匹配的规则ID
            extraction_dir: 提取目录
            message_id: 邮件唯一标识

        Returns:
            str: 保存的文件路径
        """
        import json

        # 创建规则目录
        rule_dir = extraction_dir / "extracted" / rule_id
        rule_dir.mkdir(parents=True, exist_ok=True)

        # 生成文件名
        import hashlib
        safe_message_id = hashlib.md5(message_id.encode()).hexdigest()[:12]
        filename = f"{safe_message_id}.json"
        file_path = rule_dir / filename

        # 准备JSON数据
        extracted_data = {
            "message_id": message_id,
            "subject": mail_data.get('subject', ''),
            "sender": mail_data.get('sender', ''),
            "date": mail_data.get('date', ''),
            "body": mail_data.get('body', ''),
            "matched_rules": [rule.rule_id for rule in mail_data.get('matched_rules', [])],
            "extracted_at": datetime.now().isoformat()
        }

        # 保存文件
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(extracted_data, f, ensure_ascii=False, indent=2)
            logger.debug(f"【提取器】保存提取内容：{file_path}")
            return str(file_path)
        except Exception as e:
            logger.error(f"【提取器】保存提取内容失败：{e}")
            return ""

    def _extract_html_content(self, msg: email.message.Message) -> str:
        """
        提取邮件HTML内容

        Args:
            msg: 邮件对象

        Returns:
            str: HTML内容
        """
        html_content = ""

        try:
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    if content_type == "text/html":
                        payload = part.get_payload(decode=True)
                        charset = part.get_content_charset() or 'utf-8'
                        html_content = payload.decode(charset, errors='ignore')
                        break
                    elif content_type == "text/plain" and not html_content:
                        # 如果没有HTML，使用纯文本
                        payload = part.get_payload(decode=True)
                        charset = part.get_content_charset() or 'utf-8'
                        text_content = payload.decode(charset, errors='ignore')
                        # 将纯文本包装为HTML
                        html_content = f"<pre>{text_content}</pre>"
            else:
                content_type = msg.get_content_type()
                payload = msg.get_payload(decode=True)
                charset = msg.get_content_charset() or 'utf-8'

                if content_type == "text/html":
                    html_content = payload.decode(charset, errors='ignore')
                else:
                    text_content = payload.decode(charset, errors='ignore')
                    html_content = f"<pre>{text_content}</pre>"
        except Exception as e:
            logger.error(f"【提取器】提取HTML失败：{e}")
            html_content = f"<p>内容提取失败：{str(e)}</p>"

        return html_content

    def _decode_filename(self, filename: str) -> str:
        """
        解码附件文件名

        Args:
            filename: 编码的文件名

        Returns:
            str: 解码后的文件名
        """
        try:
            decoded_parts = decode_header(filename)
            filename = ''
            for content, charset in decoded_parts:
                if isinstance(content, bytes):
                    if charset:
                        filename += content.decode(charset, errors='ignore')
                    else:
                        filename += content.decode('utf-8', errors='ignore')
                else:
                    filename += content
            return filename
        except Exception as e:
            logger.error(f"【提取器】解码文件名失败：{e}")
            return "attachment_unknown"


def extract_email_full(msg: email.message.Message, mail_data: dict, extraction_dir: Path) -> dict:
    """
    完整提取一封邮件（正文、附件、提取内容）

    Args:
        msg: 邮件对象
        mail_data: 邮件数据（包含主题、发件人等）
        extraction_dir: 提取目录

    Returns:
        dict: 提取结果
            - storage_path: 提取目录路径
            - body_file_path: 正文文件路径
            - attachment_count: 附件数量
            - attachment_paths: 附件文件路径列表
            - extracted_content_path: 提取内容文件路径
    """
    extractor = EmailExtractor()
    message_id = mail_data.get('message_id', '')
    primary_rule_id = mail_data.get('matched_rules', [None])[0]

    if primary_rule_id:
        primary_rule_id = primary_rule_id.rule_id
    else:
        primary_rule_id = "unknown"

    logger.info(f"【提取器】开始提取邮件：{mail_data.get('subject', '')}")

    # 1. 保存邮件正文HTML
    body_file_path = extractor.save_email_body(msg, primary_rule_id, extraction_dir, message_id)

    # 2. 提取附件
    attachment_count, attachment_paths = extractor.extract_attachments(msg, primary_rule_id, extraction_dir, message_id)

    # 3. 保存提取的结构化内容
    extracted_content_path = extractor.save_extracted_content(mail_data, primary_rule_id, extraction_dir, message_id)

    result = {
        'storage_path': str(extraction_dir),
        'body_file_path': body_file_path,
        'attachment_count': attachment_count,
        'attachment_paths': attachment_paths,
        'extracted_content_path': extracted_content_path
    }

    logger.info(f"【提取器】邮件提取完成：正文={bool(body_file_path)}, 附件={attachment_count}个, 提取内容={bool(extracted_content_path)}")

    return result
