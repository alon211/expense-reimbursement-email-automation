#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独立的邮件提取脚本（用于GitHub Actions）
不依赖main.py的循环逻辑，单次执行
"""
import sys
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.rule_loader import RuleLoader
from core.email_fetcher import fetch_reimbursement_mails
from core.database import DatabaseManager
from config.settings import EXTRACT_ROOT_DIR, PARSE_RULES_JSON_PATH

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='邮件提取脚本')
    parser.add_argument('--output-dir', default=None, help='输出目录（默认使用EXTRACT_ROOT_DIR）')

    args = parser.parse_args()

    # 设置输出目录
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = Path(EXTRACT_ROOT_DIR)

    logger.info(f"📧 开始提取邮件（使用 JSON 配置的时间范围）...")
    logger.info(f"📁 输出目录: {output_dir}")

    try:
        # 创建输出目录
        output_dir.mkdir(parents=True, exist_ok=True)

        # 初始化数据库
        db_path = output_dir / "data.db"
        db = DatabaseManager(str(db_path))
        logger.info(f"✅ 数据库初始化成功: {db_path}")

        # 执行提取
        matched_mails = fetch_reimbursement_mails(
            logger_instance=logger,
            db_manager=db
        )

        # 生成结果
        result = {
            "success": True,
            "executed_at": datetime.now().isoformat(),
            "output_dir": str(output_dir),
            "matched_count": len(matched_mails),
            "mails": [
                {
                    "message_id": m.get("message_id"),
                    "subject": m.get("subject"),
                    "sender": m.get("sender"),
                    "mail_date": m.get("date"),
                    "rule_id": m.get("matched_rules", [None])[0].rule_id if m.get("matched_rules") else None,
                    "rule_name": m.get("matched_rules", [None])[0].rule_name if m.get("matched_rules") else None
                }
                for m in matched_mails
            ],
            "db_stats": db.get_statistics(),
            "errors": []
        }

        # 输出结果（使用特殊标记包围）
        print("=== EXTRACTION_RESULT ===")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print("=== EXTRACTION_RESULT_END ===")

        logger.info(f"✅ 提取完成，共匹配 {len(matched_mails)} 封邮件")

        return 0 if result["success"] else 1

    except Exception as e:
        logger.error(f"❌ 提取失败: {e}", exc_info=True)
        result = {
            "success": False,
            "error": str(e),
            "executed_at": datetime.now().isoformat()
        }
        print("=== EXTRACTION_RESULT ===")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print("=== EXTRACTION_RESULT_END ===")
        return 1


if __name__ == "__main__":
    sys.exit(main())
