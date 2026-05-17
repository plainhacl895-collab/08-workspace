---
name: self-improving-agent
description: 自我改进技能，记录错误和学习到 markdown 文件，支持持续改进和知识提升
homepage: https://github.com/pskoett/self-improving-agent
metadata: {"openclaw":{"emoji":"📚"}}
---

# Self-Improving Agent - 自我改进技能 📚

## 技能描述

记录错误、学习和功能请求到 markdown 文件，支持持续改进。编码代理可以后续处理这些记录进行修复，重要学习会提升到项目记忆中。

**核心功能**：
- ✅ 记录错误到 ERRORS.md
- ✅ 记录学习到 LEARNINGS.md
- ✅ 记录功能请求到 FEATURE_REQUESTS.md
- ✅ 自动提升到项目记忆
- ✅ 支持跨会话共享

---

## 📁 目录结构

```
~/.openclaw/workspace/
├── AGENTS.md              # 多代理工作流
├── SOUL.md                # 行为准则
├── TOOLS.md               # 工具使用
├── MEMORY.md              # 长期记忆
├── memory/                # 每日记忆文件
│   └── YYYY-MM-DD.md
└── .learnings/            # 本技能的日志文件
    ├── LEARNINGS.md       # 学习记录
    ├── ERRORS.md          # 错误记录
    └── FEATURE_REQUESTS.md # 功能请求
```

---

## 🚀 使用方法

### 记录错误

```markdown
## [ERR-20260419-001] command_name

**Logged**: 2026-04-19T14:00:00Z
**Priority**: high
**Status**: pending
**Area**: backend

### Summary
命令执行失败

### Error
实际错误信息

### Context
- 尝试的命令
- 使用的参数
- 环境详情

### Suggested Fix
可能的解决方案

### Metadata
- Reproducible: yes
- Related Files: path/to/file.ext
```

---

### 记录学习

```markdown
## [LRN-20260419-001] category

**Logged**: 2026-04-19T14:00:00Z
**Priority**: medium
**Status**: pending
**Area**: config

### Summary
一句话描述学到了什么

### Details
完整上下文：发生了什么，什么是错的，什么是正确的

### Suggested Action
具体的修复或改进建议

### Metadata
- Source: conversation
- Related Files: path/to/file.ext
- Tags: tag1, tag2
- Pattern-Key: simplify.config (可选)
```

---

### 记录功能请求

```markdown
## [FEAT-20260419-001] capability_name

**Logged**: 2026-04-19T14:00:00Z
**Priority**: medium
**Status**: pending
**Area**: frontend

### Requested Capability
用户想要做什么

### User Context
为什么需要，解决什么问题

### Complexity Estimate
simple | medium | complex

### Suggested Implementation
如何实现

### Metadata
- Frequency: first_time
```

---

## 📋 触发条件

### 自动记录场景

| 场景 | 记录到 | 类别 |
|------|--------|------|
| 命令执行失败 | ERRORS.md | - |
| 用户纠正你 | LEARNINGS.md | correction |
| 用户想要缺失功能 | FEATURE_REQUESTS.md | - |
| API/工具失败 | ERRORS.md | integration |
| 知识过时 | LEARNINGS.md | knowledge_gap |
| 发现更好方法 | LEARNINGS.md | best_practice |

---

### 对话触发词

**纠正**：
- "不对，应该是..."
- "实际上..."
- "你错了..."
- "那个过时了..."

**功能请求**：
- "你能不能也..."
- "我希望你可以..."
- "有没有办法..."
- "为什么你不能..."

**知识差距**：
- 用户提供你不知道的信息
- 文档过时
- API 行为与理解不同

---

## 🎯 优先级指南

| 优先级 | 使用场景 |
|--------|---------|
| **critical** | 阻塞核心功能、数据丢失风险、安全问题 |
| **high** | 重大影响、影响常用工作流、重复问题 |
| **medium** | 中等影响、存在变通方案 |
| **low** | 轻微不便、边缘情况、锦上添花 |

---

## 📍 区域标签

| 区域 | 范围 |
|------|------|
| **frontend** | UI、组件、客户端代码 |
| **backend** | API、服务、服务器端代码 |
| **infra** | CI/CD、部署、Docker、云 |
| **tests** | 测试文件、测试工具、覆盖率 |
| **docs** | 文档、注释、README |
| **config** | 配置文件、环境、设置 |

---

## 📤 提升到项目记忆

### 何时提升

- ✅ 学习适用于多个文件/功能
- ✅ 任何贡献者（人类或 AI）都应知道的知识
- ✅ 防止重复错误
- ✅ 记录项目特定约定

### 提升目标

| 目标 | 内容 |
|------|------|
| **SOUL.md** | 行为准则、沟通风格、原则 |
| **AGENTS.md** | 代理特定工作流、工具使用模式 |
| **TOOLS.md** | 工具功能、使用模式、集成问题 |
| **MEMORY.md** | 长期记忆 |

---

### 提升示例

**学习（详细）**：
```markdown
项目使用 pnpm workspaces。尝试 npm install 失败。
锁文件是 pnpm-lock.yaml。必须使用 pnpm install。
```

**在 AGENTS.md（简洁）**：
```markdown
## 构建和依赖
- 包管理器：pnpm（不是 npm）- 使用 `pnpm install`
```

---

## 🔄 ID 生成规则

**格式**: `TYPE-YYYYMMDD-XXX`

- **TYPE**: LRN (学习), ERR (错误), FEAT (功能)
- **YYYYMMDD**: 当前日期
- **XXX**: 序号或随机 3 字符

**示例**:
- `LRN-20260419-001`
- `ERR-20260419-A3F`
- `FEAT-20260419-002`

---

## ✅ 解决条目

当问题修复后，更新条目：

1. 更改 **Status**: `pending` → `resolved`
2. 添加解决块：

```markdown
### Resolution
- **Resolved**: 2026-04-20T09:00:00Z
- **Commit/PR**: abc123 或 #42
- **Notes**: 简要描述完成的工作
```

**其他状态值**：
- `in_progress` - 正在进行
- `wont_fix` - 决定不修复（在 Resolution 中说明原因）
- `promoted` - 已提升到项目记忆

---

## 🔍 重复模式检测

如果记录类似现有条目的内容：

1. **先搜索**: `grep -r "keyword" .learnings/`
2. **链接条目**: 添加 `**See Also**: ERR-20260419-001`
3. **提升优先级**: 如果问题重复出现
4. **考虑系统修复**: 重复问题通常表示：
   - 缺少文档 → 提升到项目记忆
   - 缺少自动化 → 添加到 AGENTS.md
   - 架构问题 → 创建技术债务工单

---

## 📊 定期审查

### 审查时机

- ✅ 开始新主要任务前
- ✅ 完成功能后
- ✅ 在有过去学习的区域工作时
- ✅ 开发期间每周

### 快速状态检查

```bash
# 统计待处理项目
grep -h "Status\*\*: pending" .learnings/*.md | wc -l

# 列出高优先级待处理项目
grep -B5 "Priority\*\*: high" .learnings/*.md | grep "^## \["

# 查找特定区域的学习
grep -l "Area\*\*: backend" .learnings/*.md
```

---

## 📝 最佳实践

1. ✅ **立即记录** - 问题发生后上下文最新鲜
2. ✅ **具体明确** - 未来代理需要快速理解
3. ✅ **包含复现步骤** - 特别是错误
4. ✅ **链接相关文件** - 使修复更容易
5. ✅ **建议具体修复** - 不只是"调查"
6. ✅ **使用一致类别** - 支持过滤
7. ✅ **积极提升** - 如果不确定，添加到项目记忆
8. ✅ **定期审查** - 过时的学习失去价值

---

## ⚠️ 注意事项

### 不记录的内容

- ❌ 密钥、令牌、私钥
- ❌ 环境变量
- ❌ 完整源码/配置文件
- ❌ 原始命令输出（除非用户明确要求）

### 推荐做法

- ✅ 简短摘要
- ✅ 脱敏摘录
- ✅ 关键信息优先

---

## 📋 使用示例

### 示例 1: 记录命令错误

**场景**: Excel 命令失败

**记录到** `.learnings/ERRORS.md`:
```markdown
## [ERR-20260419-001] excel-write

**Logged**: 2026-04-19T14:00:00Z
**Priority**: high
**Status**: pending
**Area**: config

### Summary
写入 Excel 跟进记录时文件被锁定

### Error
Excel 进程未关闭，无法写入

### Context
- 命令：write-followup
- 环境：Windows
- Excel 文件被其他进程占用

### Suggested Fix
1. 写入前检查并关闭 Excel 进程
2. 添加重试机制

### Metadata
- Reproducible: yes
- Related Files: tools/tuantuan_cli.py
```

---

### 示例 2: 记录学习

**场景**: 用户纠正缓存刷新逻辑

**记录到** `.learnings/LEARNINGS.md`:
```markdown
## [LRN-20260419-001] correction

**Logged**: 2026-04-19T14:30:00Z
**Priority**: medium
**Status**: pending
**Area**: config

### Summary
缓存应该在写入跟进后自动刷新

### Details
之前认为需要手动刷新，但用户指出写入后应该自动刷新。
修改 tuantuan_cli.py 在 write-followup 后自动调用 refresh。

### Suggested Action
修改所有写入操作后自动刷新缓存

### Metadata
- Source: user_feedback
- Related Files: tools/tuantuan_cli.py
- Tags: cache, auto-refresh
- Pattern-Key: auto-refresh.after-write
```

---

### 示例 3: 记录功能请求

**场景**: 用户想要批量写入跟进

**记录到** `.learnings/FEATURE_REQUESTS.md`:
```markdown
## [FEAT-20260419-001] batch-followup

**Logged**: 2026-04-19T15:00:00Z
**Priority**: medium
**Status**: pending
**Area**: frontend

### Requested Capability
批量写入多个客户的跟进记录

### User Context
每天需要给多个客户写跟进，一个一个写太慢

### Complexity Estimate
medium

### Suggested Implementation
添加 --clients 参数支持多客户：
write-followup --clients "刘先生，李女士" --content "内容" --date 2026-04-19

### Metadata
- Frequency: recurring
- Related Features: write-followup
```

---

## 🎯 状态值说明

| 状态 | 说明 |
|------|------|
| **pending** | 待处理 |
| **in_progress** | 正在进行 |
| **resolved** | 已解决 |
| **promoted** | 已提升到项目记忆 |
| **wont_fix** | 决定不修复 |

---

## 🔗 相关链接

- [原始仓库](https://github.com/pskoett/self-improving-agent)
- [ClawHub 页面](https://clawhub.ai/pskoett/self-improving-agent)
- [Agent Skills 规范](https://agentskills.io/specification)

---

*Remade for OpenClaw from original repo* 🔹
