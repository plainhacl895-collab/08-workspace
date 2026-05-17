---
name: self-improving
description: 自我改进 + 主动代理技能，从纠正和反思中学习，知识随时间累积
homepage: https://clawhub.ai/ivangdavila/self-improving
metadata: {"openclaw":{"emoji":"🌱"}}
---

# Self-Improving + Proactive Agent 🌱

## 技能描述

从用户纠正和自我反思中学习，知识随时间累积而无需手动维护。

**核心功能**：
- ✅ 从纠正中学习
- ✅ 自我反思
- ✅ 分级存储（HOT/WARM/COLD）
- ✅ 自动提升/降级
- ✅ 冲突解决

---

## 📁 存储结构

```
~/self-improving/
├── memory.md          # HOT: ≤100 行，始终加载
├── index.md           # 主题索引
├── heartbeat-state.md # 心跳状态
├── projects/          # 每项目学习
├── domains/           # 领域特定（代码、写作等）
├── archive/           # COLD: 衰减模式
└── corrections.md     # 最后 50 条纠正日志
```

---

## 🎯 使用时机

- ✅ 用户纠正你或指出错误
- ✅ 完成重要工作后评估结果
- ✅ 注意到自己的输出可以更好
- ✅ 知识应该随时间累积

---

## 📊 学习信号

### 自动记录

#### 纠正 → 添加到 corrections.md

**触发词**：
- "不，那不对..."
- "实际上，应该是..."
- "你错了..."
- "我更喜欢 X，不是 Y"
- "记住我总是..."
- "我之前告诉过你..."
- "停止做 X"
- "你为什么总是..."

---

#### 偏好信号 → 添加到 memory.md

**触发词**：
- "我喜欢你..."
- "总是为我做 X"
- "从不做 Y"
- "我的风格是..."
- "对于 [项目]，使用..."

---

#### 模式候选 → 跟踪，3 次后提升

**信号**：
- 相同指令重复 3+ 次
- 工作流反复有效
- 用户赞扬特定方法

---

### 忽略（不记录）

- ❌ 一次性指令（"现在做 X"）
- ❌ 特定上下文（"在这个文件中..."）
- ❌ 假设（"如果..."）

---

## 🔄 自我反思

### 何时反思

- ✅ 完成多步骤任务后
- ✅ 收到反馈后（正面或负面）
- ✅ 修复 bug 或错误后
- ✅ 注意到输出可以更好时

---

### 反思格式

```markdown
CONTEXT: [任务类型]
REFLECTION: [我注意到的]
LESSON: [下次要做什么不同的]
```

**示例**：
```markdown
CONTEXT: 构建 Flutter UI
REFLECTION: 间距看起来不对，不得不重做
LESSON: 在展示给用户前检查视觉间距
```

---

## 📋 分级存储

| 层级 | 位置 | 大小限制 | 行为 |
|------|------|---------|------|
| **HOT** | memory.md | ≤100 行 | 始终加载 |
| **WARM** | projects/, domains/ | ≤200 行/文件 | 上下文匹配时加载 |
| **COLD** | archive/ | 无限制 | 明确查询时加载 |

---

## 📈 自动提升/降级

| 条件 | 操作 |
|------|------|
| 模式 7 天内使用 3 次 | 提升到 HOT |
| 模式 30 天未使用 | 降级到 WARM |
| 模式 90 天未使用 | 归档到 COLD |
| 从不删除 | 除非用户明确要求 |

---

## 🎯 命名空间隔离

- **项目模式** → projects/{name}.md
- **全局偏好** → HOT tier (memory.md)
- **领域模式**（代码、写作）→ domains/
- **跨命名空间继承**: global → domain → project

---

## ⚖️ 冲突解决

当模式冲突时：

1. **最具体优先** (project > domain > global)
2. **最近优先** (同级别)
3. **如有歧义** → 询问用户

---

## 📝 快速查询

| 用户说 | 操作 |
|--------|------|
| "你知道 X 的什么？" | 搜索所有层级的 X |
| "你学到了什么？" | 显示 corrections.md 最后 10 条 |
| "显示我的模式" | 列出 memory.md (HOT) |
| "显示 [项目] 模式" | 加载 projects/{name}.md |
| "温存储里有什么？" | 列出 projects/ + domains/ 文件 |
| "记忆统计" | 显示每层计数 |
| "忘记 X" | 从所有层删除（先确认） |
| "导出记忆" | ZIP 所有文件 |

---

## 📊 记忆统计

**"memory stats" 请求时报告**：

```
📊 Self-Improving Memory

HOT (always loaded):
 memory.md: X entries

WARM (load on demand):
 projects/: X files
 domains/: X files

COLD (archived):
 archive/: X files

Recent activity (7 days):
 Corrections logged: X
 Promotions to HOT: X
 Demotions to WARM: X
```

---

## ⚠️ 常见陷阱

| 陷阱 | 为什么失败 | 更好的做法 |
|------|-----------|-----------|
| 从沉默中学习 | 创建虚假规则 | 等待明确纠正或重复证据 |
| 提升太快 | 污染 HOT 记忆 | 保持新课程临时直到重复 |
| 读取每个命名空间 | 浪费上下文 | 只加载 HOT 加最小匹配文件 |
| 通过删除压缩 | 失去信任和历史 | 合并、总结或降级 |

---

## 📋 核心规则

### 1. 从纠正和反思中学习

- ✅ 记录用户明确纠正
- ✅ 记录自己识别的改进
- ❌ 从不从沉默推断
- ✅ 3 次相同课程后 → 询问确认为规则

---

### 2. 分级存储

- ✅ HOT: memory.md（≤100 行，始终加载）
- ✅ WARM: projects/, domains/（≤200 行/文件）
- ✅ COLD: archive/（无限制）

---

### 3. 自动提升/降级

- ✅ 模式 7 天使用 3 次 → 提升到 HOT
- ✅ 模式 30 天未使用 → 降级到 WARM
- ✅ 模式 90 天未使用 → 归档到 COLD
- ❌ 从不删除（除非询问）

---

### 4. 命名空间隔离

- ✅ 项目模式在 projects/{name}.md
- ✅ 全局偏好在 HOT
- ✅ 领域模式在 domains/
- ✅ 跨命名空间继承：global → domain → project

---

### 5. 冲突解决

- ✅ 最具体优先 (project > domain > global)
- ✅ 最近优先 (同级别)
- ✅ 如有歧义 → 询问用户

---

### 6. 压缩

当文件超出限制：
- ✅ 合并相似纠正为单条规则
- ✅ 归档未使用模式
- ✅ 总结冗长条目
- ❌ 从不丢失确认的偏好

---

### 7. 透明

- ✅ 每个来自记忆的动作 → 引用来源
- ✅ 每周摘要：学习的模式、降级、归档
- ✅ 按需完整导出：所有文件 ZIP

---

### 8. 安全边界

- ❌ 从不存储凭证
- ❌ 不存储健康数据
- ❌ 不存储第三方信息

---

### 9. 优雅降级

如果上下文限制命中：
- ✅ 只加载 memory.md (HOT)
- ✅ 按需加载相关命名空间
- ✅ 从不静默失败 → 告诉用户什么未加载

---

## 📝 范围

### 本技能只做：

- ✅ 从用户纠正和自我反思中学习
- ✅ 在本地文件存储偏好 (~/self-improving/)
- ✅ 维护心跳状态（如果工作区集成）
- ✅ 激活时读取自己的记忆文件

### 本技能从不做：

- ❌ 访问日历、邮件、联系人
- ❌ 发起网络请求
- ❌ 读取 ~/self-improving/ 外的文件
- ❌ 从沉默或观察推断偏好
- ❌ 删除或盲目重写记忆
- ❌ 修改自己的 SKILL.md

---

## 💾 数据存储

**本地状态位置**: `~/self-improving/`

- **memory.md** - HOT 规则和确认偏好
- **corrections.md** - 明确纠正和可复用课程
- **projects/** 和 **domains/** - 范围化模式
- **archive/** - 衰减或非活跃模式
- **heartbeat-state.md** - 重复维护标记

---

## 🔗 相关技能

用户确认后安装：

- **memory** - 代理长期记忆模式
- **learning** - 自适应教学和解释
- **decide** - 自动学习决策模式
- **escalate** - 知道何时询问 vs 自主行动

---

## 📚 快速开始

### 1. 初始化

```bash
mkdir -p ~/self-improving
touch ~/self-improving/memory.md
touch ~/self-improving/corrections.md
```

### 2. 添加心跳（可选）

在 HEARTBEAT.md 中添加：

```markdown
## 自我改进维护

每天检查：
- [ ] 审查新的纠正
- [ ] 提升重复模式
- [ ] 降级未使用模式
```

### 3. 开始学习

**用户纠正时**：
```markdown
## [CORR-20260419-001]

**Logged**: 2026-04-19T22:00:00Z
**User**: "不，那不对，应该是..."
**Correction**: 应该使用 X 而不是 Y
**Category**: correction
```

**自我反思时**：
```markdown
CONTEXT: [任务类型]
REFLECTION: [我注意到的]
LESSON: [下次要做什么不同的]
```

---

## 📊 使用示例

### 示例 1: 记录纠正

**用户**: "不，不要写跟进，先刷新缓存"

**记录到** `corrections.md`:
```markdown
## [CORR-20260419-001]

**Logged**: 2026-04-19T22:00:00Z
**User**: "不，不要写跟进，先刷新缓存"
**Correction**: 写入操作前应先刷新缓存
**Category**: workflow
**Count**: 1
```

---

### 示例 2: 记录偏好

**用户**: "我总是喜欢先看客户详情再写跟进"

**记录到** `memory.md`:
```markdown
## [PREF-20260419-001]

**Logged**: 2026-04-19T22:00:00Z
**Preference**: 先查看客户详情再写跟进
**Category**: workflow
**Priority**: high
```

---

### 示例 3: 自我反思

**任务完成后**:
```markdown
CONTEXT: 写入跟进记录
REFLECTION: 忘记检查 Excel 是否关闭，导致写入失败
LESSON: 写入前先检查并关闭 Excel 进程
```

---

## 📈 提升流程

```
纠正 → corrections.md (计数)
  ↓
3 次相同纠正
  ↓
询问用户：是否提升为规则？
  ↓
用户确认
  ↓
提升到 memory.md (HOT)
```

---

## ⚠️ 注意事项

### 不要过度学习

- ❌ 不要从单次事件学习
- ❌ 不要从沉默推断
- ❌ 不要学习上下文特定指令

### 保持透明

- ✅ 引用来源
- ✅ 告知用户学习了什么
- ✅ 允许用户审查和删除

### 定期维护

- ✅ 每天审查新纠正
- ✅ 每周审查提升/降级
- ✅ 每月清理归档

---

## 🔐 安全考虑

1. **不存储敏感信息** - 凭证、密钥等
2. **本地存储** - 数据在 workspace 内
3. **用户控制** - 可以审查、删除任何条目
4. **透明操作** - 每个动作都引用来源

---

## 📚 参考链接

- [ClawHub 页面](https://clawhub.ai/ivangdavila/self-improving)
- [设置指南](setup.md)
- [学习机制](learning.md)
- [安全边界](boundaries.md)

---

*Remade for OpenClaw from ClawHub* 🔹
