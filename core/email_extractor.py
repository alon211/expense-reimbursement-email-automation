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
            Path: 提取目录路径（格式：extracted_mails/YYYY-MM-DD_HHMMSS/）

        注意：每次运行使用时间戳命名，但会通过预检查避免重复提取
        """
        # 恢复时间戳命名（每次运行独立目录）
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

    def process_archived_attachments(self, attachment_paths: List[str], rule: object, extraction_dir: Path) -> dict:
        """
        处理压缩文件附件，自动解压

        Args:
            attachment_paths: 附件文件路径列表
            rule: 规则对象
            extraction_dir: 提取目录

        Returns:
            dict: {
                'archive_count': 压缩包数量,
                'extracted_count': 解压的文件数量,
                'extracted_paths': 解压后的文件路径列表
            }
        """
        logger.info(f"【提取器】process_archived_attachments() 方法被调用，附件数量：{len(attachment_paths)}")
        logger.info(f"【提取器】规则配置：should_extract_archives={rule.should_extract_archives()}")

        from utils.archive_utils import ArchiveExtractor

        # 检查规则是否允许解压
        if not rule.should_extract_archives():
            logger.info("【提取器】规则配置为不解压压缩文件，跳过处理")
            logger.debug("【提取器】规则配置不解压压缩文件，跳过")
            return {
                'archive_count': 0,
                'extracted_count': 0,
                'extracted_paths': []
            }

        # 获取解压配置
        password = rule.get_archive_password()
        allowed_types = rule.get_allowed_archive_types()

        # 如果没有指定允许的格式，使用默认支持的格式
        if not allowed_types:
            allowed_types = ['.zip', '.rar', '.7z', '.tar.gz', '.tar.bz2', '.tgz', '.tbz2', '.tar']

        logger.info(f"【提取器】开始检查压缩文件附件（允许格式：{', '.join(allowed_types)}）")

        archive_extractor = ArchiveExtractor()
        archive_count = 0
        extracted_count = 0
        extracted_paths = []

        # 遍历附件，查找压缩文件
        for attachment_path in attachment_paths:
            attachment_file = Path(attachment_path)

            # 检查是否为压缩文件
            if not archive_extractor.is_archive_file(attachment_file, allowed_types):
                logger.debug(f"【提取器】跳过非压缩文件：{attachment_file.name}")
                continue

            # 获取压缩文件类型
            archive_type = archive_extractor.get_archive_type(attachment_file)
            if not archive_type:
                logger.warning(f"【提取器】无法识别压缩文件类型：{attachment_file.name}")
                continue

            logger.info(f"【提取器】发现压缩文件：{attachment_file.name} (类型: {archive_type})")
            archive_count += 1

            # 解压文件
            try:
                result = archive_extractor.extract_archive(
                    archive_path=attachment_file,
                    extract_dir=attachment_file.parent,  # 解压到附件所在目录
                    password=password if password else None,
                    allowed_types=allowed_types
                )

                extracted_count += result['extracted_count']
                extracted_paths.extend(result['extracted_paths'])

                logger.info(f"【提取器】✅ 解压成功：{attachment_file.name}")
                logger.info(f"【提取器】   解压文件数：{result['extracted_count']}")
                logger.info(f"【提取器】   解压目录：{result['extract_dir']}")

            except Exception as e:
                logger.error(f"【提取器】❌ 解压失败：{attachment_file.name}，错误：{e}")

        # 输出汇总日志
        if archive_count > 0:
            logger.info(f"【提取器】压缩文件处理完成：")
            logger.info(f"【提取器】   发现压缩包：{archive_count} 个")
            logger.info(f"【提取器】   解压文件：{extracted_count} 个")
        else:
            logger.debug("【提取器】未发现压缩文件附件")

        return {
            'archive_count': archive_count,
            'extracted_count': extracted_count,
            'extracted_paths': extracted_paths
        }

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
    根据规则的 extract_options 决定提取哪些内容

    Args:
        msg: 邮件对象
        mail_data: 邮件数据（包含主题、发件人、matched_rules等）
        extraction_dir: 提取目录

    Returns:
        dict: 提取结果
            - storage_path: 提取目录路径
            - body_file_path: 正文文件路径
            - attachment_count: 附件数量
            - attachment_paths: 附件文件路径列表
            - extracted_content_path: 提取内容文件路径
    """
    # 调试信息：确认函数被调用
    print("=" * 60, flush=True)
    print("【DEBUG-PRIORITY-1】extract_email_full 函数被调用", flush=True)
    print(f"【DEBUG-PRIORITY-1】邮件主题：{mail_data.get('subject', '')}", flush=True)
    print("=" * 60, flush=True)

    extractor = EmailExtractor()
    message_id = mail_data.get('message_id', '')
    primary_rule = mail_data.get('matched_rules', [None])[0]

    if primary_rule:
        primary_rule_id = primary_rule.rule_id
        logger.info(f"【提取器】使用规则：{primary_rule.rule_name} (ID: {primary_rule_id})")
    else:
        primary_rule_id = "unknown"
        logger.warning("【提取器】未找到匹配规则，使用默认规则 ID")
        # 创建一个默认规则对象（提取所有内容）
        from core.rule_loader import Rule
        primary_rule = Rule({
            "rule_id": "unknown",
            "rule_name": "默认规则",
            "enabled": True,
            "extract_options": {
                "extract_attachments": True,
                "extract_body": True,
                "extract_headers": True
            }
        })

    logger.info(f"【提取器】开始提取邮件：{mail_data.get('subject', '')}")
    logger.debug(f"【提取器】提取选项：extract_body={primary_rule.should_extract_body()}, extract_attachments={primary_rule.should_extract_attachments()}")

    # 根据规则的 extract_options 决定提取内容
    body_file_path = ""
    attachment_count = 0
    attachment_paths = []
    extracted_content_path = ""

    # 1. 保存邮件正文HTML（如果规则要求）
    if primary_rule.should_extract_body():
        logger.info("【提取器】根据规则配置，提取邮件正文")
        body_file_path = extractor.save_email_body(msg, primary_rule_id, extraction_dir, message_id)
    else:
        logger.info("【提取器】规则配置不提取正文，跳过")

    # 2. 提取附件（如果规则要求）
    if primary_rule.should_extract_attachments():
        logger.info("【提取器】根据规则配置，提取附件")
        attachment_count, attachment_paths = extractor.extract_attachments(msg, primary_rule_id, extraction_dir, message_id)

        # 2.5 处理压缩文件附件（如果规则允许）
        if attachment_count > 0:
            logger.info(f"【提取器】准备检查 {attachment_count} 个附件中是否有压缩文件")
            archive_result = extractor.process_archived_attachments(attachment_paths, primary_rule, extraction_dir)

            # 更新统计信息
            attachment_count += archive_result['extracted_count']
            attachment_paths.extend(archive_result['extracted_paths'])

            # 如果有压缩文件被解压，记录额外信息
            if archive_result['archive_count'] > 0:
                logger.info(f"【提取器】压缩文件处理：发现 {archive_result['archive_count']} 个压缩包，解压 {archive_result['extracted_count']} 个文件")
    else:
        logger.info("【提取器】规则配置不提取附件，跳过")

    # 3. 保存提取的结构化内容（始终保存，用于记录）
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
