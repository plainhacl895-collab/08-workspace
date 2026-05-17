---
name: hooks-system
description: Hooks 系统，提供工具执行前后的拦截、修改、增强能力，包括权限检查、日志记录、错误处理、智能建议
homepage: https://github.com/tuantuan-assistant/hooks-system
metadata: {"openclaw":{"emoji":"🪝"}}
---

# Hooks System - 钩子系统 🪝

## 技能描述

实现 Claw-Code 风格的 Hooks 系统，提供工具执行前后的拦截、修改、增强能力。

**核心价值**：
- 工具执行前：权限检查、参数修改、拒绝危险操作
- 工具执行后：结果处理、日志记录、触发通知
- 细粒度控制：基于工具名、前缀、路径、用户、会话的权限策略

---

## 核心架构

### 1. **Hook 类型**

```python
class HookType:
    PRE_TOOL_USE = "PreToolUse"      # 工具使用前
    POST_TOOL_USE = "PostToolUse"    # 工具使用后
    PRE_COMMAND = "PreCommand"       # 命令执行前
    POST_COMMAND = "PostCommand"     # 命令执行后
    ON_ERROR = "OnError"             # 错误发生时
    ON_SUGGESTION = "OnSuggestion"   # 提供建议时
```

### 2. **Hook 上下文**

```python
@dataclass
class HookContext:
    hook_type: HookType
    tool_name: str | None           # 工具名称
    command_name: str | None        # 命令名称
    parameters: dict                # 参数
    user_id: str                    # 用户 ID
    session_id: str                 # 会话 ID
    timestamp: datetime
    metadata: dict                  # 额外元数据
```

### 3. **Hook 结果**

```python
@dataclass
class HookResult:
    allowed: bool                   # 是否允许执行
    modified_parameters: dict | None  # 修改后的参数
    rejection_reason: str | None    # 拒绝理由
    suggestions: list[str] | None   # 建议列表
    notifications: list[str] | None # 通知列表
    metadata: dict                  # 额外元数据
```

### 4. **权限上下文**

```python
@dataclass(frozen=True)
class PermissionContext:
    deny_names: frozenset[str]      # 拒绝的工具名称
    deny_prefixes: tuple[str, ...]  # 拒绝的前缀
    deny_paths: tuple[str, ...]     # 拒绝的路径
    allow_names: frozenset[str]     # 允许的工具名称
    allow_prefixes: tuple[str, ...] # 允许的前缀
    require_confirmation: frozenset[str]  # 需要确认的工具
    
    def check_permission(self, tool_name: str, path: str | None = None) -> PermissionResult:
        # 权限检查逻辑
        pass
```

---

## Hook 实现

### Hook 1: 工具权限检查（PreToolUse）

```python
class ToolPermissionHook:
    """工具权限检查 Hook"""
    
    def __init__(self, permission_context: PermissionContext):
        self.permission_context = permission_context
    
    def execute(self, context: HookContext) -> HookResult:
        # 检查是否在拒绝列表中
        if context.tool_name in self.permission_context.deny_names:
            return HookResult(
                allowed=False,
                rejection_reason=f"工具 {context.tool_name} 被明确禁止"
            )
        
        # 检查前缀
        if any(context.tool_name.startswith(prefix) for prefix in self.permission_context.deny_prefixes):
            return HookResult(
                allowed=False,
                rejection_reason=f"工具 {context.tool_name} 的前缀被禁止"
            )
        
        # 检查路径（如果是文件操作）
        if path := context.metadata.get('file_path'):
            if any(path.startswith(deny_path) for deny_path in self.permission_context.deny_paths):
                return HookResult(
                    allowed=False,
                    rejection_reason=f"路径 {path} 被禁止访问"
                )
        
        # 检查是否需要确认
        if context.tool_name in self.permission_context.require_confirmation:
            # 等待用户确认
            user_confirmed = wait_for_user_confirmation(
                f"确认执行 {context.tool_name}？"
            )
            if not user_confirmed:
                return HookResult(
                    allowed=False,
                    rejection_reason="用户未确认"
                )
        
        return HookResult(allowed=True)
```

### Hook 2: 工具执行日志（PostToolUse）

```python
class ToolLoggingHook:
    """工具执行日志 Hook"""
    
    def __init__(self, log_dir: str):
        self.log_dir = log_dir
    
    def execute(self, context: HookContext, result: any) -> HookResult:
        # 记录工具执行日志
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'tool_name': context.tool_name,
            'parameters': context.parameters,
            'result_summary': summarize_result(result),
            'user_id': context.user_id,
            'session_id': context.session_id,
        }
        
        # 写入日志文件
        log_file = Path(self.log_dir) / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        
        return HookResult(allowed=True)
```

### Hook 3: 错误记忆检查（OnError）

```python
class ErrorMemoryHook:
    """错误记忆检查 Hook"""
    
    def __init__(self, memory_dir: str):
        self.memory_dir = memory_dir
    
    def execute(self, context: HookContext, error: Exception) -> HookResult:
        # 加载相关错误记忆
        past_errors = load_error_memory(self.memory_dir, context.tool_name)
        
        notifications = []
        if past_errors:
            notifications.append(f"⚠️ 历史上有 {len(past_errors)} 次相关错误")
            for error_record in past_errors[:3]:
                notifications.append(f"  - {error_record.error_type}: {error_record.prevention}")
        
        # 记录新错误
        if should_record_error(error, past_errors):
            record_new_error(self.memory_dir, context, error)
            notifications.append("💡 错误已记录到记忆库")
        
        return HookResult(
            allowed=True,
            notifications=notifications
        )
```

### Hook 4: 智能建议（OnSuggestion）

```python
class SmartSuggestionHook:
    """智能建议 Hook"""
    
    def execute(self, context: HookContext) -> HookResult:
        suggestions = []
        
        # 基于历史执行记录提供建议
        if context.tool_name == 'FileWriteTool':
            past_writes = load_past_writes(context.user_id)
            if past_writes:
                suggestions.append(f"💡 您通常备份后编辑，是否先创建备份？")
        
        # 基于最佳实践提供建议
        if context.tool_name == 'BashTool':
            if 'rm -rf' in context.parameters.get('command', ''):
                suggestions.append("⚠️ 危险操作！建议先确认路径和备份")
        
        # 基于业务规则提供建议
        if context.tool_name == 'WriteFollowupTool':
            client_context = load_client_context(context.metadata.get('client_id'))
            if client_context and client_context.last_followup_days > 7:
                suggestions.append(f"💡 客户已超过 7 天未跟进，建议详细记录")
        
        return HookResult(
            allowed=True,
            suggestions=suggestions
        )
```

---

## Hook 注册表

```python
class HookRegistry:
    """Hook 注册表"""
    
    def __init__(self):
        self.hooks: dict[HookType, list[callable]] = {
            HookType.PRE_TOOL_USE: [],
            HookType.POST_TOOL_USE: [],
            HookType.PRE_COMMAND: [],
            HookType.POST_COMMAND: [],
            HookType.ON_ERROR: [],
            HookType.ON_SUGGESTION: [],
        }
    
    def register(self, hook_type: HookType, hook: callable, priority: int = 0):
        """注册 Hook"""
        self.hooks[hook_type].append((priority, hook))
        self.hooks[hook_type].sort(key=lambda x: x[0], reverse=True)
    
    def execute_hooks(self, hook_type: HookType, context: HookContext, **kwargs) -> HookResult:
        """执行所有注册的 Hook"""
        final_result = HookResult(allowed=True)
        
        for priority, hook in self.hooks[hook_type]:
            try:
                result = hook(context, **kwargs)
                
                # 合并结果
                if not result.allowed:
                    final_result.allowed = False
                    final_result.rejection_reason = result.rejection_reason
                    break
                
                if result.modified_parameters:
                    final_result.modified_parameters = result.modified_parameters
                
                if result.suggestions:
                    final_result.suggestions = (final_result.suggestions or []) + result.suggestions
                
                if result.notifications:
                    final_result.notifications = (final_result.notifications or []) + result.notifications
                
            except Exception as e:
                # Hook 执行失败，记录但不中断
                log_hook_error(hook, e)
        
        return final_result
```

---

## 内置 Hooks

### 1. 危险操作拦截

```python
class DangerousOperationHook:
    """危险操作拦截 Hook"""
    
    DANGEROUS_PATTERNS = [
        r'rm\s+(-rf|--recursive|-fr)',  # 递归删除
        r'del\s+/[sf]',                  # Windows 强制删除
        r'format\s+',                    # 格式化
        r'dd\s+if=/dev/zero',            # 磁盘写入
        r'>\s*/dev/sd',                  # 磁盘覆盖
    ]
    
    def execute(self, context: HookContext) -> HookResult:
        if context.tool_name != 'BashTool':
            return HookResult(allowed=True)
        
        command = context.parameters.get('command', '')
        
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, command):
                return HookResult(
                    allowed=False,
                    rejection_reason=f"检测到危险命令模式：{pattern}",
                    notifications=["⚠️ 此操作可能导致数据丢失"]
                )
        
        return HookResult(allowed=True)
```

### 2. 文件备份建议

```python
class FileBackupSuggestionHook:
    """文件备份建议 Hook"""
    
    def execute(self, context: HookContext) -> HookResult:
        if context.tool_name not in ['FileWriteTool', 'FileEditTool']:
            return HookResult(allowed=True)
        
        file_path = context.parameters.get('file_path', '')
        
        # 检查是否是重要文件
        important_patterns = [
            r'\.py$',
            r'\.md$',
            r'daily_followup\.xlsm',
            r'\.json$',
        ]
        
        for pattern in important_patterns:
            if re.search(pattern, file_path):
                return HookResult(
                    allowed=True,
                    suggestions=[f"💡 建议先备份 {file_path}"]
                )
        
        return HookResult(allowed=True)
```

### 3. 会话记忆更新

```python
class SessionMemoryUpdateHook:
    """会话记忆更新 Hook"""
    
    def execute(self, context: HookContext, result: any) -> HookResult:
        # 工具执行成功后更新会话记忆
        if context.tool_name in ['WriteFollowupTool', 'ClientUpdateTool']:
            # 提取关键信息
            client_id = context.metadata.get('client_id')
            action = context.tool_name
            timestamp = datetime.now()
            
            # 更新会话记忆
            update_session_memory(
                session_id=context.session_id,
                key=f'last_{action}',
                value={
                    'client_id': client_id,
                    'timestamp': timestamp.isoformat(),
                    'result': summarize_result(result)
                }
            )
        
        return HookResult(allowed=True)
```

---

## 配置示例

```yaml
# ~/.openclaw/config/hooks-config.yaml
hooks:
  enabled: true
  
  # 权限控制
  permission:
    deny_names:
      - DeleteClientTool
      - ExportAllDataTool
    deny_prefixes:
      - Remote
      - Bulk
    deny_paths:
      - C:/Windows/
      - /etc/
    require_confirmation:
      - BashTool
      - FileWriteTool
      - FileDeleteTool
  
  # 日志
  logging:
    enabled: true
    log_dir: ~/.openclaw/logs/hooks/
    log_level: INFO
    log_format: json
  
  # 错误记忆
  error_memory:
    enabled: true
    memory_dir: ~/.agent-memory/errors/
    max_errors_stored: 100
  
  # 建议
  suggestions:
    enabled: true
    smart_suggestions: true
    backup_suggestions: true
  
  # 内置 Hooks
  builtin:
    dangerous_operation_hook: true
    file_backup_suggestion_hook: true
    session_memory_update_hook: true
```

---

## 使用示例

### 注册 Hook

```python
# 初始化 Hook 注册表
registry = HookRegistry()

# 注册权限检查 Hook
permission_context = PermissionContext(
    deny_names=frozenset(['DeleteClientTool']),
    deny_prefixes=('Remote', 'Bulk'),
    require_confirmation=frozenset(['BashTool', 'FileWriteTool'])
)
registry.register(
    HookType.PRE_TOOL_USE,
    ToolPermissionHook(permission_context).execute,
    priority=100  # 高优先级
)

# 注册日志 Hook
registry.register(
    HookType.POST_TOOL_USE,
    ToolLoggingHook('~/.openclaw/logs/hooks').execute,
    priority=10
)

# 注册错误记忆 Hook
registry.register(
    HookType.ON_ERROR,
    ErrorMemoryHook('~/.agent-memory/errors').execute,
    priority=50
)
```

### 执行 Hook

```python
# 工具执行前
context = HookContext(
    hook_type=HookType.PRE_TOOL_USE,
    tool_name='FileWriteTool',
    parameters={'file_path': 'daily_followup.xlsm', 'content': '...'},
    user_id='user_123',
    session_id='session_456'
)

result = registry.execute_hooks(HookType.PRE_TOOL_USE, context)

if not result.allowed:
    print(f"❌ 工具执行被拒绝：{result.rejection_reason}")
    return

if result.suggestions:
    for suggestion in result.suggestions:
        print(suggestion)

# 执行工具...

# 工具执行后
post_context = HookContext(
    hook_type=HookType.POST_TOOL_USE,
    tool_name='FileWriteTool',
    parameters=context.parameters,
    user_id=context.user_id,
    session_id=context.session_id
)

registry.execute_hooks(HookType.POST_TOOL_USE, post_context, result=tool_result)
```

---

## 监控指标

```python
@dataclass
class HookMetrics:
    total_hooks_executed: int       # 总执行次数
    hooks_by_type: dict[HookType, int]  # 按类型统计
    rejections: int                 # 拒绝次数
    suggestions_provided: int       # 提供建议次数
    errors_caught: int              # 捕获错误次数
    avg_execution_time_ms: float    # 平均执行时间
    slowest_hooks: list[str]        # 最慢的 Hooks
```

---

## 版本历史

- **v1.0.0** (2026-04-15) - 初始版本
  - ✅ Hook 类型定义
  - ✅ Hook 上下文和结果
  - ✅ 权限检查 Hook
  - ✅ 日志 Hook
  - ✅ 错误记忆 Hook
  - ✅ 智能建议 Hook
  - ✅ Hook 注册表
  - ✅ 内置危险操作拦截
  - ✅ 文件备份建议

---

*Created by 团团 based on claw-code hooks architecture* 🔹
