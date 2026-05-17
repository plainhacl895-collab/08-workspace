# OpenClaw 技能安装完全指南

**版本**: v1.0.0  
**最后更新**: 2026-04-15  
**适用**: OpenClaw 2026.4.14+

---

## 📋 目录

1. [技能安装流程](#技能安装流程)
2. [技能创建指南](#技能创建指南)
3. [元数据规范](#元数据规范)
4. [依赖管理](#依赖管理)
5. [测试验证](#测试验证)
6. [故障排查](#故障排查)
7. [最佳实践](#最佳实践)
8. [检查清单](#检查清单)

---

## 技能安装流程

### 完整流程图

```
1. 创建技能框架
   ↓
2. 编写 SKILL.md 和功能代码
   ↓
3. 验证元数据
   ↓
4. 检查依赖
   ↓
5. 测试技能
   ↓
6. 正式使用
```

### 详细步骤

#### 步骤 1: 创建技能框架

```bash
# 手动创建目录结构
mkdir workspace/skills/my-skill
cd workspace/skills/my-skill
mkdir scripts references examples
```

#### 步骤 2: 编写 SKILL.md

```markdown
---
name: my-skill
description: 简洁明了的技能描述
homepage: https://github.com/user/my-skill
metadata: {"openclaw":{"emoji":"🔧"}}
---

# My Skill - 技能名称 🔧

## 技能描述

详细说明技能的功能和用途。

## 使用方法

```bash
# 示例命令
/my-command arg1 arg2
```

## 配置

如果有配置项，在此说明。

## 示例

提供使用示例。
```

#### 步骤 3: 验证元数据

```bash
# 使用验证脚本
powershell -ExecutionPolicy Bypass -File scripts/verify.ps1 -SkillName my-skill
```

#### 步骤 4: 检查依赖

```bash
# 检查 Python
python --version

# 检查 Node.js
node --version

# 检查其他依赖
# ...
```

#### 步骤 5: 测试技能

```bash
# 使用测试脚本
powershell -ExecutionPolicy Bypass -File scripts/test.ps1 -SkillName my-skill
```

#### 步骤 6: 正式使用

技能已自动可用（OpenClaw 自动发现），无需额外配置。

---

## 技能创建指南

### 标准目录结构

```
workspace/skills/my-skill/
├── SKILL.md              # 必需，技能主文件
├── scripts/              # 推荐，脚本目录
│   ├── install.ps1       # 安装脚本
│   ├── verify.ps1        # 验证脚本
│   └── test.ps1          # 测试脚本
├── references/           # 推荐，参考文档
├── examples/             # 推荐，使用示例
└── README.md             # 推荐，详细说明
```

### SKILL.md 模板

```markdown
---
name: skill-name
description: 简洁明了的技能描述（不超过 100 字）
homepage: https://github.com/user/repo
metadata: {"openclaw":{"emoji":"🔧"}}
---

# Skill Name - 中文名称 🔧

## 技能描述

详细说明技能的功能、用途和核心价值。

## 核心功能

- 功能 1
- 功能 2
- 功能 3

## 使用方法

```bash
# 基本用法
/skill-command [options]

# 高级用法
/skill-command --option value
```

## 配置

如果有配置项：

```yaml
# ~/.openclaw/config/skill-config.yaml
skill_name:
  option1: value1
  option2: value2
```

## 示例

### 示例 1: 基本使用

```bash
/skill-command arg1
```

### 示例 2: 高级使用

```bash
/skill-command arg1 --option value
```

## 故障排查

常见问题及解决方案。

## 版本历史

- v1.0.0 - 初始版本
```

---

## 元数据规范

### ✅ 正确的元数据

```yaml
---
name: my-skill                          # 必需，技能名称（小写，连字符分隔）
description: 简洁明了的技能描述         # 必需，技能描述（不超过 100 字）
homepage: https://github.com/user/repo  # 推荐，项目主页
metadata: {"openclaw":{"emoji":"🔧"}}   # 必需，OpenClaw 元数据
---
```

### ❌ 错误的元数据

```yaml
---
name: My_Skill                          # ❌ 不要使用大写和下划线
description: 这是一个非常非常长的描述...  # ❌ 描述太长
metadata: {
  "openclaw": {
    "emoji": "🔧",
    "requires": {"bins": ["python3"]}   # ❌ 不要添加 requires
  }
}
---
```

### 元数据字段说明

| 字段 | 必需 | 说明 | 示例 |
|------|------|------|------|
| `name` | ✅ | 技能名称（小写，连字符） | `my-skill` |
| `description` | ✅ | 技能描述（简洁） | `技能描述` |
| `homepage` | ⚠️ | 项目主页（GitHub 等） | `https://...` |
| `metadata.openclaw.emoji` | ✅ | 技能图标（emoji） | `🔧` |
| `metadata.openclaw.requires` | ❌ | **不要添加** | - |

---

## 依赖管理

### 声明依赖（不推荐）

**不要**在 SKILL.md 中声明依赖，而是：

1. 在 README.md 中说明依赖
2. 在安装脚本中检查依赖
3. 提供依赖安装指南

### 依赖检查脚本

```powershell
# scripts/check-deps.ps1

Write-Host "检查依赖..."

# 检查 Python
$python = Get-Command python -ErrorAction SilentlyContinue
if ($python) {
    Write-Host "✅ Python 已安装：$($python.Version)"
} else {
    Write-Host "❌ Python 未安装，请安装 Python 3.8+"
    exit 1
}

# 检查 Node.js
$node = Get-Command node -ErrorAction SilentlyContinue
if ($node) {
    Write-Host "✅ Node.js 已安装：$($node.Version)"
} else {
    Write-Host "⚠️  Node.js 未安装（可选）"
}
```

### 依赖安装指南

在 README.md 中提供：

```markdown
## 依赖

### Python

```bash
# Windows
winget install Python.Python.3.11

# macOS
brew install python@3.11

# Linux
sudo apt install python3.11
```

### Node.js

```bash
# Windows
winget install OpenJS.NodeJS.LTS

# macOS
brew install node

# Linux
sudo apt install nodejs
```
```

---

## 测试验证

### 测试类型

1. **元数据测试** - 验证 SKILL.md 格式
2. **功能测试** - 验证技能功能
3. **集成测试** - 验证与其他技能的兼容性
4. **启动测试** - 验证不影响 OpenClaw 启动

### 测试脚本模板

```powershell
# scripts/test.ps1

param([switch]$Verbose)

$TestsPassed = 0
$TestsFailed = 0

# 测试 1: 技能是否被加载
Write-Host "[测试 1] 检查技能加载..."
$skillList = openclaw skills list 2>&1
if ($skillList -match "my-skill") {
    Write-Host "✅ PASS"
    $TestsPassed++
} else {
    Write-Host "❌ FAIL"
    $TestsFailed++
}

# 测试 2: 功能测试
Write-Host "[测试 2] 功能测试..."
# 添加具体功能测试

# 测试总结
Write-Host ""
Write-Host "通过：$TestsPassed"
Write-Host "失败：$TestsFailed"

if ($TestsFailed -eq 0) {
    Write-Host "✅ 所有测试通过"
    exit 0
} else {
    Write-Host "❌ 部分测试失败"
    exit 1
}
```

### 运行测试

```bash
# 运行测试脚本
powershell -ExecutionPolicy Bypass -File scripts/test.ps1

# 详细模式
powershell -ExecutionPolicy Bypass -File scripts/test.ps1 -Verbose
```

---

## 故障排查

### 问题 1: 技能未加载

**症状**: `openclaw skills list` 不显示技能

**原因**:
- SKILL.md 格式错误
- 目录结构不正确
- OpenClaw 未重新加载

**解决**:
```bash
# 1. 验证 SKILL.md
powershell -ExecutionPolicy Bypass -File scripts/verify.ps1

# 2. 检查目录结构
ls workspace/skills/my-skill/

# 3. 重启 OpenClaw
openclaw gateway restart
```

### 问题 2: 显示 "needs setup"

**症状**: 技能状态显示 "needs setup"

**原因**: SKILL.md 中声明了 `requires`

**解决**:
```bash
# 编辑 SKILL.md，移除 requires 字段
# 然后重启 OpenClaw
```

### 问题 3: OpenClaw 无法启动

**症状**: `openclaw gateway` 启动失败

**原因**: 技能配置错误

**解决**:
```bash
# 1. 运行诊断
openclaw doctor

# 2. 自动修复
openclaw doctor --fix

# 3. 如果仍失败，临时移除技能
mv workspace/skills/my-skill workspace/skills/my-skill.disabled

# 4. 重启 OpenClaw
openclaw gateway
```

### 问题 4: 技能功能不正常

**症状**: 技能命令无响应或报错

**原因**:
- 脚本权限问题
- 依赖未安装
- 代码错误

**解决**:
```bash
# 1. 检查脚本权限
chmod +x scripts/*.sh

# 2. 检查依赖
powershell -ExecutionPolicy Bypass -File scripts/check-deps.ps1

# 3. 查看日志
cat ~/.openclaw/logs/*.log | grep "my-skill"
```

---

## 最佳实践

### 1. 命名规范

- ✅ 使用小写字母
- ✅ 使用连字符分隔
- ❌ 不要使用大写
- ❌ 不要使用下划线

**示例**:
- ✅ `my-skill`
- ❌ `MySkill`
- ❌ `my_skill`

### 2. 描述规范

- ✅ 简洁明了（不超过 100 字）
- ✅ 说明核心功能
- ❌ 不要过于冗长
- ❌ 不要包含技术细节

**示例**:
- ✅ `Hooks 系统，提供工具执行前后的拦截能力`
- ❌ `这是一个非常复杂的系统，它包含了...`（太长）

### 3. 版本控制

- 使用语义化版本（SemVer）
- 在 SKILL.md 中记录版本历史
- 使用 Git 标签标记版本

**示例**:
```markdown
## 版本历史

- v1.0.0 (2026-04-15) - 初始版本
  - ✅ 功能 1
  - ✅ 功能 2
```

### 4. 文档规范

- 提供完整的 README.md
- 包含使用示例
- 提供故障排查指南
- 说明依赖和安装步骤

### 5. 测试规范

- 编写自动化测试脚本
- 测试覆盖核心功能
- 定期运行测试
- 记录测试结果

---

## 检查清单

### 技能创建检查清单

- [ ] 创建标准目录结构
- [ ] 编写 SKILL.md（正确的元数据）
- [ ] 创建 scripts/ 目录
- [ ] 创建 verify.ps1 脚本
- [ ] 创建 install.ps1 脚本
- [ ] 创建 test.ps1 脚本
- [ ] 编写 README.md
- [ ] 提供使用示例
- [ ] 检查命名规范

### 技能安装检查清单

- [ ] 运行 verify.ps1 验证
- [ ] 检查依赖是否满足
- [ ] 运行 install.ps1 安装
- [ ] 运行 test.ps1 测试
- [ ] 验证 `openclaw skills list` 显示
- [ ] 测试技能功能
- [ ] 检查不影响其他技能
- [ ] 检查不影响 OpenClaw 启动

### 技能发布检查清单

- [ ] 所有测试通过
- [ ] 文档完整
- [ ] 示例可用
- [ ] 版本号正确
- [ ] 提交到 Git
- [ ] 创建 Git 标签
- [ ] 更新 CHANGELOG

---

## 相关资源

- **技能目录**: `workspace/skills/`
- **技能安装器**: `workspace/skills/skill-installer/SKILL.md`
- **验证脚本**: `workspace/skills/skill-installer/scripts/verify.ps1`
- **安装脚本**: `workspace/skills/skill-installer/scripts/install.ps1`
- **测试脚本**: `workspace/skills/skill-installer/scripts/test.ps1`

---

**最后更新**: 2026-04-15 🔹
