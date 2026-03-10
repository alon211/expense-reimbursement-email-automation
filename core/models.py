# -*- coding: utf-8 -*-
"""数据模型模块

定义邮件提取相关的数据模型。
"""
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime


@dataclass
class ExtractedEmail:
    """已提取邮件记录模型"""
    id: Optional[int] = None
    message_id: str = ""
    subject: str = ""
    sender: str = ""
    rule_id: str = ""
    extracted_at: Optional[datetime] = None
    storage_path: str = ""
    attachment_count: int = 0
    body_file_path: str = ""

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'message_id': self.message_id,
            'subject': self.subject,
            'sender': self.sender,
            'rule_id': self.rule_id,
            'extracted_at': self.extracted_at.isoformat() if self.extracted_at else None,
            'storage_path': self.storage_path,
            'attachment_count': self.attachment_count,
            'body_file_path': self.body_file_path
        }


@dataclass
class ExtractionHistory:
    """提取历史记录模型"""
    id: Optional[int] = None
    message_id: str = ""
    rule_id: str = ""
    action: str = ""
    created_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'message_id': self.message_id,
            'rule_id': self.rule_id,
            'action': self.action,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
