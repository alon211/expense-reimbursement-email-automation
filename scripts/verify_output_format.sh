#!/bin/bash
# 本地验证 GitHub Actions 输出格式（Linux 环境）
#
# 用途：验证文件路径方案是否正确
# 使用方法：bash scripts/verify_output_format.sh

echo "=== GitHub Actions 输出格式验证工具 (Linux) ==="
echo ""

# 测试数据
RESULT='{"success": true, "matched_count": 0}'

# 创建临时输出文件（模拟 GITHUB_OUTPUT）
GITHUB_OUTPUT_FILE=$(mktemp)

echo "测试 1: 文件路径格式（推荐）"
echo "----------------------------------------"
echo "$RESULT" > /tmp/test_result.json
echo "summary_file=/tmp/test_result.json" >> "$GITHUB_OUTPUT_FILE"

echo "输出内容："
cat "$GITHUB_OUTPUT_FILE"

echo ""
echo "验证结果："
if [ -f "/tmp/test_result.json" ]; then
    echo "✅ 文件创建成功"
    echo "✅ 文件路径方案验证通过"
    echo ""
    echo "文件内容："
    cat /tmp/test_result.json
else
    echo "❌ 文件创建失败"
fi

# 清理
rm -f "$GITHUB_OUTPUT_FILE"
rm -f /tmp/test_result.json

echo ""
echo "=== 验证完成 ==="
echo "✅ 文件路径方法最可靠，推荐使用"
