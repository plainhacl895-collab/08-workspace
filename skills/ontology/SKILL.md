---
name: ontology
description: 类型化的词汇表 + 约束系统，用于将知识表示为可验证的图谱
homepage: https://clawhub.ai/oswalpalash/ontology
metadata: {"openclaw":{"emoji":"🕸️"}}
---

# Ontology - 知识图谱技能 🕸️

## 技能描述

类型化的词汇表 + 约束系统，用于将知识表示为可验证的图谱。

**核心概念**：
- 一切都是有类型的实体
- 每个实体有属性
- 实体之间有关系
- 每次变更都经过类型约束验证

---

## 📊 核心类型

### 代理与人

```json
Person: { name, email?, phone?, notes? }
Organization: { name, type?, members[] }
```

### 工作

```json
Project: { name, status, goals[], owner? }
Task: { title, status, due?, priority?, assignee?, blockers[] }
Goal: { description, target_date?, metrics[] }
```

### 时间与地点

```json
Event: { title, start, end?, location?, attendees[], recurrence? }
Location: { name, address?, coordinates? }
```

### 信息

```json
Document: { title, path?, url?, summary? }
Message: { content, sender, recipients[], thread? }
Thread: { subject, participants[], messages[] }
Note: { content, tags[], refs[] }
```

### 资源

```json
Account: { service, username, credential_ref? }
Device: { name, type, identifiers[] }
Credential: { service, secret_ref } # 不直接存储密钥
```

---

## 💾 存储

**默认位置**: `memory/ontology/graph.jsonl`

**数据格式**:
```json
{"op":"create","entity":{"id":"p_001","type":"Person","properties":{"name":"Alice"}}}
{"op":"create","entity":{"id":"proj_001","type":"Project","properties":{"name":"Website Redesign","status":"active"}}}
{"op":"relate","from":"proj_001","rel":"has_owner","to":"p_001"}
```

---

## 🚀 使用场景

| 触发 | 操作 |
|------|------|
| "记住..." | 创建/更新实体 |
| "我知道 X 的什么？" | 查询图谱 |
| "链接 X 到 Y" | 创建关系 |
| "显示项目 Z 的所有任务" | 图谱遍历 |
| "什么依赖于 X？" | 依赖查询 |
| 规划多步骤工作 | 建模为图谱转换 |
| 技能需要共享状态 | 读/写本体对象 |

---

## 🔧 工作流程

### 创建实体

```bash
python3 scripts/ontology.py create --type Person --props '{"name":"Alice","email":"alice@example.com"}'
```

### 查询

```bash
python3 scripts/ontology.py query --type Task --where '{"status":"open"}'
python3 scripts/ontology.py get --id task_001
python3 scripts/ontology.py related --id proj_001 --rel has_task
```

### 链接实体

```bash
python3 scripts/ontology.py relate --from proj_001 --rel has_task --to task_001
```

### 验证

```bash
python3 scripts/ontology.py validate # 检查所有约束
```

---

## 📋 约束定义

**位置**: `memory/ontology/schema.yaml`

```yaml
types:
  Task:
    required: [title, status]
    status_enum: [open, in_progress, blocked, done]
  
  Event:
    required: [title, start]
    validate: "end >= start if end exists"
  
  Credential:
    required: [service, secret_ref]
    forbidden_properties: [password, secret, token]

relations:
  has_owner:
    from_types: [Project, Task]
    to_types: [Person]
    cardinality: many_to_one
  
  blocks:
    from_types: [Task]
    to_types: [Task]
    acyclic: true # 无循环依赖
```

---

## 🏗️ 架构作为图谱转换

将多步骤计划建模为一系列图谱操作：

**计划**: "安排团队会议并创建后续任务"

```
1. CREATE Event { title: "Team Sync", attendees: [p_001, p_002] }
2. RELATE Event -> has_project -> proj_001
3. CREATE Task { title: "Prepare agenda", assignee: p_001 }
4. RELATE Task -> for_event -> event_001
5. CREATE Task { title: "Send summary", assignee: p_001, blockers: [task_001] }
```

每个步骤在执行前都经过验证。违反约束则回滚。

---

## 🔗 集成模式

### 与因果推理

记录本体突变为因果动作：

```json
action = {
  "action": "create_entity",
  "domain": "ontology",
  "context": {"type": "Task", "project": "proj_001"},
  "outcome": "created"
}
```

### 跨技能通信

```python
# 邮件技能创建承诺
commitment = ontology.create("Commitment", {
  "source_message": msg_id,
  "description": "Send report by Friday",
  "due": "2026-01-31"
})

# 任务技能接收
tasks = ontology.query("Commitment", {"status": "pending"})
for c in tasks:
  ontology.create("Task", {
    "title": c.description,
    "due": c.due,
    "source": c.id
  })
```

---

## 📝 快速开始

### 初始化存储

```bash
mkdir -p memory/ontology
touch memory/ontology/graph.jsonl
```

### 创建架构（推荐）

```bash
python3 scripts/ontology.py schema-append --data '{
  "types": {
    "Task": { "required": ["title", "status"] },
    "Project": { "required": ["name"] },
    "Person": { "required": ["name"] }
  }
}'
```

### 开始使用

```bash
python3 scripts/ontology.py create --type Person --props '{"name":"Alice"}'
python3 scripts/ontology.py list --type Person
```

---

## 📚 技能合约

使用本体的技能应该声明：

```yaml
# 在 SKILL.md 前缀或头部
ontology:
  reads: [Task, Project, Person]
  writes: [Task, Action]
  preconditions:
    - "Task.assignee must exist"
  postconditions:
    - "Created Task has status=open"
```

---

## 🎯 房地产应用场景

### 客户管理

```json
Person: {
  "name": "刘先生",
  "phone": "138****0909",
  "budget": 1500,
  "district": "长宁",
  "grade": "A"
}
```

### 房源管理

```json
Property: {
  "id": "107114878245",
  "title": "仁恒河滨花园 4 房",
  "price": 1698,
  "area": 180,
  "rooms": "4 室 2 厅",
  "district": "长宁"
}
```

### 客户关系

```json
{
  "op": "relate",
  "from": "client_liu",
  "rel": "interested_in",
  "to": "property_107114878245"
}
```

### 跟进记录

```json
Followup: {
  "client": "client_liu",
  "date": "2026-04-19",
  "content": "电话沟通，邀约看房",
  "type": "phone"
}
```

---

## 📊 图谱查询示例

### 查询客户感兴趣的所有房源

```bash
python3 scripts/ontology.py related \
  --id client_liu \
  --rel interested_in
```

### 查询某房源的所有跟进

```bash
python3 scripts/ontology.py query \
  --type Followup \
  --where '{"client":"client_liu"}'
```

### 查询客户依赖关系

```bash
python3 scripts/ontology.py query \
  --type Task \
  --where '{"assignee":"agent_wang","status":"open"}'
```

---

## ⚠️ 注意事项

### 追加模式

使用现有本体数据或架构时，**追加/合并**变更而非覆盖文件。这保留历史并避免破坏先前定义。

### 不记录的内容

- ❌ 密钥、令牌、私钥
- ❌ 环境变量
- ❌ 完整凭证

**推荐**：使用 `credential_ref` 间接引用

---

## 🔐 安全考虑

1. **不存储密钥** - 使用引用间接存储
2. **本地存储** - 数据在 workspace 内
3. **类型验证** - 防止无效数据
4. **关系约束** - 防止无效关系
5. **循环检测** - 防止循环依赖

---

## 📚 参考链接

- [ClawHub 页面](https://clawhub.ai/oswalpalash/ontology)
- [完整类型定义](references/schema.md)
- [查询示例](references/queries.md)

---

*Remade for OpenClaw from ClawHub* 🔹
