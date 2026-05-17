#!/bin/bash
# 代码分析脚本

echo "======================================"
echo "代码分析工具"
echo "======================================"
echo ""

if [ $# -lt 1 ]; then
    echo "用法：$0 <pattern> [target_path]"
    echo ""
    echo "示例:"
    echo "  $0 'tc\.get\(' ~/.hermes/hermes-agent/agent/"
    echo ""
    exit 1
fi

PATTERN="$1"
TARGET_PATH="${2:-.}"

echo "分析配置:"
echo "  搜索模式：$PATTERN"
echo "  目标路径：$TARGET_PATH"
echo ""

# 统计
echo "[1/3] 统计问题..."
TOTAL=$(grep -r "$PATTERN" "$TARGET_PATH" --include="*.py" 2>/dev/null | wc -l || echo 0)
echo "  发现问题总数：$TOTAL"

# 文件分布
echo ""
echo "[2/3] 文件分布..."
echo "  影响文件:"
grep -rl "$PATTERN" "$TARGET_PATH" --include="*.py" 2>/dev/null | while read file; do
    COUNT=$(grep -c "$PATTERN" "$file" 2>/dev/null || echo 0)
    echo "    - $file ($COUNT 处)"
done

# 详细位置
echo ""
echo "[3/3] 详细位置..."
if [ "$TOTAL" -le 20 ]; then
    grep -rn "$PATTERN" "$TARGET_PATH" --include="*.py" 2>/dev/null | while read line; do
        echo "  $line"
    done
else
    echo "  问题较多，显示前 20 个:"
    grep -rn "$PATTERN" "$TARGET_PATH" --include="*.py" 2>/dev/null | head -20 | while read line; do
        echo "  $line"
    done
    echo "  ... 还有 $((TOTAL - 20)) 处"
fi

echo ""
echo "======================================"
echo "分析完成"
echo "======================================"
echo ""

if [ "$TOTAL" -eq 0 ]; then
    echo "✅ 未发现问题"
else
    echo "⚠️  发现 $TOTAL 处问题"
    echo ""
    echo "建议使用 /code-fix 进行修复"
fi
