#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Actions环境适配器
处理GitHub Secrets和环境变量
"""
import os
import sys


def setup_github_environment():
    """设置GitHub Actions环境，验证必需的Secrets"""

    # 从GitHub Secrets读取配置
    required_secrets = [
        'IMAP_HOST',
        'IMAP_USER',
        'IMAP_PASS'
    ]

    optional_secrets = [
        'DINGTALK_WEBHOOK',
        'DINGTALK_SECRET'
    ]

    # 验证必需配置
    missing = []
    for secret in required_secrets:
        if not os.environ.get(secret):
            missing.append(secret)

    if missing:
        print(f"❌ 缺少必需的Secrets: {', '.join(missing)}")
        print("\n请在GitHub仓库设置中添加以下Secrets：")
        print("1. 进入仓库 → Settings → Secrets and variables → Actions")
        print("2. 点击 'New repository secret'")
        for secret in missing:
            if secret == 'IMAP_HOST':
                print(f"   - 名称: {secret}, 值: 如 imap.qq.com")
            elif secret == 'IMAP_USER':
                print(f"   - 名称: {secret}, 值: 如 your_email@qq.com")
            elif secret == 'IMAP_PASS':
                print(f"   - 名称: {secret}, 值: 邮箱授权码（不是登录密码）")
        sys.exit(1)

    print(f"✅ GitHub Secrets配置验证通过")

    # 显示配置信息（脱敏）
    imap_host = os.environ.get('IMAP_HOST', '')
    imap_user = os.environ.get('IMAP_USER', '')
    print(f"IMAP_HOST: {imap_host[:8]}... (已脱敏)")
    print(f"IMAP_USER: {imap_user[:3]}***@*** (已脱敏)")

    # 检查可选配置
    dingtalk_webhook = os.environ.get('DINGTALK_WEBHOOK', '')
    if dingtalk_webhook:
        print(f"✅ 钉钉通知已配置")
    else:
        print(f"⚠️  钉钉通知未配置（可选）")

    return True


def main():
    """主函数"""
    print("🔧 GitHub Actions环境适配器")
    print("=" * 50)

    success = setup_github_environment()

    if success:
        print("\n✅ 环境配置完成，可以开始提取邮件")
        return 0
    else:
        print("\n❌ 环境配置失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
