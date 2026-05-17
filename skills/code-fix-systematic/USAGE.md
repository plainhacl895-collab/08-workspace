# Code Fix Systematic - 使用指南

## 📋 快速开始

### 方式 1: 使用 PowerShell 脚本（推荐）

```powershell
# 修复 Hermes 的 tc.get() 问题
.\fix-hermes-systematic.ps1
```

### 方式 2: 使用 WSL 脚本

```bash
# 分析问题
wsl -d Ubuntu bash ~/.openclaw/workspace/skills/code-fix-systematic/scripts/analyze.sh \
    'tc\.get\(' ~/.hermes/hermes-agent/agent/

# 执行修复
wsl -d Ubuntu bash ~/.openclaw/workspace/skills/code-fix-systematic/scripts/fix.sh \
    'tc\.get\("function"\)' 'tc.function' ~/.hermes/hermes-agent/agent/

# 验证修复
wsl -d Ubuntu bash ~/.openclaw/workspace/skills/code-fix-systematic/scripts/verify.sh \
    ~/.hermes/hermes-agent/agent/conversation_loop.py
```

---

## 🔧 完整修复流程（以 Hermes 为例）

### 步骤 1: 创建备份

```bash
wsl -d Ubuntu bash -c "
cp -r ~/.hermes/hermes-agent/agent/conversation_loop.py \
    ~/.hermes/hermes-agent/agent/conversation_loop.py.bak.$(date +%Y%m%d_%H%M%S)
"
```

### 步骤 2: 分析问题

```bash
wsl -d Ubuntu bash -c "
echo '=== 问题分析 ==='
grep -rn 'tc\.get\(' ~/.hermes/hermes-agent/agent/conversation_loop.py
"
```

**预期输出**：
```
=== 问题分析 ===
674:    "result": _results_by_id.get(tc.get("id")),
807:    tool_name = tc.get("function", {}).get("name", "unknown")
809:    tool_input = json.loads(tc.get("function", {}).get("arguments", "{}"))
816:    ... == tc.get("id"):
900:    ... tc.get("id") == ...
901:    ... tc.get("function", {}).get("name", "unknown")
```

### 步骤 3: 执行批量修复

```bash
wsl -d Ubuntu python3 -c "
file = '/home/huawei/.hermes/hermes-agent/agent/conversation_loop.py'
with open(file, 'r') as f:
    content = f.read()

# 修复 tc.get(\"function\", {})
content = content.replace('tc.get(\"function\", {})', 'getattr(tc, \"function\", {})')

# 修复 tc.get(\"id\")
content = content.replace('tc.get(\"id\")', 'getattr(tc, \"id\", None)')

with open(file, 'w') as f:
    f.write(content)

print('✅ 修复完成')
"
```

### 步骤 4: 验证无遗漏

```bash
wsl -d Ubuntu bash -c "
echo '=== 验证修复 ==='
REMAINING=$(grep -c 'tc\.get\(' ~/.hermes/hermes-agent/agent/conversation_loop.py || echo 0)
if [ \"\$REMAINING\" -eq 0 ]; then
    echo '✅ 无遗漏问题'
else
    echo \"⚠️  仍有 \$REMAINING 处未修复\"
    grep -n 'tc\.get\(' ~/.hermes/hermes-agent/agent/conversation_loop.py
fi
"
```

### 步骤 5: 清理缓存

```bash
wsl -d Ubuntu bash -c "
find ~/.hermes -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
echo '✅ 缓存已清理'
"
```

### 步骤 6: 重启服务

```bash
wsl -d Ubuntu bash -c "
~/.hermes/hermes-agent/venv/bin/hermes gateway restart
echo '✅ Gateway 已重启'
"
```

### 步骤 7: 测试功能

在 Telegram 中发送 `/reset` 然后发送 `你好` 测试。

---

## 📊 修复报告模板

```markdown
# 代码修复报告

## 修复信息
- **时间**: $(date)
- **修复模式**: tc.get() -> getattr(tc, ...)
- **目标文件**: conversation_loop.py
- **备份位置**: conversation_loop.py.bak.TIMESTAMP

## 修复统计
- **发现问题**: 6 处
- **已修复**: 6 处
- **剩余问题**: 0 处
- **修复成功率**: 100%

## 影响范围
- **文件**: 1 个
- **函数**: 3 个
- **调用点**: 6 个

## 验证结果
- ✅ 语法检查通过
- ✅ 导入检查通过
- ✅ 无遗漏问题
- ✅ 缓存已清理
- ✅ 服务已重启

## 测试建议
1. 发送 /reset 清除旧会话
2. 发送测试消息验证功能
3. 检查日志无新错误
```

---

## ⚠️ 注意事项

### 1. 始终先备份

```bash
# 修复前必须备份
cp file.py file.py.bak.$(date +%Y%m%d_%H%M%S)
```

### 2. 使用预览模式

```bash
# 先预览修复效果
grep -n 'pattern' file.py
# 确认无误再执行替换
```

### 3. 全局搜索

```bash
# 修复后再次搜索，确认无遗漏
grep -rn 'pattern' directory/
# 应该输出 0 处
```

### 4. 运行测试

```bash
# 修复后必须测试功能
hermes gateway restart
# 然后测试 Telegram 机器人
```

---

## 🎯 最佳实践

### 修复前

1. ✅ 创建备份
2. ✅ 分析问题范围
3. ✅ 评估影响
4. ✅ 通知相关人员（如果适用）

### 修复中

1. ✅ 使用批量替换
2. ✅ 预览修复效果
3. ✅ 记录修改内容

### 修复后

1. ✅ 验证语法
2. ✅ 确认无遗漏
3. ✅ 清理缓存
4. ✅ 运行测试
5. ✅ 生成报告

---

## 📚 相关文档

- **技能文档**: `workspace/skills/code-fix-systematic/SKILL.md`
- **修复脚本**: `workspace/skills/code-fix-systematic/scripts/`
- **备份目录**: `~/.code_fix_backups/`

---

**最后更新**: 2026-04-17 🔹
