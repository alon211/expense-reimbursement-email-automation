#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试生产环境日志配置"""
import sys
import io
import os

# 设置标准输出编码为 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_production_logger():
    """测试生产环境日志配置"""
    print("=" * 60)
    print("测试生产环境日志配置")
    print("=" * 60)

    # 测试1：INFO 级别（生产环境）
    print("\n1. 测试 INFO 级别（生产环境）")
    print("-" * 40)

    # 临时修改环境变量
    original_log_level = os.environ.get('LOG_LEVEL')
    os.environ['LOG_LEVEL'] = 'INFO'

    # 重新导入以加载新的配置
    import importlib
    import config.settings
    importlib.reload(config.settings)

    from config.logger_config import init_logger
    logger, log_file = init_logger()

    print("\n--- 测试日志输出 ---")
    logger.debug("这条是 DEBUG 日志（文件中应该有，控制台不应该有）")
    logger.info("这条是 INFO 日志（文件中应该有，控制台不应该有）")
    logger.warning("这条是 WARNING 日志（文件中应该有，控制台不应该有）")
    logger.error("这条是 ERROR 日志（文件中应该有，控制台不应该有）")

    print("\n✅ 如果控制台只显示了初始化信息，而没有显示上述日志，说明生产环境配置正确")

    # 测试2：DEBUG 级别（开发环境）
    print("\n" + "=" * 60)
    print("2. 测试 DEBUG 级别（开发环境）")
    print("-" * 40)

    # 恢复环境变量或设置为 DEBUG
    os.environ['LOG_LEVEL'] = 'DEBUG'

    # 重新导入以加载新的配置
    importlib.reload(config.settings)

    from config.logger_config import init_logger as init_logger_debug
    logger_debug, log_file_debug = init_logger_debug()

    print("\n--- 测试日志输出 ---")
    logger_debug.debug("这条是 DEBUG 日志（控制台和文件都应该有）")
    logger_debug.info("这条是 INFO 日志（控制台和文件都应该有）")
    logger_debug.warning("这条是 WARNING 日志（控制台和文件都应该有）")
    logger_debug.error("这条是 ERROR 日志（控制台和文件都应该有）")

    print("\n✅ 如果控制台显示了所有日志，说明开发环境配置正确")

    # 恢复原始配置
    if original_log_level:
        os.environ['LOG_LEVEL'] = original_log_level
    elif 'LOG_LEVEL' in os.environ:
        del os.environ['LOG_LEVEL']

    print("\n" + "=" * 60)
    print("✅ 测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    test_production_logger()
