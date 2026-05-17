---
name: memory-setup
description: 配置持久化记忆系统，将代理从金鱼变成大象
homepage: https://clawhub.ai/jrbobbyhansen-pixel/memory-setup
metadata: {"openclaw":{"emoji":"🐘"}}
---

# Memory Setup - 记忆设置技能 🐘

## 技能描述

配置持久化记忆系统，让代理能够记住过去的工作、决策和偏好。

**核心功能**：
- ✅ 持久化记忆配置
- ✅ MEMORY.md 结构
- ✅ 日志系统
- ✅ 项目上下文
- ✅ 偏好存储
- ✅ 本地或云嵌入

---

## 🚀 快速设置

### 1. 启用记忆搜索

在 OpenClaw 配置中启用记忆搜索：

```json
{
  "memorySearch": {
    "enabled": true,
    "provider": "voyage",
    "sources": ["memory", "sessions"],
    "indexMode": "hot",
    "minScore": 0.3,
    "maxResults": 20
  }
}
```

---

### 2. 创建记忆结构

在 workspace 中创建：

```
workspace/
├── MEMORY.md          # 长期策划记忆
└── memory/
    ├── logs/          # 日志 (YYYY-MM-DD.md)
    ├── projects/      # 项目特定上下文
    ├── groups/        # 群聊上下文
    └── system/        # 偏好、设置笔记
```

---

### 3. 初始化 MEMORY.md

在 workspace 根目录创建 MEMORY.md：

```markdown
# MEMORY.md — Long-Term Memory

## About [User Name]
- Key facts, preferences, context

## Active Projects
- Project summaries and status

## Decisions & Lessons
- Important choices made
- Lessons learned

## Preferences
- Communication style
- Tools and workflows
```

---

## ⚙️ 配置选项详解

| 设置 | 用途 | 推荐值 |
|------|------|--------|
| **enabled** | 启用记忆搜索 | `true` |
| **provider** | 嵌入提供者 | `"voyage"` |
| **sources** | 索引源 | `["memory", "sessions"]` |
| **indexMode** | 索引模式 | `"hot"` (实时) |
| **minScore** | 相关性阈值 | `0.3` (越低结果越多) |
| **maxResults** | 最大片段数 | `20` |

---

## 📡 提供者选项

### 云提供者

- **voyage** - Voyage AI 嵌入（推荐）
- **openai** - OpenAI 嵌入

### 本地提供者

- **local** - 本地嵌入（无需 API）

---

## 📁 源选项

| 源 | 内容 |
|----|------|
| **memory** | MEMORY.md + memory/*.md 文件 |
| **sessions** | 过去的对话记录 |
| **both** | 完整上下文（推荐） |

---

## 📝 日志格式

每日创建 `memory/logs/YYYY-MM-DD.md`：

```markdown
# YYYY-MM-DD — Daily Log

## [Time] — [Event/Task]
- What happened
- Decisions made
- Follow-ups needed

## [Time] — [Another Event]
- Details
```

---

## 🧠 代理指令 (AGENTS.md)

在 AGENTS.md 中添加记忆回忆指令：

```markdown
## Memory Recall
Before answering questions about prior work, decisions, dates, people, preferences, or todos:
1. Run memory_search with relevant query
2. Use memory_get to pull specific lines if needed
3. If low confidence after search, say you checked
```

---

## 🔧 故障排除

### 记忆搜索不工作？

- ✅ 检查 `memorySearch.enabled: true` 在配置中
- ✅ 验证 MEMORY.md 存在于 workspace 根目录
- ✅ 重启网关：`openclaw gateway restart`

---

### 结果不相关？

- ✅ 降低 minScore 到 0.2 获取更多结果
- ✅ 增加 maxResults 到 30
- ✅ 检查记忆文件是否有有意义的内容

---

### 提供者错误？

- **Voyage**: 在环境变量中设置 `VOYAGE_API_KEY`
- **OpenAI**: 在环境变量中设置 `OPENAI_API_KEY`
- **本地**: 如果没有 API 密钥可用，使用 local 提供者

---

## ✅ 验证

测试记忆是否工作：

**用户**: "你记得关于 [过去话题] 的什么？"  
**代理**: [应该搜索记忆并返回相关上下文]

如果代理没有记忆，说明配置未应用。重启网关。

---

## 📊 完整配置示例

```json
{
  "memorySearch": {
    "enabled": true,
    "provider": "voyage",
    "sources": ["memory", "sessions"],
    "indexMode": "hot",
    "minScore": 0.3,
    "maxResults": 20
  },
  "workspace": "/path/to/your/workspace"
}
```

---

## 🎯 为什么重要

### 没有记忆：

- ❌ 代理在会话间忘记一切
- ❌ 重复问题，失去上下文
- ❌ 项目无连续性

### 有记忆：

- ✅ 回忆过去对话
- ✅ 了解你的偏好
- ✅ 跟踪项目历史
- ✅ 随时间建立关系

**金鱼 → 大象** 🐘

---

## 📋 使用场景

### 自动触发

- ✅ 用户询问过去的工作
- ✅ 用户询问决策历史
- ✅ 用户询问偏好
- ✅ 用户询问日期/人员
- ✅ 用户询问待办事项

---

### 手动查询

```bash
# 搜索记忆
memory_search --query "project setup"

# 获取特定行
memory_get --path "memory/2026-04-19.md" --from 10 --lines 5
```

---

## 📂 目录结构

### workspace 根目录

- **MEMORY.md** - 长期策划记忆
- **AGENTS.md** - 代理行为指令

### memory/ 目录

- **logs/** - 每日日志
- **projects/** - 项目上下文
- **groups/** - 群聊上下文
- **system/** - 系统偏好

---

## 🔐 安全考虑

### 数据存储

- ✅ 本地存储 - 数据在 workspace 内
- ✅ 无外部传输 - 除非使用云提供者
- ✅ 可选 API - 可完全离线使用

---

### API 密钥

- ⚠️ 如果使用云提供者需要密钥
- ✅ 通过环境变量设置
- ✅ 可使用 local 提供者避免

---

## 📚 参考链接

- [ClawHub 页面](https://clawhub.ai/jrbobbyhansen-pixel/memory-setup)
- [OpenClaw 配置文档](https://docs.openclaw.ai)
- [Memory Search API](https://docs.openclaw.ai/memory-search)

---

*Remade for OpenClaw from ClawHub* 🔹
