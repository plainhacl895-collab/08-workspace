#!/bin/bash
# 代码验证脚本

echo "======================================"
echo "代码验证工具"
echo "======================================"
echo ""

if [ $# -lt 1 ]; then
    echo "用法：$0 <file_or_directory>"
    echo ""
    echo "示例:"
    echo "  $0 ~/.hermes/hermes-agent/agent/conversation_loop.py"
    echo "  $0 ~/.hermes/hermes-agent/agent/"
    echo ""
    exit 1
fi

TARGET="$1"
ERRORS=0
WARNINGS=0

# 语法检查
echo "[1/3] 语法检查..."
if [ -d "$TARGET" ]; then
    FILES=$(find "$TARGET" -type f -name "*.py")
else
    FILES="$TARGET"
fi

for file in $FILES; do
    if [ -f "$file" ]; then
        if python3 -m py_compile "$file" 2>/dev/null; then
            echo "  ✅ $file"
        else
            echo "  ❌ $file (语法错误)"
            ERRORS=$((ERRORS + 1))
        fi
    fi
done

# 导入检查
echo ""
echo "[2/3] 导入检查..."
for file in $FILES; do
    if [ -f "$file" ]; then
        if python3 -c "import sys; sys.path.insert(0, '$(dirname $file)'); import $(basename $file .py)" 2>/dev/null; then
            echo "  ✅ $file"
        else
            echo "  ⚠️  $file (导入警告)"
            WARNINGS=$((WARNINGS + 1))
        fi
    fi
done

# 代码风格检查（如果有 pycodestyle）
echo ""
echo "[3/3] 代码风格检查..."
if command -v pycodestyle &> /dev/null; then
    pycodestyle "$TARGET" --max-line-length=120 --ignore=E501,W503 2>/dev/null | head -10 || true
else
    echo "  ℹ️  pycodestyle 未安装，跳过"
fi

echo ""
echo "======================================"
echo "验证完成"
echo "======================================"
echo ""
echo "错误数：$ERRORS"
echo "警告数：$WARNINGS"
echo ""

if [ "$ERRORS" -eq 0 ]; then
    echo "✅ 验证通过"
    exit 0
else
    echo "❌ 验证失败（$ERRORS 个错误）"
    exit 1
fi
