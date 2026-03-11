#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地工作流测试脚本
模拟GitHub Actions的执行逻辑，用于本地调试和验证
"""
import sys
import io
import json
import argparse
import tempfile
from pathlib import Path
from datetime import datetime

# Windows中文输出修复
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.logger_config import init_logger
from config.settings import (
    IMAP_HOST, IMAP_USER, IMAP_PASS,
    PARSE_RULES_JSON_PATH, LOG_DIR
)
from core.database import DatabaseManager
from core.rule_loader import RuleLoader
from core.email_fetcher import fetch_reimbursement_mails


def validate_environment(logger, args):
    """
    验证运行环境

    Returns:
        dict: 验证结果，包含 'valid', 'errors', 'warnings', 'output_dir'
    """
    result = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'output_dir': None
    }

    print("\n🔍 验证环境配置...")

    # 检查IMAP配置
    if not IMAP_HOST:
        result['errors'].append("IMAP_HOST未配置（请检查.env文件）")
    else:
        print(f"  ✅ IMAP_HOST: {IMAP_HOST}")

    if not IMAP_USER:
        result['errors'].append("IMAP_USER未配置（请检查.env文件）")
    else:
        print(f"  ✅ IMAP_USER: {IMAP_USER}")

    if not IMAP_PASS:
        result['errors'].append("IMAP_PASS未配置（请检查.env文件）")
    else:
        print(f"  ✅ IMAP_PASS: {'*' * len(IMAP_PASS)}")

    # 检查规则配置文件
    rules_path = Path(PARSE_RULES_JSON_PATH)
    if not rules_path.exists():
        result['errors'].append(f"规则配置文件不存在: {PARSE_RULES_JSON_PATH}")
    else:
        print(f"  ✅ 规则配置: {PARSE_RULES_JSON_PATH}")

        # 验证JSON格式
        try:
            with open(rules_path, 'r', encoding='utf-8') as f:
                rules_data = json.load(f)
            print(f"  ✅ 规则文件格式正确（包含{len(rules_data.get('rules', []))}条规则）")
        except json.JSONDecodeError as e:
            result['errors'].append(f"规则配置文件JSON格式错误: {e}")

    # 检查/创建输出目录
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        # 使用临时目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(tempfile.gettempdir()) / f"test_workflow_{timestamp}"

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"  ✅ 输出目录: {output_dir}")
    except Exception as e:
        result['errors'].append(f"无法创建输出目录: {e}")

    result['output_dir'] = output_dir

    # 检查日志目录
    log_dir = Path(LOG_DIR)
    if not log_dir.exists():
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            print(f"  ✅ 日志目录: {LOG_DIR}")
        except Exception as e:
            result['warnings'].append(f"无法创建日志目录: {e}")
    else:
        print(f"  ✅ 日志目录: {LOG_DIR}")

    result['valid'] = len(result['errors']) == 0

    return result


def execute_extraction(logger, args, env_result):
    """
    执行邮件提取流程

    Returns:
        dict: 执行结果
    """
    from core.database import DatabaseManager
    from core.rule_loader import RuleLoader

    print("\n⏳ 开始执行提取...")
    print("=" * 50)

    # 初始化数据库
    db_path = env_result['output_dir'] / "data.db"
    db = DatabaseManager(str(db_path))
    logger.info(f"数据库初始化成功: {db_path}")
    print(f"✅ 数据库初始化成功")

    # 加载规则
    rules_loader = RuleLoader(PARSE_RULES_JSON_PATH)
    enabled_rules = rules_loader.get_enabled_rules()
    logger.info(f"规则加载完成: {len(enabled_rules)}/{len(rules_loader.rules)}条启用")
    print(f"✅ 规则加载完成（{len(enabled_rules)}条启用）")

    # 解析规则ID过滤器
    rule_ids = None
    if args.rule_filter:
        rule_ids = [rid.strip() for rid in args.rule_filter.split(',')]
        logger.info(f"规则过滤: {rule_ids}")
        print(f"✅ 规则过滤: {', '.join(rule_ids)}")

    # 执行提取
    start_time = datetime.now()

    try:
        matched_mails = fetch_reimbursement_mails(
            logger_instance=logger,
            db_manager=db,
            rule_ids=rule_ids
        )
    except Exception as e:
        logger.error(f"提取失败: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'executed_at': start_time.isoformat()
        }

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    # 构建结果
    result = {
        'success': True,
        'executed_at': start_time.isoformat(),
        'duration_seconds': duration,
        'time_range_days': args.time_range_days,
        'matched_count': len(matched_mails),
        'mails': [],
        'errors': []
    }

    # 整理邮件信息
    for mail in matched_mails:
        rule_id = mail.get('matched_rules', [{}])[0].get('rule_id') if mail.get('matched_rules') else None
        rule_name = mail.get('matched_rules', [{}])[0].get('rule_name') if mail.get('matched_rules') else None

        mail_info = {
            'message_id': mail.get('message_id'),
            'subject': mail.get('subject'),
            'sender': mail.get('sender'),
            'date': mail.get('date'),
            'rule_id': rule_id,
            'rule_name': rule_name
        }
        result['mails'].append(mail_info)

    # 获取数据库统计
    try:
        stats = db.get_statistics()
        result['statistics'] = stats
    except Exception as e:
        logger.warning(f"获取数据库统计失败: {e}")
        result['statistics'] = {}

    return result


def generate_report(result, args, env_result):
    """
    生成测试报告（控制台 + JSON）
    """
    print("\n" + "=" * 50)
    print("📊 测试报告")
    print("=" * 50)

    # 执行摘要
    status_icon = "✅" if result['success'] else "❌"
    status_text = "成功" if result['success'] else "失败"
    print(f"执行状态: {status_icon} {status_text}")
    print(f"执行时间: {result.get('executed_at', 'N/A')}")
    print(f"总耗时: {result.get('duration_seconds', 0):.1f}秒")
    print(f"匹配邮件: {result.get('matched_count', 0)}封")

    # 匹配邮件列表
    mails = result.get('mails', [])
    if mails:
        print(f"\n📧 匹配邮件列表:")
        for idx, mail in enumerate(mails, 1):
            print(f"\n  {idx}. {mail['subject']}")
            print(f"     发件人: {mail['sender']}")
            if mail.get('rule_id'):
                print(f"     规则: {mail['rule_id']} ({mail['rule_name']})")
            print(f"     日期: {mail['date']}")
    else:
        print("\n📧 没有匹配的邮件")

    # 数据库统计
    stats = result.get('statistics', {})
    if stats:
        print(f"\n💾 数据库统计:")
        print(f"  已提取邮件: {stats.get('total_extracted', 0)}条")
        print(f"  提取历史: {stats.get('total_history', 0)}条")

    # 错误信息
    errors = result.get('errors', [])
    if errors:
        print(f"\n❌ 错误信息:")
        for error in errors:
            print(f"  - {error}")

    # 保存JSON报告
    report_file = env_result['output_dir'] / "test_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 测试完成")
    print(f"📁 详细报告: {report_file}")
    print(f"📁 输出目录: {env_result['output_dir']}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='本地工作流测试脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例用法:
  # 使用3天时间范围测试
  python scripts/test_workflow_locally.py --time-range-days 3

  # 只测试特定规则
  python scripts/test_workflow_locally.py --rule-filter rule_003

  # 详细输出模式
  python scripts/test_workflow_locally.py --verbose

  # 干运行（只验证，不实际提取）
  python scripts/test_workflow_locally.py --dry-run

  # 指定输出目录
  python scripts/test_workflow_locally.py --output-dir ./my_test
        '''
    )

    parser.add_argument(
        '--time-range-days',
        type=int,
        default=3,
        help='搜索时间范围（天），默认3'
    )
    parser.add_argument(
        '--rule-filter',
        type=str,
        default=None,
        help='规则ID过滤器（逗号分隔），默认全部'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default=None,
        help='输出目录（默认使用临时目录）'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='详细输出模式'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='干运行模式（只验证配置，不实际提取）'
    )

    args = parser.parse_args()

    print("🔧 本地工作流测试脚本")
    print("=" * 50)
    print(f"📋 配置信息:")
    print(f"  时间范围: {args.time_range_days}天")
    print(f"  规则过滤: {args.rule_filter or '全部'}")
    print(f"  详细模式: {'是' if args.verbose else '否'}")
    print(f"  干运行: {'是' if args.dry_run else '否'}")

    try:
        # 1. 初始化日志系统
        logger, log_file = init_logger()
        logger.info("=" * 50)
        logger.info("本地工作流测试脚本启动")
        logger.info(f"时间范围: {args.time_range_days}天")
        logger.info(f"规则过滤: {args.rule_filter or '全部'}")
        logger.info("=" * 50)

        print(f"\n📁 日志文件: {log_file}")

        # 2. 验证环境
        env_result = validate_environment(logger, args)

        if not env_result['valid']:
            print("\n❌ 环境验证失败:")
            for error in env_result['errors']:
                print(f"  - {error}")
            return 1

        if env_result['warnings']:
            print("\n⚠️  警告:")
            for warning in env_result['warnings']:
                print(f"  - {warning}")

        if args.dry_run:
            print("\n✅ 干运行模式：环境验证通过，跳过实际提取")
            return 0

        # 3. 执行提取
        result = execute_extraction(logger, args, env_result)

        # 4. 生成报告
        generate_report(result, args, env_result)

        return 0 if result['success'] else 1

    except KeyboardInterrupt:
        print("\n\n⚠️  用户手动终止程序")
        return 130
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
