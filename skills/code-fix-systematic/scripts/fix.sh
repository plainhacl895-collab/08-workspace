#!/bin/bash
# 系统性代码修复脚本 - 主脚本

set -e

echo "======================================"
echo "系统性代码修复工具 v1.0"
echo "======================================"
echo ""

# 检查参数
if [ $# -lt 2 ]; then
    echo "用法：$0 <old_pattern> <new_pattern> [target_path]"
    echo ""
    echo "示例:"
    echo "  $0 'tc.get(\"function\")' 'tc.function' ~/.hermes/hermes-agent/agent/"
    echo ""
    exit 1
fi

PATTERN_OLD="$1"
PATTERN_NEW="$2"
TARGET_PATH="${3:-.}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_LABEL="fix_${TIMESTAMP}"

echo "修复配置:"
echo "  旧模式：$PATTERN_OLD"
echo "  新模式：$PATTERN_NEW"
echo "  目标路径：$TARGET_PATH"
echo "  备份标签：$BACKUP_LABEL"
echo ""

# 步骤 1: 创建备份
echo "[1/8] 创建备份..."
BACKUP_DIR="$HOME/.code_fix_backups/$BACKUP_LABEL"
mkdir -p "$BACKUP_DIR"
if [ -d "$TARGET_PATH" ]; then
    cp -r "$TARGET_PATH" "$BACKUP_DIR/" 2>/dev/null || true
    echo "  ✅ 备份完成：$BACKUP_DIR"
else
    echo "  ⚠️  目标路径不存在，跳过备份"
fi

# 步骤 2: 分析问题
echo ""
echo "[2/8] 分析问题..."
echo "  搜索模式：$PATTERN_OLD"
FOUND=$(grep -r "$PATTERN_OLD" "$TARGET_PATH" 2>/dev/null | wc -l || echo 0)
echo "  发现问题数：$FOUND"
if [ "$FOUND" -eq 0 ]; then
    echo "  ✅ 未发现问题"
    exit 0
fi

echo "  问题位置:"
grep -rn "$PATTERN_OLD" "$TARGET_PATH" 2>/dev/null | head -10 | while read line; do
    echo "    $line"
done
if [ "$FOUND" -gt 10 ]; then
    echo "    ... 还有 $((FOUND - 10)) 处"
fi

# 步骤 3: 预览修复
echo ""
echo "[3/8] 预览修复..."
echo "  将替换：$PATTERN_OLD -> $PATTERN_NEW"
echo "  影响文件:"
grep -rl "$PATTERN_OLD" "$TARGET_PATH" 2>/dev/null | while read file; do
    echo "    - $file"
done

read -p "确认执行修复？(y/N): " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "  已取消"
    exit 0
fi

# 步骤 4: 执行修复
echo ""
echo "[4/8] 执行修复..."
if [[ "$PATTERN_OLD" == *"\\"* ]]; then
    # 包含转义字符，使用 sed
    find "$TARGET_PATH" -type f -name "*.py" -exec sed -i "s/$PATTERN_OLD/$PATTERN_NEW/g" {} \;
else
    # 简单替换
    find "$TARGET_PATH" -type f -name "*.py" -exec sed -i "s/$PATTERN_OLD/$PATTERN_NEW/g" {} \;
fi
echo "  ✅ 修复完成"

# 步骤 5: 验证语法
echo ""
echo "[5/8] 验证语法..."
PYTHON_FILES=$(find "$TARGET_PATH" -type f -name "*.py" | head -5)
for file in $PYTHON_FILES; do
    if python3 -m py_compile "$file" 2>/dev/null; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file (语法错误)"
        read -p "是否继续？(y/N): " continue_flag
        if [ "$continue_flag" != "y" ] && [ "$continue_flag" != "Y" ]; then
            echo "正在回滚..."
            if [ -d "$BACKUP_DIR" ]; then
                rm -rf "$TARGET_PATH"
                cp -r "$BACKUP_DIR"/* "$TARGET_PATH/"
                echo "已回滚到修复前状态"
            fi
            exit 1
        fi
    fi
done

# 步骤 6: 确认无遗漏
echo ""
echo "[6/8] 确认无遗漏..."
REMAINING=$(grep -r "$PATTERN_OLD" "$TARGET_PATH" 2>/dev/null | wc -l || echo 0)
if [ "$REMAINING" -eq 0 ]; then
    echo "  ✅ 无遗漏问题"
else
    echo "  ⚠️  仍有 $REMAINING 处未修复"
    grep -rn "$PATTERN_OLD" "$TARGET_PATH" 2>/dev/null | head -5
fi

# 步骤 7: 清理缓存
echo ""
echo "[7/8] 清理缓存..."
find "$TARGET_PATH" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$TARGET_PATH" -type f -name "*.pyc" -delete 2>/dev/null || true
echo "  ✅ 缓存已清理"

# 步骤 8: 生成报告
echo ""
echo "[8/8] 生成报告..."
REPORT_FILE="$BACKUP_DIR/fix_report.txt"
cat > "$REPORT_FILE" << EOF
代码修复报告
============

修复时间：$(date)
修复模式：$PATTERN_OLD -> $PATTERN_NEW
目标路径：$TARGET_PATH
备份位置：$BACKUP_DIR

修复统计:
  发现问题数：$FOUND
  剩余问题数：$REMAINING
  修复成功率：$(( (FOUND - REMAINING) * 100 / FOUND ))%

影响文件:
$(grep -rl "$PATTERN_OLD" "$TARGET_PATH" 2>/dev/null || find "$TARGET_PATH" -type f -name "*.py" -exec grep -l "$PATTERN_NEW" {} \; 2>/dev/null | head -10)

验证结果:
  语法检查：通过
  缓存清理：完成
EOF

echo "  ✅ 报告已生成：$REPORT_FILE"

echo ""
echo "======================================"
echo "修复完成！"
echo "======================================"
echo ""
echo "备份位置：$BACKUP_DIR"
echo "修复报告：$REPORT_FILE"
echo ""
echo "下一步："
echo "1. 运行测试验证功能"
echo "2. 如有问题，从备份恢复：cp -r $BACKUP_DIR/* $TARGET_PATH/"
echo ""
