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
                # 将 sqlite3.Row 转换为字典以支持 .get() 方法
                row_dict = dict(row)
                return ExtractedEmail(
                    id=row_dict['id'],
                    message_id=row_dict['message_id'],
                    subject=row_dict['subject'],
                    sender=row_dict['sender'],
                    rule_id=row_dict['rule_id'],
                    mail_date=row_dict.get('mail_date', ''),
                    extracted_at=datetime.fromisoformat(row_dict['extracted_at']) if row_dict.get('extracted_at') else None,
                    storage_path=row_dict['storage_path'],
                    attachment_count=row_dict['attachment_count'],
                    body_file_path=row_dict['body_file_path']
                )
            return None

    def get_existing_mail_dates(self) -> set:
        """
        获取所有已提取且文件存在的邮件发送时间集合
        自动删除文件不存在的记录（允许重新提取）

        Returns:
            set: 邮件发送时间的集合（用于快速去重检查）
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # 查询所有有 storage_path 或 body_file_path 的记录
            cursor.execute("""
                SELECT id, message_id, mail_date, storage_path, body_file_path
                FROM extracted_emails
                WHERE mail_date IS NOT NULL AND mail_date != ''
                AND (storage_path IS NOT NULL AND storage_path != ''
                     OR body_file_path IS NOT NULL AND body_file_path != '')
            """)

            existing_dates = set()
            records_to_delete = []  # 需要删除的记录（文件不存在）

            for row in cursor.fetchall():
                # 验证文件是否真实存在
                storage_path = row['storage_path']
                body_file_path = row['body_file_path']
                record_id = row['id']
                message_id = row['message_id']
                mail_date = row['mail_date']

                storage_exists = storage_path and Path(storage_path).exists()
                body_exists = body_file_path and Path(body_file_path).exists()

                if storage_exists or body_exists:
                    # 文件存在，添加到已提取集合
                    existing_dates.add(mail_date)
                else:
                    # 文件不存在，记录需要删除
                    records_to_delete.append((record_id, message_id, mail_date, storage_path, body_file_path))

            # 删除文件不存在的记录（允许重新提取）
            if records_to_delete:
                logger.warning(f"【数据库清理】发现 {len(records_to_delete)} 条记录的文件不存在，将删除记录以允许重新提取")
                for record_id, message_id, mail_date, storage_path, body_file_path in records_to_delete:
                    # 先删除关联的提取历史记录（使用 message_id 关联）
                    cursor.execute("""
                        DELETE FROM extraction_history
                        WHERE message_id = ?
                    """, (message_id,))

                    # 再删除主记录
                    cursor.execute("""
                        DELETE FROM extracted_emails
                        WHERE id = ?
                    """, (record_id,))
                    logger.info(f"【数据库清理】已删除记录 ID={record_id}, message_id={message_id}, mail_date={mail_date}（原路径：storage={storage_path}, body={body_file_path}）")

            logger.info(f"【数据库预检查】找到 {len(existing_dates)} 个已提取且文件存在的邮件")
            if records_to_delete:
                logger.info(f"【数据库清理】已删除 {len(records_to_delete)} 条文件不存在的记录，允许重新提取")
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
                    mail_date=dict(row).get('mail_date', ''),
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

    def clean_invalid_records(self) -> int:
        """
        清理所有文件不存在的记录（允许重新提取）
        这是一个手动清理方法，可以强制删除所有无效记录

        Returns:
            int: 删除的记录数
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 查询所有记录
            cursor.execute("""
                SELECT id, message_id, mail_date, storage_path, body_file_path
                FROM extracted_emails
            """)

            records_to_delete = []
            for row in cursor.fetchall():
                record_id = row['id']
                message_id = row['message_id']
                mail_date = row['mail_date']
                storage_path = row['storage_path']
                body_file_path = row['body_file_path']

                # 检查文件是否存在
                storage_exists = storage_path and Path(storage_path).exists()
                body_exists = body_file_path and Path(body_file_path).exists()

                # 如果两个路径都为空或者文件不存在，则删除记录
                if not storage_exists and not body_exists:
                    records_to_delete.append((record_id, message_id, mail_date))

            # 删除无效记录
            deleted_count = 0
            for record_id, message_id, mail_date in records_to_delete:
                # 先删除关联的提取历史记录（使用 message_id 关联）
                cursor.execute("""
                    DELETE FROM extraction_history
                    WHERE message_id = ?
                """, (message_id,))

                # 再删除主记录
                cursor.execute("""
                    DELETE FROM extracted_emails
                    WHERE id = ?
                """, (record_id,))
                deleted_count += 1
                logger.info(f"【手动清理】已删除无效记录 ID={record_id}, message_id={message_id}, mail_date={mail_date}")

            if deleted_count > 0:
                logger.info(f"【手动清理】总共删除了 {deleted_count} 条无效记录")
            else:
                logger.info(f"【手动清理】没有发现无效记录")

            return deleted_count

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
