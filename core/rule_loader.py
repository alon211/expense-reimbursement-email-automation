# -*- coding: utf-8 -*-
"""邮件解析规则加载模块

提供规则配置的加载、验证和查询功能。
"""
import json
import logging
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger("RuleLoader")


class Rule:
    """邮件解析规则类"""

    def __init__(self, rule_data: Dict):
        """
        初始化规则

        Args:
            rule_data: 规则配置字典
        """
        self.rule_id = rule_data.get("rule_id", "")
        self.rule_name = rule_data.get("rule_name", "")
        self.enabled = rule_data.get("enabled", False)
        self.description = rule_data.get("description", "")
        self.match_conditions = rule_data.get("match_conditions", {})
        self.extract_options = rule_data.get("extract_options", {})
        self.output_subdir = rule_data.get("output_subdir", "")

    def match(self, subject: str, sender: str, body: str) -> bool:
        """
        检查邮件是否匹配此规则

        Args:
            subject: 邮件主题
            sender: 发件人
            body: 邮件正文

        Returns:
            bool: 是否匹配
        """
        if not self.enabled:
            return False

        subject_lower = subject.lower()
        sender_lower = sender.lower()
        body_lower = body.lower()

        # 检查发件人匹配
        for keyword in self.match_conditions.get("sender_contains", []):
            if keyword.lower() in sender_lower:
                return True

        # 检查主题匹配
        for keyword in self.match_conditions.get("subject_contains", []):
            if keyword.lower() in subject_lower:
                return True

        # 检查正文匹配
        for keyword in self.match_conditions.get("body_contains", []):
            if keyword.lower() in body_lower:
                return True

        return False

    def should_extract_attachments(self) -> bool:
        """是否提取附件"""
        return self.extract_options.get("extract_attachments", False)

    def should_extract_body(self) -> bool:
        """是否提取正文"""
        return self.extract_options.get("extract_body", False)

    def should_extract_headers(self) -> bool:
        """是否提取邮件头"""
        return self.extract_options.get("extract_headers", False)

    def should_extract_archives(self) -> bool:
        """是否解压压缩文件"""
        return self.extract_options.get("extract_archives", False)

    def get_archive_password(self) -> str:
        """获取压缩包密码"""
        return self.extract_options.get("archive_password", "")

    def get_allowed_archive_types(self) -> List[str]:
        """获取允许的压缩格式列表"""
        return self.extract_options.get("allowed_archive_types", [])

    def should_extract_nuonuo_invoice(self) -> bool:
        """是否提取诺诺网发票PDF"""
        return self.extract_options.get("extract_nuonuo_invoice", False)

    def get_nuonuo_anchor_text(self) -> str:
        """获取诺诺网链接锚点文字"""
        return self.extract_options.get("nuonuo_anchor_text", "点击链接查看发票：")

    def get_nuonuo_download_options(self) -> dict:
        """获取诺诺网下载选项"""
        return self.extract_options.get("nuonuo_download_options", {})


class RuleLoader:
    """规则加载器"""

    def __init__(self, rules_file_path: str):
        """
        初始化规则加载器

        Args:
            rules_file_path: 规则 JSON 文件路径
        """
        self.rules_file_path = Path(rules_file_path)
        self.parse_time_range_days = 30
        self.rules: List[Rule] = []
        self._load_rules()

    def _load_rules(self):
        """加载并验证规则文件"""
        if not self.rules_file_path.exists():
            logger.warning(f"规则文件不存在：{self.rules_file_path}")
            return

        try:
            with open(self.rules_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 加载全局配置
            self.parse_time_range_days = data.get("parse_time_range_days", 30)

            # 加载规则列表
            rules_data = data.get("rules", [])
            self.rules = [Rule(rule_data) for rule_data in rules_data]

            logger.info(f"成功加载 {len(self.rules)} 条规则，解析时间范围：{self.parse_time_range_days} 天")

        except json.JSONDecodeError as e:
            logger.error(f"规则文件 JSON 格式错误：{e}")
        except Exception as e:
            logger.error(f"加载规则文件失败：{e}")

    def get_enabled_rules(self) -> List[Rule]:
        """获取所有启用的规则"""
        return [rule for rule in self.rules if rule.enabled]

    def get_rule_by_id(self, rule_id: str) -> Optional[Rule]:
        """根据 ID 获取规则"""
        for rule in self.rules:
            if rule.rule_id == rule_id:
                return rule
        return None

    def match_rules(self, subject: str, sender: str, body: str) -> List[Rule]:
        """
        匹配所有符合条件的规则

        Args:
            subject: 邮件主题
            sender: 发件人
            body: 邮件正文

        Returns:
            匹配的规则列表
        """
        return [
            rule for rule in self.get_enabled_rules()
            if rule.match(subject, sender, body)
        ]

    def reload(self):
        """重新加载规则文件"""
        logger.info("重新加载规则文件...")
        self._load_rules()
