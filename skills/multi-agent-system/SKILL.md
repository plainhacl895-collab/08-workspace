---
name: multi-agent-system
description: 多 Agent 协作系统，支持专业化分工、并行执行、团队协作，包含 6 个业务 Agent（客户、房源、跟进、匹配、计划、验证）
homepage: https://github.com/tuantuan-assistant/multi-agent-system
metadata: {"openclaw":{"emoji":"🤖"}}
---

# Multi-Agent System - 多 Agent 协作系统 🤖

## 技能描述

实现 Claw-Code 风格的多 Agent 协作系统，支持专业化分工、并行执行、团队协作。

**核心价值**：
- **专业化分工** - 不同 Agent 负责不同领域（客户、房源、跟进、匹配）
- **并行执行** - 多个子 Agent 同时处理任务
- **团队协作** - Agent 之间共享记忆、协同工作
- **Agent 记忆** - 每个 Agent 有独立的记忆和上下文

---

## 核心架构

### 1. **Agent 类型**

```python
class AgentType:
    CLIENT_AGENT = "ClientAgent"              # 客户 Agent
    PROPERTY_AGENT = "PropertyAgent"          # 房源 Agent
    FOLLOWUP_AGENT = "FollowupAgent"          # 跟进 Agent
    MATCHING_AGENT = "MatchingAgent"          # 匹配 Agent
    ANALYSIS_AGENT = "AnalysisAgent"          # 分析 Agent
    GENERAL_AGENT = "GeneralAgent"            # 通用 Agent
    VERIFICATION_AGENT = "VerificationAgent"  # 验证 Agent
    PLANNING_AGENT = "PlanningAgent"          # 计划 Agent
```

### 2. **Agent 基类**

```python
@dataclass
class Agent:
    agent_id: str                     # Agent 唯一 ID
    agent_type: AgentType             # Agent 类型
    name: str                         # Agent 名称
    description: str                  # Agent 描述
    capabilities: list[str]           # 能力列表
    memory: AgentMemory               # Agent 记忆
    context: AgentContext             # Agent 上下文
    status: AgentStatus               # Agent 状态
    created_at: datetime              # 创建时间
    last_active: datetime             # 最后活跃时间
    
    async def execute(self, task: Task) -> AgentResult:
        """执行任务"""
        pass
    
    async def collaborate(self, other_agents: list['Agent']) -> CollaborativeResult:
        """与其他 Agent 协作"""
        pass
```

### 3. **Agent 记忆**

```python
@dataclass
class AgentMemory:
    agent_id: str
    short_term: list[MemoryEntry]     # 短期记忆（当前会话）
    long_term: list[MemoryEntry]      # 长期记忆（持久化）
    working_context: dict             # 工作上下文
    learned_patterns: list[Pattern]   # 学习到的模式
    
    def add_short_term(self, entry: MemoryEntry):
        """添加短期记忆"""
        self.short_term.append(entry)
        # 超过限制时压缩
        if len(self.short_term) > 100:
            self.compress_short_term()
    
    def add_long_term(self, entry: MemoryEntry):
        """添加长期记忆"""
        self.long_term.append(entry)
        save_to_disk(entry)
    
    def search(self, query: str, scope: str = 'all') -> list[MemoryEntry]:
        """搜索记忆"""
        pass
    
    def compress_short_term(self):
        """压缩短期记忆"""
        # 保留最重要的 20 条
        important = sorted(
            self.short_term,
            key=lambda x: x.importance_score,
            reverse=True
        )[:20]
        self.short_term = important
```

### 4. **Agent 上下文**

```python
@dataclass
class AgentContext:
    session_id: str                   # 会话 ID
    user_id: str                      # 用户 ID
    current_task: Task | None         # 当前任务
    related_agents: list[str]         # 相关 Agent IDs
    shared_state: dict                # 共享状态
    conversation_history: list[Message]  # 对话历史
    tool_permissions: PermissionContext  # 工具权限
    
    def to_dict(self) -> dict:
        """转换为字典"""
        pass
    
    @classmethod
    def from_dict(cls, data: dict) -> 'AgentContext':
        """从字典加载"""
        pass
```

---

## 内置 Agent

### 1. 客户 Agent（ClientAgent）

```python
class ClientAgent(Agent):
    """客户 Agent - 负责客户相关的所有任务"""
    
    def __init__(self):
        super().__init__(
            agent_id='client_agent_001',
            agent_type=AgentType.CLIENT_AGENT,
            name='客户助手',
            description='专注于客户管理、跟进、分析的 Agent',
            capabilities=[
                'client_search',          # 客户搜索
                'client_context',         # 客户上下文
                'client_update',          # 客户信息更新
                'followup_write',         # 跟进写入
                'followup_analysis',      # 跟进分析
                'client_triage',          # 客户分类
            ],
            memory=AgentMemory(agent_id='client_agent_001'),
            context=AgentContext(),
            status=AgentStatus.IDLE
        )
    
    async def execute(self, task: ClientTask) -> AgentResult:
        """执行客户相关任务"""
        
        if task.action == 'search':
            return await self.search_client(task.query)
        elif task.action == 'context':
            return await self.get_client_context(task.client_id)
        elif task.action == 'update':
            return await self.update_client_info(task.client_id, task.updates)
        elif task.action == 'followup':
            return await self.write_followup(task.client_id, task.content)
        elif task.action == 'triage':
            return await self.triage_clients(task.limit)
        
        return AgentResult(success=False, message='未知操作')
    
    async def search_client(self, query: str) -> AgentResult:
        """搜索客户"""
        # 使用团团工具
        result = await run_tuantuan_command('client-search', {'query': query})
        
        # 学习搜索模式
        self.memory.add_long_term(MemoryEntry(
            content=f'搜索客户：{query}',
            metadata={'result_count': len(result.clients)},
            importance_score=0.7
        ))
        
        return AgentResult(
            success=True,
            data=result,
            message=f'找到 {len(result.clients)} 个客户'
        )
```

### 2. 房源 Agent（PropertyAgent）

```python
class PropertyAgent(Agent):
    """房源 Agent - 负责房源相关的所有任务"""
    
    def __init__(self):
        super().__init__(
            agent_id='property_agent_001',
            agent_type=AgentType.PROPERTY_AGENT,
            name='房源助手',
            description='专注于房源搜索、匹配、分析的 Agent',
            capabilities=[
                'property_search',        # 房源搜索
                'property_detail',        # 房源详情
                'property_match',         # 房源匹配
                'property_grab',          # 房源抓取
                'market_analysis',        # 市场分析
            ],
            memory=AgentMemory(agent_id='property_agent_001'),
            status=AgentStatus.IDLE
        )
    
    async def execute(self, task: PropertyTask) -> AgentResult:
        """执行房源相关任务"""
        
        if task.action == 'search':
            return await self.search_properties(task.criteria)
        elif task.action == 'detail':
            return await self.get_property_detail(task.house_id)
        elif task.action == 'match':
            return await self.match_properties(task.client_id)
        elif task.action == 'grab':
            return await self.grab_property_updates()
        elif task.action == 'analyze':
            return await self.analyze_market(task.area)
        
        return AgentResult(success=False, message='未知操作')
```

### 3. 跟进 Agent（FollowupAgent）

```python
class FollowupAgent(Agent):
    """跟进 Agent - 负责跟进相关的所有任务"""
    
    def __init__(self):
        super().__init__(
            agent_id='followup_agent_001',
            agent_type=AgentType.FOLLOWUP_AGENT,
            name='跟进助手',
            description='专注于跟进计划、执行、分析的 Agent',
            capabilities=[
                'daily_plan',             # 每日计划
                'followup_execute',       # 跟进执行
                'followup_check',         # 跟进检查
                'followup_analysis',      # 跟进分析
                'experience_query',       # 经验查询
            ],
            memory=AgentMemory(agent_id='followup_agent_001'),
            status=AgentStatus.IDLE
        )
    
    async def execute(self, task: FollowupTask) -> AgentResult:
        """执行跟进相关任务"""
        
        if task.action == 'daily_plan':
            return await self.generate_daily_plan(task.date)
        elif task.action == 'execute':
            return await self.execute_followup(task.client_id, task.content)
        elif task.action == 'check':
            return await self.check_followup_status(task.date)
        elif task.action == 'analyze':
            return await self.analyze_followup_effectiveness(task.period)
        
        return AgentResult(success=False, message='未知操作')
    
    async def generate_daily_plan(self, date: str) -> AgentResult:
        """生成每日跟进计划"""
        # 运行每日计划命令
        result = await run_tuantuan_command('client-daily-brief', {
            'limit': 8,
            'date': date
        })
        
        # 学习计划模式
        self.memory.add_long_term(MemoryEntry(
            content=f'生成 {date} 的每日计划',
            metadata={
                'total_clients': len(result.clients),
                'a_level_count': len([c for c in result.clients if c.grade == 'A']),
            },
            importance_score=0.9
        ))
        
        return AgentResult(
            success=True,
            data=result,
            message=f'生成 {len(result.clients)} 个客户的跟进计划'
        )
```

### 4. 匹配 Agent（MatchingAgent）

```python
class MatchingAgent(Agent):
    """匹配 Agent - 负责客户 - 房源匹配"""
    
    def __init__(self):
        super().__init__(
            agent_id='matching_agent_001',
            agent_type=AgentType.MATCHING_AGENT,
            name='匹配助手',
            description='专注于客户 - 房源智能匹配的 Agent',
            capabilities=[
                'client_property_match',  # 客户房源匹配
                'recommendation',         # 推荐
                'comparison',             # 对比
                'scoring',                # 评分
            ],
            memory=AgentMemory(agent_id='matching_agent_001'),
            status=AgentStatus.IDLE
        )
    
    async def execute(self, task: MatchingTask) -> AgentResult:
        """执行匹配任务"""
        
        if task.action == 'match':
            return await self.match_client_to_properties(task.client_id)
        elif task.action == 'recommend':
            return await self.recommend_properties(task.client_id, task.limit)
        elif task.action == 'compare':
            return await self.compare_properties(task.property_ids)
        elif task.action == 'score':
            return await self.score_match(task.client_id, task.property_id)
        
        return AgentResult(success=False, message='未知操作')
    
    async def match_client_to_properties(self, client_id: str) -> AgentResult:
        """匹配客户到房源"""
        # 运行推荐命令
        result = await run_tuantuan_command('client-recommend-properties', {
            'query': client_id,
            'candidate-limit': 5,
            'final-limit': 3
        })
        
        # 学习匹配模式
        self.memory.add_long_term(MemoryEntry(
            content=f'为客户 {client_id} 匹配房源',
            metadata={
                'matched_count': len(result.properties),
                'avg_score': result.average_score,
            },
            importance_score=0.95
        ))
        
        return AgentResult(
            success=True,
            data=result,
            message=f'匹配到 {len(result.properties)} 套房源'
        )
```

### 5. 计划 Agent（PlanningAgent）

```python
class PlanningAgent(Agent):
    """计划 Agent - 负责任务规划和分解"""
    
    def __init__(self):
        super().__init__(
            agent_id='planning_agent_001',
            agent_type=AgentType.PLANNING_AGENT,
            name='计划助手',
            description='专注于任务规划、分解、调度的 Agent',
            capabilities=[
                'task_decompose',         # 任务分解
                'phase_planning',         # 阶段规划
                'resource_allocation',    # 资源分配
                'scheduling',             # 调度
            ],
            memory=AgentMemory(agent_id='planning_agent_001'),
            status=AgentStatus.IDLE
        )
    
    async def execute(self, task: PlanningTask) -> AgentResult:
        """执行计划任务"""
        
        if task.action == 'decompose':
            return await self.decompose_task(task.complex_task)
        elif task.action == 'plan_phases':
            return await self.plan_phases(task.task)
        elif task.action == 'allocate':
            return await self.allocate_resources(task.task, task.agents)
        elif task.action == 'schedule':
            return await self.schedule_tasks(task.tasks)
        
        return AgentResult(success=False, message='未知操作')
```

### 6. 验证 Agent（VerificationAgent）

```python
class VerificationAgent(Agent):
    """验证 Agent - 负责结果验证和质量检查"""
    
    def __init__(self):
        super().__init__(
            agent_id='verification_agent_001',
            agent_type=AgentType.VERIFICATION_AGENT,
            name='验证助手',
            description='专注于结果验证、质量检查、错误检测的 Agent',
            capabilities=[
                'result_verification',    # 结果验证
                'quality_check',          # 质量检查
                'error_detection',        # 错误检测
                'consistency_check',      # 一致性检查
            ],
            memory=AgentMemory(agent_id='verification_agent_001'),
            status=AgentStatus.IDLE
        )
    
    async def execute(self, task: VerificationTask) -> AgentResult:
        """执行验证任务"""
        
        if task.action == 'verify':
            return await self.verify_result(task.result, task.criteria)
        elif task.action == 'check_quality':
            return await self.check_quality(task.output)
        elif task.action == 'detect_errors':
            return await self.detect_errors(task.content)
        elif task.action == 'check_consistency':
            return await self.check_consistency(task.items)
        
        return AgentResult(success=False, message='未知操作')
```

---

## Agent 协作系统

### 1. **协作协调器**

```python
class AgentCoordinator:
    """Agent 协作协调器"""
    
    def __init__(self):
        self.agents: dict[str, Agent] = {}
        self.active_tasks: dict[str, Task] = {}
        self.collaboration_history: list[CollaborationRecord] = []
    
    def register_agent(self, agent: Agent):
        """注册 Agent"""
        self.agents[agent.agent_id] = agent
    
    async def execute_collaborative_task(self, task: CollaborativeTask) -> CollaborativeResult:
        """执行协作任务"""
        
        # 1. 任务分解
        planning_agent = self.get_agent_by_type(AgentType.PLANNING_AGENT)
        subtasks = await planning_agent.decompose_task(task)
        
        # 2. 分配子任务给合适的 Agent
        assignments = self.assign_subtasks(subtasks)
        
        # 3. 并行执行
        results = await asyncio.gather(*[
            self.agents[agent_id].execute(subtask)
            for agent_id, subtask in assignments.items()
        ])
        
        # 4. 结果汇总
        verification_agent = self.get_agent_by_type(AgentType.VERIFICATION_AGENT)
        final_result = await verification_agent.verify_result(results, task.criteria)
        
        # 5. 记录协作历史
        self.collaboration_history.append(CollaborationRecord(
            task=task,
            assignments=assignments,
            results=results,
            final_result=final_result
        ))
        
        return final_result
    
    def assign_subtasks(self, subtasks: list[SubTask]) -> dict[str, SubTask]:
        """分配子任务给合适的 Agent"""
        assignments = {}
        
        for subtask in subtasks:
            # 根据子任务类型选择合适的 Agent
            if subtask.type == 'client_related':
                agent = self.get_agent_by_type(AgentType.CLIENT_AGENT)
            elif subtask.type == 'property_related':
                agent = self.get_agent_by_type(AgentType.PROPERTY_AGENT)
            elif subtask.type == 'followup_related':
                agent = self.get_agent_by_type(AgentType.FOLLOWUP_AGENT)
            elif subtask.type == 'matching_related':
                agent = self.get_agent_by_type(AgentType.MATCHING_AGENT)
            else:
                agent = self.get_agent_by_type(AgentType.GENERAL_AGENT)
            
            assignments[agent.agent_id] = subtask
        
        return assignments
```

### 2. **Agent 通信**

```python
class AgentMessage:
    """Agent 间通信消息"""
    
    def __init__(
        self,
        sender_id: str,
        receiver_id: str,
        message_type: str,
        content: any,
        priority: int = 0,
        requires_response: bool = False
    ):
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.message_type = message_type
        self.content = content
        self.priority = priority
        self.requires_response = requires_response
        self.timestamp = datetime.now()
        self.response: AgentMessage | None = None

class AgentCommunicationBus:
    """Agent 通信总线"""
    
    def __init__(self):
        self.message_queues: dict[str, asyncio.Queue] = {}
        self.subscribers: dict[str, list[callable]] = {}
    
    def register_agent(self, agent_id: str):
        """注册 Agent"""
        self.message_queues[agent_id] = asyncio.Queue()
    
    async def send_message(self, message: AgentMessage):
        """发送消息"""
        queue = self.message_queues.get(message.receiver_id)
        if queue:
            await queue.put(message)
            
            # 通知订阅者
            if message.message_type in self.subscribers:
                for callback in self.subscribers[message.message_type]:
                    await callback(message)
    
    async def receive_message(self, agent_id: str, timeout: float = None) -> AgentMessage:
        """接收消息"""
        queue = self.message_queues.get(agent_id)
        if queue:
            try:
                return await asyncio.wait_for(queue.get(), timeout)
            except asyncio.TimeoutError:
                return None
        return None
```

---

## Agent 分叉系统

```python
class AgentForkManager:
    """Agent 分叉管理器"""
    
    def __init__(self, parent_agent: Agent):
        self.parent_agent = parent_agent
        self.forks: list[Agent] = []
        self.results: list[AgentResult] = []
    
    def fork(self, task: Task, count: int = 3) -> list[Agent]:
        """分叉多个子 Agent 并行执行任务"""
        
        for i in range(count):
            fork_agent = Agent(
                agent_id=f'{self.parent_agent.agent_id}_fork_{i}',
                agent_type=self.parent_agent.agent_type,
                name=f'{self.parent_agent.name}_fork_{i}',
                description=f'Fork of {self.parent_agent.name}',
                capabilities=self.parent_agent.capabilities,
                memory=AgentMemory(agent_id=f'{self.parent_agent.agent_id}_fork_{i}'),
                context=deepcopy(self.parent_agent.context),
                status=AgentStatus.RUNNING
            )
            
            self.forks.append(fork_agent)
        
        return self.forks
    
    async def execute_parallel(self, tasks: list[Task]) -> list[AgentResult]:
        """并行执行多个任务"""
        
        if len(tasks) != len(self.forks):
            raise ValueError("任务数必须等于分叉数")
        
        # 并行执行
        self.results = await asyncio.gather(*[
            fork.execute(task)
            for fork, task in zip(self.forks, tasks)
        ])
        
        # 合并结果
        return self.results
    
    def merge_results(self) -> MergedResult:
        """合并所有分叉的结果"""
        
        merged = MergedResult(
            success=all(r.success for r in self.results),
            data=self._merge_data(),
            message=f'合并了 {len(self.results)} 个结果'
        )
        
        return merged
```

---

## 使用示例

### 场景 1: 客户房源匹配协作

```python
# 初始化协调器
coordinator = AgentCoordinator()

# 注册所有 Agent
coordinator.register_agent(ClientAgent())
coordinator.register_agent(PropertyAgent())
coordinator.register_agent(MatchingAgent())
coordinator.register_agent(PlanningAgent())
coordinator.register_agent(VerificationAgent())

# 创建协作任务
task = CollaborativeTask(
    name='为客户刘先生匹配房源',
    description='分析客户需求，搜索匹配房源，生成推荐报告',
    client_id='刘先生微信',
    criteria={
        'budget': 1500,
        'area': '长宁',
        'rooms': 4,
    }
)

# 执行协作任务
result = await coordinator.execute_collaborative_task(task)

print(f'✅ 任务完成：{result.message}')
print(f'📊 匹配到 {len(result.data.properties)} 套房源')
```

### 场景 2: 每日跟进计划并行执行

```python
# 创建跟进 Agent
followup_agent = FollowupAgent()

# 分叉 3 个子 Agent 并行处理
fork_manager = AgentForkManager(followup_agent)
forks = fork_manager.fork(task=None, count=3)

# 准备子任务
subtasks = [
    FollowupTask(action='daily_plan', date='2026-04-15', limit=8),
    FollowupTask(action='daily_plan', date='2026-04-15', limit=8, offset=8),
    FollowupTask(action='daily_plan', date='2026-04-15', limit=8, offset=16),
]

# 并行执行
results = await fork_manager.execute_parallel(subtasks)

# 合并结果
merged = fork_manager.merge_results()
print(f'✅ 生成 {merged.total_clients} 个客户的跟进计划')
```

---

## 监控指标

```python
@dataclass
class AgentMetrics:
    total_agents: int                   # 总 Agent 数
    active_agents: int                  # 活跃 Agent 数
    tasks_executed: int                 # 执行任务数
    tasks_succeeded: int                # 成功任务数
    tasks_failed: int                   # 失败任务数
    avg_execution_time_ms: float        # 平均执行时间
    collaboration_count: int            # 协作次数
    fork_count: int                     # 分叉次数
    memory_usage_mb: float              # 记忆使用量
```

---

## 配置示例

```yaml
# ~/.openclaw/config/agent-system-config.yaml
agent_system:
  enabled: true
  
  # 内置 Agent
  builtin_agents:
    client_agent: true
    property_agent: true
    followup_agent: true
    matching_agent: true
    planning_agent: true
    verification_agent: true
  
  # Agent 记忆
  memory:
    short_term_limit: 100
    long_term_persist: true
    compress_threshold: 80
    importance_threshold: 0.5
  
  # 协作
  collaboration:
    enabled: true
    max_parallel_agents: 5
    fork_limit: 10
  
  # 监控
  monitoring:
    enabled: true
    log_metrics: true
    alert_on_failure: true
```

---

## 版本历史

- **v1.0.0** (2026-04-15) - 初始版本
  - ✅ Agent 基类和类型定义
  - ✅ 6 个内置 Agent（客户、房源、跟进、匹配、计划、验证）
  - ✅ Agent 记忆系统
  - ✅ Agent 上下文管理
  - ✅ 协作协调器
  - ✅ Agent 通信总线
  - ✅ Agent 分叉系统
  - ✅ 监控指标

---

*Created by 团团 based on claw-code Agent architecture* 🔹
