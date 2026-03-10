# -*- coding: utf-8 -*-
"""数据库管理模块

提供邮件去重和存储位置记录功能。
"""
import sqlite3
import logging
from pathlib import Path
from typing import Optional, List
from datetime import datetime
from contextlib import contextmanager

from core.models import ExtractedEmail, ExtractionHistory

logger = logging.getLogger("Database")


class DatabaseManager:
    """数据库管理器"""

    def __init__(self, db_path: str):
        """
        初始化数据库管理器

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self._init_database()

    @contextmanager
    def _get_connection(self):
        """获取数据库连接（上下文管理器）"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 支持字典式访问
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"数据库操作失败，已回滚：{e}")
            raise
        finally:
            conn.close()

    def _init_database(self):
        """初始化数据库表结构"""
        # 确保数据库目录存在
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 创建已提取邮件记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS extracted_emails (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id TEXT UNIQUE NOT NULL,
                    subject TEXT,
                    sender TEXT,
                    rule_id TEXT,
                    mail_date TEXT,
                    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    storage_path TEXT,
                    attachment_count INTEGER DEFAULT 0,
                    body_file_path TEXT
                )
            """)

            # 检查并添加 mail_date 字段（数据库迁移）
            cursor.execute("PRAGMA table_info(extracted_emails)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'mail_date' not in columns:
                logger.info("【数据库迁移】添加 mail_date 字段...")
                cursor.execute("ALTER TABLE extracted_emails ADD COLUMN mail_date TEXT")
                logger.info("【数据库迁移】mail_date 字段添加成功")

            # 创建提取历史表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS extraction_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id TEXT,
                    rule_id TEXT,
                    action TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 创建索引以提高查询性能
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_message_id
                ON extracted_emails(message_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_rule_id
                ON extracted_emails(rule_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_extracted_at
                ON extracted_emails(extracted_at)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_history_message_id
                ON extraction_history(message_id)
            """)

            logger.info(f"数据库初始化完成：{self.db_path}")

    def is_email_extracted(self, message_id: str) -> bool:
        """
        检查邮件是否已提取

        Args:
            message_id: 邮件的 Message-ID

        Returns:
            bool: 是否已提取
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM extracted_emails WHERE message_id = ? LIMIT 1",
                (message_id,)
            )
            return cursor.fetchone() is not None

    def is_email_extracted_with_files(self, message_id: str) -> tuple:
        """
        检查邮件是否已提取且文件存在（增强版去重）

        Args:
            message_id: 邮件的 Message-ID

        Returns:
            tuple: (是否已提取, 数据库记录存在, 提取内容文件存在, 邮件HTML文件存在)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT storage_path, body_file_path FROM extracted_emails WHERE message_id = ?",
                (message_id,)
            )
            row = cursor.fetchone()

            # 数据库中无记录
            if row is None:
                return (False, False, False, False)

            # 数据库有记录，检查文件是否存在
            storage_path = row['storage_path']
            body_file_path = row['body_file_path']

            storage_exists = storage_path and Path(storage_path).exists()
            body_exists = body_file_path and Path(body_file_path).exists()

            # 任意一个关键文件存在就认为已提取
            files_exist = storage_exists or body_exists

            return (files_exist, True, storage_exists, body_exists)

    def add_extracted_email(self, email_record: ExtractedEmail) -> int:
        """
        添加已提取邮件记录

        Args:
            email_record: 邮件记录对象

        Returns:
            int: 插入记录的 ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO extracted_emails
                (message_id, subject, sender, rule_id, mail_date, extracted_at, storage_path, attachment_count, body_file_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                email_record.message_id,
                email_record.subject,
                email_record.sender,
                email_record.rule_id,
                email_record.mail_date,
                email_record.extracted_at or datetime.now(),
                email_record.storage_path,
                email_record.attachment_count,
                email_record.body_file_path
            ))
            return cursor.lastrowid

    def update_extracted_email(self, email_record: ExtractedEmail) -> bool:
        """
        更新已提取邮件记录（用于重新提取文件时更新路径）

        Args:
            email_record: 邮件记录对象

        Returns:
            bool: 是否更新成功
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE extracted_emails
                SET subject = ?, sender = ?, rule_id = ?, mail_date = ?, extracted_at = ?,
                    storage_path = ?, attachment_count = ?, body_file_path = ?
                WHERE message_id = ?
            """, (
                email_record.subject,
                email_record.sender,
                email_record.rule_id,
                email_record.mail_date,
                email_record.extracted_at or datetime.now(),
                email_record.storage_path,
                email_record.attachment_count,
                email_record.body_file_path,
                email_record.message_id
            ))
            updated = cursor.rowcount > 0
            if updated:
                logger.info(f"【数据库】更新邮件记录：message_id={email_record.message_id}")
            return updated

    def get_extracted_email(self, message_id: str) -> Optional[ExtractedEmail]:
        """
        根据 Message-ID 获取已提取邮件记录

        Args:
            message_id: 邮件的 Message-ID

        Returns:
            ExtractedEmail|None: 邮件记录对象
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM extracted_emails WHERE message_id = ?",
                (message_id,)
            )
            row = cursor.fetchone()
            if row:
                return ExtractedEmail(
                    id=row['id'],
                    message_id=row['message_id'],
                    subject=row['subject'],
                    sender=row['sender'],
                    rule_id=row['rule_id'],
                    mail_date=row.get('mail_date', ''),
                    extracted_at=datetime.fromisoformat(row['extracted_at']) if row['extracted_at'] else None,
                    storage_path=row['storage_path'],
                    attachment_count=row['attachment_count'],
                    body_file_path=row['body_file_path']
                )
            return None

    def get_existing_mail_dates(self) -> set:
        """
        获取所有已提取且文件存在的邮件发送时间集合

        Returns:
            set: 邮件发送时间的集合（用于快速去重检查）
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # 查询所有有 storage_path 或 body_file_path 的记录
            cursor.execute("""
                SELECT mail_date, storage_path, body_file_path
                FROM extracted_emails
                WHERE mail_date IS NOT NULL AND mail_date != ''
                AND (storage_path IS NOT NULL AND storage_path != ''
                     OR body_file_path IS NOT NULL AND body_file_path != '')
            """)

            existing_dates = set()
            for row in cursor.fetchall():
                # 验证文件是否真实存在
                storage_path = row['storage_path']
                body_file_path = row['body_file_path']

                # 任意一个文件存在就认为邮件已提取
                if (storage_path and Path(storage_path).exists()) or \
                   (body_file_path and Path(body_file_path).exists()):
                    existing_dates.add(row['mail_date'])

            logger.info(f"【数据库预检查】找到 {len(existing_dates)} 个已提取且文件存在的邮件")
            return existing_dates

    def get_all_extracted_emails(self, limit: int = 100, offset: int = 0) -> List[ExtractedEmail]:
        """
        获取所有已提取邮件记录

        Args:
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            List[ExtractedEmail]: 邮件记录列表
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM extracted_emails ORDER BY extracted_at DESC LIMIT ? OFFSET ?",
                (limit, offset)
            )
            rows = cursor.fetchall()
            return [
                ExtractedEmail(
                    id=row['id'],
                    message_id=row['message_id'],
                    subject=row['subject'],
                    sender=row['sender'],
                    rule_id=row['rule_id'],
                    mail_date=row.get('mail_date', ''),
                    extracted_at=datetime.fromisoformat(row['extracted_at']) if row['extracted_at'] else None,
                    storage_path=row['storage_path'],
                    attachment_count=row['attachment_count'],
                    body_file_path=row['body_file_path']
                )
                for row in rows
            ]

    def add_extraction_history(self, history: ExtractionHistory) -> int:
        """
        添加提取历史记录

        Args:
            history: 历史记录对象

        Returns:
            int: 插入记录的 ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO extraction_history
                (message_id, rule_id, action, created_at)
                VALUES (?, ?, ?, ?)
            """, (
                history.message_id,
                history.rule_id,
                history.action,
                history.created_at or datetime.now()
            ))
            return cursor.lastrowid

    def get_extraction_history(self, message_id: str) -> List[ExtractionHistory]:
        """
        获取指定邮件的提取历史

        Args:
            message_id: 邮件的 Message-ID

        Returns:
            List[ExtractionHistory]: 历史记录列表
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM extraction_history WHERE message_id = ? ORDER BY created_at DESC",
                (message_id,)
            )
            rows = cursor.fetchall()
            return [
                ExtractionHistory(
                    id=row['id'],
                    message_id=row['message_id'],
                    rule_id=row['rule_id'],
                    action=row['action'],
                    created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
                )
                for row in rows
            ]

    def get_statistics(self) -> dict:
        """
        获取数据库统计信息

        Returns:
            dict: 统计信息字典
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 总提取邮件数
            cursor.execute("SELECT COUNT(*) as count FROM extracted_emails")
            total_emails = cursor.fetchone()['count']

            # 按规则统计
            cursor.execute("""
                SELECT rule_id, COUNT(*) as count
                FROM extracted_emails
                GROUP BY rule_id
            """)
            by_rule = {row['rule_id']: row['count'] for row in cursor.fetchall()}

            # 历史记录数
            cursor.execute("SELECT COUNT(*) as count FROM extraction_history")
            total_history = cursor.fetchone()['count']

            return {
                'total_emails': total_emails,
                'by_rule': by_rule,
                'total_history': total_history
            }

    def delete_email_record(self, message_id: str) -> bool:
        """
        删除指定邮件的提取记录

        Args:
            message_id: 邮件的 Message-ID

        Returns:
            bool: 是否删除成功
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM extracted_emails WHERE message_id = ?",
                (message_id,)
            )
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info(f"已删除邮件记录：{message_id}")
            return deleted

    def clear_old_records(self, days: int = 30) -> int:
        """
        清理指定天数之前的记录

        Args:
            days: 天数

        Returns:
            int: 删除的记录数
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - days)

            cursor.execute(
                "DELETE FROM extracted_emails WHERE extracted_at < ?",
                (cutoff_date,)
            )
            deleted_count = cursor.rowcount

            if deleted_count > 0:
                logger.info(f"已清理 {deleted_count} 条 {days} 天前的记录")

            return deleted_count

    def clear_all_data(self) -> dict:
        """
        清空所有数据（邮件记录和历史记录）

        Returns:
            dict: 清理统计信息
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 获取清理前的统计
            cursor.execute("SELECT COUNT(*) as count FROM extracted_emails")
            emails_count = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(*) as count FROM extraction_history")
            history_count = cursor.fetchone()['count']

            # 清空表
            cursor.execute("DELETE FROM extracted_emails")
            cursor.execute("DELETE FROM extraction_history")

            # 重置自增ID序列
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='extracted_emails'")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='extraction_history'")

            logger.warning(f"已清空所有数据：{emails_count} 条邮件记录，{history_count} 条历史记录")

            return {
                'emails_deleted': emails_count,
                'history_deleted': history_count
            }
