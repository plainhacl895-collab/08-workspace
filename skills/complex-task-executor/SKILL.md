---
name: complex-task-executor
description: complex-task-executor
---

# Complex Task Executor - 复杂任务执行器 🎯

## 技能描述

专门处理复杂任务和长任务的执行框架，解决以下核心问题：

1. **上下文丢失** - 长任务执行到后面忘记前面的进度和决策
2. **状态管理混乱** - 不知道当前执行到哪个阶段
3. **错误重复** - 前面犯过的错误后面继续犯
4. **进度不透明** - 用户不知道执行到哪一步了
5. **没有检查点** - 执行失败后无法从中间恢复
6. **工具滥用** - 没有权限控制，危险操作直接执行
7. **会话压缩不当** - 压缩时丢失重要信息

## 核心架构

### 1. **任务状态机（Task State Machine）**

```python
@dataclass
class TaskState:
    task_id: str                    # 任务唯一 ID
    task_name: str                  # 任务名称
    current_phase: str              # 当前阶段
    phase_history: list[str]        # 阶段历史
    decisions: list[Decision]       # 关键决策记录
    errors: list[ErrorRecord]       # 错误记录（避免重复）
    checkpoints: list[Checkpoint]   # 检查点（可恢复）
    progress_percent: int           # 进度百分比
    started_at: datetime            # 开始时间
    last_updated: datetime          # 最后更新时间
    status: str                     # running/paused/completed/failed
```

### 2. **阶段分解（Phase Decomposition）**

```python
COMPLEX_TASK_PHASES = {
    'code_modification': [
        '1_read_context',      # 读取完整上下文
        '2_backup',            # 备份原文件
        '3_analyze',           # 分析修改范围
        '4_execute',           # 执行修改
        '5_verify',            # 验证修改结果
        '6_commit',            # 提交/保存
    ],
    'script_execution': [
        '1_parse_command',     # 解析命令
        '2_check_deps',        # 检查依赖
        '3_set_timeout',       # 设置超时
        '4_execute',           # 执行
        '5_monitor_progress',  # 监控进度
        '6_handle_result',     # 处理结果
    ],
    'multi_step_workflow': [
        '1_plan',              # 规划步骤
        '2_validate_plan',     # 验证计划
        '3_execute_step_1',    # 执行步骤 1
        '4_checkpoint',        # 保存检查点
        '5_execute_step_2',    # 执行步骤 2
        '6_verify_all',        # 验证全部
        '7_report',            # 报告结果
    ],
}
```

### 3. **决策日志（Decision Log）**

```python
@dataclass
class Decision:
    phase: str                  # 决策阶段
    decision: str               # 决策内容
    rationale: str              # 决策理由
    alternatives: list[str]     # 考虑过的其他选项
    timestamp: datetime
    user_confirmed: bool        # 是否经过用户确认
```

**示例**：
```python
Decision(
    phase='3_analyze',
    decision='使用 edit 而非 write 修改文件',
    rationale='write 会覆盖整个文件，edit 只修改指定部分，更安全',
    alternatives=['write 覆盖', '手动编辑'],
    timestamp=datetime.now(),
    user_confirmed=False
)
```

### 4. **错误记忆（Error Memory）**

```python
@dataclass
class ErrorRecord:
    phase: str                  # 错误发生阶段
    error_type: str             # 错误类型
    error_message: str          # 错误信息
    root_cause: str             # 根本原因
    fix_applied: str            # 应用的修复
    prevention: str             # 预防措施
    timestamp: datetime
    repeated: int = 0           # 重复次数（目标：0）
```

**关键机制**：
- 每次执行前检查错误记忆
- 如果某个错误重复出现，立即停止并警告
- 任务结束后将新错误写入记忆

### 5. **检查点系统（Checkpoint System）**

```python
@dataclass
class Checkpoint:
    checkpoint_id: str          # 检查点 ID
    phase: str                  # 阶段名称
    state_snapshot: dict        # 状态快照
    recoverable: bool           # 是否可恢复
    created_at: datetime
    ttl_hours: int = 24         # 存活时间（小时）
```

**恢复流程**：
```python
def restore_checkpoint(checkpoint_id: str) -> TaskState:
    checkpoint = load_checkpoint(checkpoint_id)
    if not checkpoint:
        raise ValueError(f'Checkpoint not found: {checkpoint_id}')
    
    # 恢复状态
    state = TaskState(**checkpoint.state_snapshot)
    state.status = 'running'
    state.last_updated = datetime.now()
    
    # 通知用户
    print(f'✅ 已从检查点 {checkpoint_id} 恢复')
    print(f'📍 当前阶段：{state.current_phase}')
    
    return state
```

### 6. **进度报告（Progress Report）**

```python
@dataclass
class ProgressReport:
    task_id: str
    task_name: str
    current_phase: str
    progress_percent: int
    completed_phases: list[str]
    pending_phases: list[str]
    errors_encountered: int
    decisions_made: int
    checkpoints_created: int
    elapsed_time: timedelta
    eta: datetime | None        # 预计完成时间
```

**报告频率**：
- 每个阶段完成后自动报告
- 用户可随时查询 `/task-status <task_id>`
- 超过 5 分钟无进展时主动报告

---

## 执行流程

### 完整流程示例：修改代码

```python
async def execute_code_modification(task: CodeModificationTask):
    # 初始化任务状态
    state = TaskState(
        task_id=generate_id(),
        task_name=task.name,
        current_phase='1_read_context',
        status='running',
        started_at=datetime.now(),
    )
    
    # 阶段 1: 读取完整上下文
    log_phase_start(state, '1_read_context')
    try:
        # 🔑 关键：必须先 read 完整文件
        full_content = read_file(task.file_path)
        state.decisions.append(Decision(
            phase='1_read_context',
            decision='读取完整文件内容',
            rationale='避免截断代码，确保上下文完整',
            alternatives=['只读部分行', '依赖缓存'],
            timestamp=datetime.now()
        ))
        save_checkpoint(state, 'after_read')
    except Exception as e:
        record_error(state, 'read_failed', str(e), '文件不存在或权限问题')
        raise
    
    # 阶段 2: 备份原文件
    log_phase_start(state, '2_backup')
    backup_path = f'{task.file_path}.bak.{datetime.now().strftime("%Y%m%d%H%M%S")}'
    copy_file(task.file_path, backup_path)
    state.decisions.append(Decision(
        phase='2_backup',
        decision='创建备份文件',
        rationale='修改失败时可恢复',
        alternatives=['不备份', '使用版本控制'],
        timestamp=datetime.now()
    ))
    
    # 阶段 3: 分析修改范围
    log_phase_start(state, '3_analyze')
    # 检查错误记忆 - 避免重复犯错
    past_errors = load_error_memory('code_truncation')
    if past_errors:
        print(f'⚠️ 警告：历史上有 {len(past_errors)} 次代码截断错误')
        print(f'💡 预防措施：{past_errors[0].prevention}')
    
    edit_plan = analyze_edit(full_content, task.changes)
    state.decisions.append(Decision(
        phase='3_analyze',
        decision='使用精确文本替换',
        rationale='最小化修改范围，降低风险',
        alternatives=['重写整个文件', '使用 AST 解析'],
        timestamp=datetime.now()
    ))
    
    # 阶段 4: 执行修改
    log_phase_start(state, '4_execute')
    modified_content = apply_edit(full_content, edit_plan)
    save_checkpoint(state, 'before_write')
    
    # 阶段 5: 验证修改
    log_phase_start(state, '5_verify')
    verification_result = verify_modification(modified_content, task.requirements)
    if not verification_result.success:
        record_error(state, 'verification_failed', verification_result.error)
        # 恢复到检查点
        restore_checkpoint('before_write')
        raise ValueError('验证失败，已恢复到修改前状态')
    
    # 阶段 6: 提交/保存
    log_phase_start(state, '6_commit')
    write_file(task.file_path, modified_content)
    
    # 任务完成
    state.status = 'completed'
    state.progress_percent = 100
    save_task_state(state)
    
    # 发送完成报告
    send_progress_report(ProgressReport(
        task_id=state.task_id,
        task_name=state.task_name,
        current_phase='completed',
        progress_percent=100,
        completed_phases=state.phase_history,
        pending_phases=[],
        errors_encountered=len(state.errors),
        decisions_made=len(state.decisions),
        checkpoints_created=len(state.checkpoints),
        elapsed_time=datetime.now() - state.started_at,
        eta=None
    ))
```

---

## 命令接口

### 任务管理命令

```bash
# 开始新任务
/task-start <task_name> [--phase <phase_name>] [--checkpoint <checkpoint_id>]

# 查看任务状态
/task-status <task_id>

# 列出所有任务
/task-list [--status running|completed|failed]

# 暂停任务
/task-pause <task_id>

# 恢复任务
/task-resume <task_id> [--checkpoint <checkpoint_id>]

# 取消任务
/task-cancel <task_id>

# 查看任务历史
/task-history <task_id>

# 查看决策日志
/task-decisions <task_id>

# 查看错误记录
/task-errors <task_id>

# 列出检查点
/task-checkpoints <task_id>

# 恢复到检查点
/task-restore <checkpoint_id>
```

### 配置命令

```bash
# 设置进度报告频率
/task-config --report-frequency <minutes>

# 设置检查点间隔
/task-config --checkpoint-interval <phases>

# 设置最大重试次数
/task-config --max-retries <count>

# 启用/禁用错误记忆
/task-config --error-memory on|off
```

---

## 记忆集成

### 错误记忆文件

```json
// ~/.agent-memory/errors/code_modification.jsonl
{
  "ts": "2026-04-15T16:30:00+08:00",
  "task_type": "code_modification",
  "error_type": "code_truncation",
  "error_message": "修改代码时截断了代码行，导致语法错误",
  "root_cause": "没有读取完整文件就执行编辑",
  "fix_applied": "重新读取完整文件后重试",
  "prevention": "修改前必须先 read 完整文件，确认上下文再编辑",
  "repeated": 0
}
```

### 决策记忆文件

```json
// ~/.agent-memory/decisions/code_modification.jsonl
{
  "ts": "2026-04-15T16:35:00+08:00",
  "task_type": "code_modification",
  "phase": "3_analyze",
  "decision": "使用 edit 而非 write 修改文件",
  "rationale": "write 会覆盖整个文件，edit 只修改指定部分，更安全",
  "alternatives": ["write 覆盖", "手动编辑"],
  "user_confirmed": false
}
```

---

## 最佳实践

### 1. **任务启动前**

```python
# ✅ 正确：检查错误记忆
past_errors = load_error_memory(task_type)
if past_errors:
    print(f'⚠️ 历史上有 {len(past_errors)} 次相关错误')
    for error in past_errors[:3]:
        print(f'  - {error.error_type}: {error.prevention}')

# ✅ 正确：验证计划
validate_task_plan(task)
```

### 2. **执行过程中**

```python
# ✅ 正确：每个阶段保存检查点
for phase in task.phases:
    execute_phase(phase)
    save_checkpoint(state, f'after_{phase}')
    
# ✅ 正确：记录决策
state.decisions.append(Decision(
    phase=phase.name,
    decision=phase.decision,
    rationale=phase.rationale
))

# ✅ 正确：定期报告进度
if time_since_last_report > 5 minutes:
    send_progress_report(state)
```

### 3. **错误处理**

```python
# ✅ 正确：记录错误并检查是否重复
try:
    execute_step()
except Exception as e:
    error = record_error(state, type(e).__name__, str(e))
    
    # 检查是否重复
    if error.repeated > 0:
        print(f'🚨 错误重复 {error.repeated} 次！停止执行')
        state.status = 'failed'
        raise
    
    # 尝试恢复
    if state.checkpoints:
        print('🔄 尝试从检查点恢复...')
        restore_checkpoint(state.checkpoints[-1].checkpoint_id)
```

### 4. **任务完成后**

```python
# ✅ 正确：保存完整历史
save_task_state(state)
save_error_memory(state.errors)
save_decision_memory(state.decisions)

# ✅ 正确：发送完成报告
send_completion_report(ProgressReport(
    task_id=state.task_id,
    progress_percent=100,
    elapsed_time=datetime.now() - state.started_at,
    errors_encountered=len(state.errors),
    decisions_made=len(state.decisions)
))
```

---

## 实际应用场景

### 场景 1: 修改多个文件

```python
task = ComplexTask(
    name='重构代码结构',
    type='multi_file_modification',
    phases=[
        '1_analyze_dependencies',
        '2_backup_all_files',
        '3_modify_file_1',
        '4_verify_file_1',
        '5_modify_file_2',
        '6_verify_file_2',
        '7_run_tests',
        '8_commit_changes',
    ]
)

# 每个文件修改后保存检查点
# 验证失败时恢复到该文件的检查点
# 所有文件完成后运行测试
```

### 场景 2: 长脚本执行

```python
task = ComplexTask(
    name='部署应用',
    type='long_script_execution',
    phases=[
        '1_check_prerequisites',
        '2_install_dependencies',
        '3_configure_environment',
        '4_run_migrations',
        '5_deploy_code',
        '6_run_health_checks',
        '7_notify_stakeholders',
    ],
    timeout=3600,  # 1 小时
    checkpoint_interval=2  # 每 2 个阶段保存检查点
)

# 每个阶段监控进度
# 超时前主动报告
# 失败时恢复到最近的检查点
```

### 场景 3: 客户 - 房源匹配流程

```python
task = ComplexTask(
    name='为客户匹配房源',
    type='client_property_matching',
    phases=[
        '1_load_client_context',
        '2_extract_requirements',
        '3_search_properties',
        '4_filter_results',
        '5_rank_matches',
        '6_generate_report',
        '7_save_recommendations',
    ]
)

# 每个阶段记录决策
# 匹配失败时记录原因
# 完成后保存推荐结果
```

---

## 监控指标

```python
@dataclass
class TaskMetrics:
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    avg_completion_time: timedelta
    avg_errors_per_task: float
    most_common_errors: list[str]
    checkpoint_success_rate: float  # 检查点恢复成功率
    decision_quality_score: float   # 决策质量评分
    error_repeat_rate: float        # 错误重复率（目标：0）
```

---

## 配置示例

```yaml
# ~/.openclaw/config/complex-task-config.yaml
complex_task:
  enabled: true
  
  # 进度报告
  progress_report:
    frequency_minutes: 5
    include_decisions: true
    include_errors: true
    
  # 检查点
  checkpoints:
    enabled: true
    interval_phases: 2
    ttl_hours: 24
    max_checkpoints: 10
    
  # 错误记忆
  error_memory:
    enabled: true
    max_errors_stored: 100
    repeat_threshold: 2  # 重复 2 次后停止
    
  # 决策日志
  decision_log:
    enabled: true
    require_confirmation_for:
      - destructive_operations
      - bulk_updates
      - deletions
      
  # 超时控制
  timeouts:
    default_seconds: 300
    long_task_seconds: 3600
    warning_before_timeout_seconds: 60
```

---

## 安装与使用

### 安装

```bash
# 安装技能
openclaw skills install complex-task-executor
```

### 快速开始

```bash
# 开始新任务
/task-start "修改 daily_follow_check.py 脚本"

# 查看状态
/task-status <task_id>

# 暂停任务
/task-pause <task_id>

# 恢复任务
/task-resume <task_id>
```

---

## 版本历史

- **v1.0.0** (2026-04-15) - 初始版本
  - ✅ 任务状态机
  - ✅ 阶段分解
  - ✅ 决策日志
  - ✅ 错误记忆
  - ✅ 检查点系统
  - ✅ 进度报告

---

*Created by 团团 based on claw-code architecture patterns and session-memory experience* 🔹
