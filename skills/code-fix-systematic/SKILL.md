---
name: code-fix-systematic
description: 系统性代码修复工具，提供全局搜索、批量修复、验证测试、回归检查的完整流程，避免零散修改导致的问题
homepage: https://github.com/tuantuan-assistant/code-fix-systematic
metadata: {"openclaw":{"emoji":"🔧"}}
---

# Code Fix Systematic - 系统性代码修复工具 🔧

## 技能描述

专门用于**系统性、批量、安全**地修复代码问题，避免零散修改导致的顾此失彼。

**核心价值**：
- ✅ 全局搜索，不遗漏任何位置
- ✅ 批量修复，一次性解决所有问题
- ✅ 自动验证，确保修复生效
- ✅ 回归测试，确保不引入新问题
- ✅ 完整备份，随时可回滚

---

## 核心功能

### 1. **全局代码分析器**

```bash
/code-analyze <pattern> --path <directory>
```

**功能**：
- 搜索整个代码库中所有匹配的模式
- 生成问题报告（位置、上下文、影响范围）
- 评估修复优先级和风险

**示例**：
```bash
# 查找所有 tc.get() 调用
/code-analyze "tc\.get\(" --path ~/.hermes/hermes-agent/agent/

# 查找所有字典访问改为对象访问的位置
/code-analyze "\.get\(\"function\"" --path ~/.hermes/hermes-agent/
```

**输出**：
```
发现 6 处问题：
  1. conversation_loop.py:807 - tc.get("function", {}).get("name")
  2. conversation_loop.py:809 - tc.get("function", {}).get("arguments")
  3. conversation_loop.py:901 - tc.get("function", {}).get("name")
  ...

影响范围：
  - 文件：1 个
  - 函数：3 个
  - 调用点：6 个
```

### 2. **批量修复引擎**

```bash
/code-fix --pattern <old> --replacement <new> --path <directory> --dry-run
```

**功能**：
- 批量替换所有匹配的代码
- 支持正则表达式
- 支持预览模式（--dry-run）
- 自动处理转义和引号

**示例**：
```bash
# 预览修复
/code-fix --pattern 'tc\.get\("function", \{\}\)\.get\("name"\)' \
          --replacement 'tc.function.name' \
          --path ~/.hermes/hermes-agent/agent/ \
          --dry-run

# 执行修复
/code-fix --pattern 'tc\.get\("function", \{\}\)\.get\("name"\)' \
          --replacement 'tc.function.name' \
          --path ~/.hermes/hermes-agent/agent/
```

### 3. **代码验证器**

```bash
/code-verify <file> --syntax --imports --runtime
```

**功能**：
- 语法检查（Python/JavaScript 等）
- 导入检查
- 运行时验证（如果可能）

**示例**：
```bash
# 验证修复后的文件
/code-verify ~/.hermes/hermes-agent/agent/conversation_loop.py --syntax

# 完整验证
/code-verify ~/.hermes/hermes-agent/agent/conversation_loop.py --syntax --imports --runtime
```

### 4. **回归测试套件**

```bash
/code-test --suite <test_suite> --path <directory>
```

**功能**：
- 运行现有测试套件
- 检查是否引入新错误
- 生成测试报告

**示例**：
```bash
# 运行 Hermes 测试
/code-test --suite hermes_tests --path ~/.hermes/hermes-agent/

# 运行特定模块测试
/code-test --suite conversation_loop_tests --path ~/.hermes/hermes-agent/agent/
```

### 5. **备份和回滚系统**

```bash
/code-backup create <label>
/code-backup list
/code-backup restore <label>
```

**功能**：
- 创建带标签的备份
- 列出所有备份
- 一键回滚到任意备份点

**示例**：
```bash
# 修复前创建备份
/code-backup create "before_tc_get_fix"

# 列出备份
/code-backup list

# 回滚
/code-backup restore "before_tc_get_fix"
```

### 6. **影响分析报告**

```bash
/code-impact <pattern> --path <directory> --report
```

**功能**：
- 分析修改的影响范围
- 识别依赖关系
- 生成详细报告

**输出示例**：
```
影响分析报告
============

修改模式：tc.get("function") -> tc.function

影响文件：
  1. conversation_loop.py (6 处修改)
     - _handle_tool_call() 函数
     - _process_assistant_message() 函数
     - _run_conversation() 函数

依赖检查：
  ✅ 无外部依赖
  ✅ 无 API 变更
  ⚠️  需要清理 Python 缓存

风险评估：低风险
  - 修改范围：局部
  - 向后兼容：是
  - 测试覆盖：80%
```

---

## 完整修复流程

### 标准流程（推荐）

```bash
# 步骤 1: 创建备份
/code-backup create "before_fix_$(date +%Y%m%d)"

# 步骤 2: 分析问题
/code-analyze "tc\.get\(" --path <directory>

# 步骤 3: 生成修复方案
/code-impact "tc\.get\(" --path <directory> --report

# 步骤 4: 预览修复
/code-fix --pattern <old> --replacement <new> --path <directory> --dry-run

# 步骤 5: 执行修复
/code-fix --pattern <old> --replacement <new> --path <directory>

# 步骤 6: 验证语法
/code-verify <file> --syntax --imports

# 步骤 7: 清理缓存
find <directory> -type d -name __pycache__ -exec rm -rf {} +

# 步骤 8: 运行测试
/code-test --suite <test_suite> --path <directory>

# 步骤 9: 重启服务
<service> restart

# 步骤 10: 验证功能
<test_command>
```

---

## 使用示例

### 示例 1: 修复 Hermes 的 tc.get() 问题

```bash
# 1. 创建备份
/code-backup create "hermes_tc_fix_20260417"

# 2. 分析问题
/code-analyze "tc\.get\(" --path ~/.hermes/hermes-agent/agent/

# 输出：
# 发现 6 处问题
# - conversation_loop.py:807, 809, 901 (3 处 tc.get("function"))
# - conversation_loop.py:674, 816, 900 (3 处 tc.get("id"))

# 3. 批量修复 tc.get("function")
/code-fix --pattern 'tc\.get\("function", \{\}\)\.get\("name"\)' \
          --replacement 'tc.function.name' \
          --path ~/.hermes/hermes-agent/agent/

/code-fix --pattern 'tc\.get\("function", \{\}\)\.get\("arguments"\)' \
          --replacement 'tc.function.arguments' \
          --path ~/.hermes/hermes-agent/agent/

# 4. 批量修复 tc.get("id")
/code-fix --pattern 'tc\.get\("id"\)' \
          --replacement 'getattr(tc, "id", None)' \
          --path ~/.hermes/hermes-agent/agent/

# 5. 验证修复
/code-verify ~/.hermes/hermes-agent/agent/conversation_loop.py --syntax

# 6. 验证无遗漏
/code-analyze "tc\.get\(" --path ~/.hermes/hermes-agent/agent/
# 输出：发现 0 处问题 ✅

# 7. 清理缓存
find ~/.hermes -type d -name __pycache__ -exec rm -rf {} +

# 8. 重启服务
hermes gateway restart

# 9. 测试功能
hermes --version
# 测试 Telegram 机器人
```

### 示例 2: 批量修改函数名

```bash
# 分析问题
/code-analyze "def old_function_name" --path ./project/

# 预览修复
/code-fix --pattern 'def old_function_name' \
          --replacement 'def new_function_name' \
          --path ./project/ \
          --dry-run

# 执行修复
/code-fix --pattern 'def old_function_name' \
          --replacement 'def new_function_name' \
          --path ./project/

# 验证
/code-verify ./project/ --syntax
```

---

## 检查清单

### 修复前检查清单

- [ ] 已创建备份（/code-backup create）
- [ ] 已分析问题范围（/code-analyze）
- [ ] 已生成影响报告（/code-impact）
- [ ] 已预览修复（--dry-run）
- [ ] 已通知相关人员（如果适用）

### 修复后检查清单

- [ ] 语法验证通过（/code-verify --syntax）
- [ ] 导入检查通过（/code-verify --imports）
- [ ] 测试套件通过（/code-test）
- [ ] 无遗漏问题（/code-analyze 确认 0 处）
- [ ] 缓存已清理
- [ ] 服务已重启
- [ ] 功能测试通过

---

## 最佳实践

### 1. 始终先备份

```bash
# 修复前必须创建备份
/code-backup create "before_<fix_name>_$(date +%Y%m%d)"
```

### 2. 使用预览模式

```bash
# 先预览，确认无误再执行
/code-fix --pattern <old> --replacement <new> --dry-run
```

### 3. 全局搜索，不遗漏

```bash
# 修复后再次搜索，确认无遗漏
/code-analyze <pattern> --path <directory>
# 应该输出：发现 0 处问题
```

### 4. 运行完整测试

```bash
# 修复后必须运行测试
/code-test --suite <full_suite>
```

### 5. 记录修复过程

```bash
# 记录修复日志
echo "修复时间：$(date)" >> fix_log.md
echo "修复模式：<old> -> <new>" >> fix_log.md
echo "影响文件：<files>" >> fix_log.md
echo "测试结果：<result>" >> fix_log.md
```

---

## 脚本模板

### 完整修复脚本模板

```bash
#!/bin/bash
# 系统性代码修复脚本模板

set -e  # 遇到错误立即退出

# 配置
PATTERN_OLD='tc\.get\("function"\)'
PATTERN_NEW='tc.function'
TARGET_PATH="$HOME/.hermes/hermes-agent/agent/"
BACKUP_LABEL="hermes_tc_fix_$(date +%Y%m%d)"

echo "======================================"
echo "系统性代码修复"
echo "======================================"

# 1. 创建备份
echo "[1/8] 创建备份..."
/code-backup create "$BACKUP_LABEL"

# 2. 分析问题
echo "[2/8] 分析问题..."
/code-analyze "$PATTERN_OLD" --path "$TARGET_PATH"

# 3. 预览修复
echo "[3/8] 预览修复..."
/code-fix --pattern "$PATTERN_OLD" --replacement "$PATTERN_NEW" \
          --path "$TARGET_PATH" --dry-run

# 4. 执行修复
echo "[4/8] 执行修复..."
/code-fix --pattern "$PATTERN_OLD" --replacement "$PATTERN_NEW" \
          --path "$TARGET_PATH"

# 5. 验证语法
echo "[5/8] 验证语法..."
/code-verify "$TARGET_PATH/conversation_loop.py" --syntax --imports

# 6. 确认无遗漏
echo "[6/8] 确认无遗漏..."
REMAINING=$(/code-analyze "$PATTERN_OLD" --path "$TARGET_PATH" | grep -c "发现" || echo 0)
if [ "$REMAINING" -eq 0 ]; then
    echo "  ✅ 无遗漏问题"
else
    echo "  ❌ 仍有 $REMAINING 处问题"
    exit 1
fi

# 7. 清理缓存
echo "[7/8] 清理缓存..."
find "$TARGET_PATH" -type d -name __pycache__ -exec rm -rf {} +

# 8. 运行测试
echo "[8/8] 运行测试..."
/code-test --suite hermes_tests --path "$TARGET_PATH"

echo ""
echo "======================================"
echo "修复完成！"
echo "======================================"
echo "备份标签：$BACKUP_LABEL"
echo ""
```

---

## 版本历史

- **v1.0.0** (2026-04-17) - 初始版本
  - ✅ 全局代码分析器
  - ✅ 批量修复引擎
  - ✅ 代码验证器
  - ✅ 回归测试套件
  - ✅ 备份和回滚系统
  - ✅ 影响分析报告
  - ✅ 完整修复流程
  - ✅ 检查清单
  - ✅ 最佳实践

---

*Created by 团团 based on systematic code fix requirements* 🔹
