---
name: skill-installer
description: 技能安装专用工具，提供技能创建、验证、安装、测试的完整流程，确保技能能正常使用且不影响 OpenClaw 运行
homepage: https://github.com/tuantuan-assistant/skill-installer
metadata: {"openclaw":{"emoji":"📦"}}
---

# Skill Installer - 技能安装器 📦

## 技能描述

专门用于设计、创建、验证、安装和测试 OpenClaw 技能的系统化工具。

**核心价值**：
- ✅ 标准化技能创建流程
- ✅ 自动验证技能配置
- ✅ 确保不影响 OpenClaw 运行
- ✅ 完整的测试和验证
- ✅ 故障排查和回滚机制

---

## 核心功能

### 1. **技能创建向导**

```bash
/skill-create <skill-name>
```

**功能**：
- 创建标准技能目录结构
- 生成 SKILL.md 模板（正确的元数据格式）
- 生成必要的脚本和文档
- 检查命名冲突

**目录结构**：
```
workspace/skills/<skill-name>/
├── SKILL.md              # 技能主文件（含元数据）
├── scripts/              # 脚本目录
│   ├── install.sh        # 安装脚本
│   ├── verify.sh         # 验证脚本
│   └── test.sh           # 测试脚本
├── references/           # 参考文档
├── examples/             # 使用示例
└── README.md             # 技能说明
```

### 2. **元数据验证器**

```bash
/skill-verify-metadata <skill-name>
```

**验证项**：
- ✅ SKILL.md 是否存在
- ✅ 元数据格式是否正确
- ✅ 是否包含必需的字段（name, description）
- ✅ 是否包含无效的字段（requires 等）
- ✅ emoji 是否正确
- ✅ homepage 是否有效

**正确的元数据格式**：
```yaml
---
name: skill-name
description: 技能描述（简洁明了）
homepage: https://github.com/...
metadata: {"openclaw":{"emoji":"📦"}}
---
```

**错误的元数据**：
```yaml
---
name: skill-name
description: 技能描述
metadata: {"openclaw":{"emoji":"📦","requires":{"bins":["python3"]}}}  # ❌ 不要添加 requires
---
```

### 3. **依赖检查器**

```bash
/skill-check-deps <skill-name>
```

**检查项**：
- ✅ Python 是否安装（如果技能需要）
- ✅ Node.js 是否安装（如果技能需要）
- ✅ 外部命令是否可用
- ✅ 文件权限是否正确
- ✅ 目录结构是否完整

### 4. **技能安装器**

```bash
/skill-install <skill-name> [--force]
```

**安装流程**：
1. 备份当前技能（如果已存在）
2. 验证技能元数据
3. 检查依赖
4. 复制到 skills 目录
5. 设置文件权限
6. 验证技能可加载
7. 运行测试

**回滚机制**：
- 如果安装失败，自动恢复到备份
- 保留安装日志
- 提供详细的错误信息

### 5. **技能测试器**

```bash
/skill-test <skill-name> [--verbose]
```

**测试项**：
- ✅ 技能是否能被 OpenClaw 发现
- ✅ 技能描述是否正确显示
- ✅ 技能命令是否可用
- ✅ 技能功能是否正常
- ✅ 是否影响其他技能
- ✅ 是否影响 OpenClaw 启动

### 6. **技能卸载器**

```bash
/skill-uninstall <skill-name> [--backup]
```

**卸载流程**：
1. 检查技能是否正在使用
2. 备份技能（如果指定 --backup）
3. 删除技能目录
4. 清理缓存
5. 验证 OpenClaw 正常运行

### 7. **技能列表和状态**

```bash
/skill-list [--status]
/skill-status <skill-name>
```

**显示信息**：
- ✅ 技能名称和描述
- ✅ 安装状态（installed/needs setup/error）
- ✅ 依赖状态（satisfied/missing）
- ✅ 最后更新时间
- ✅ 文件大小和行数

---

## 使用流程

### 流程 1: 创建新技能

```bash
# 1. 创建技能框架
/skill-create my-new-skill

# 2. 编辑 SKILL.md 和功能代码
# 在 workspace/skills/my-new-skill/SKILL.md 中编写

# 3. 验证元数据
/skill-verify-metadata my-new-skill

# 4. 检查依赖
/skill-check-deps my-new-skill

# 5. 测试技能
/skill-test my-new-skill

# 6. 正式使用
# 技能已自动可用（OpenClaw 自动发现）
```

### 流程 2: 安装现有技能

```bash
# 1. 从 ClawHub 安装
openclaw skills install <skill-name>

# 2. 从本地安装
/skill-install <skill-name>

# 3. 验证安装
/skill-test <skill-name>

# 4. 查看状态
/skill-status <skill-name>
```

### 流程 3: 故障排查

```bash
# 1. 检查技能状态
/skill-status <skill-name>

# 2. 查看详细日志
cat ~/.openclaw/logs/skill-install-<timestamp>.log

# 3. 验证 OpenClaw 配置
openclaw doctor

# 4. 回滚到之前的版本
/skill-uninstall <skill-name> --backup
# 然后从备份恢复
```

---

## 检查清单

### 技能创建检查清单

- [ ] SKILL.md 文件存在
- [ ] 元数据格式正确（name, description, metadata）
- [ ] 没有无效的元数据字段（如 requires）
- [ ] emoji 正确且唯一
- [ ] homepage 有效（GitHub 或其他）
- [ ] 技能描述清晰简洁
- [ ] 目录结构完整（scripts/, references/）
- [ ] 有使用示例
- [ ] 有测试脚本

### 技能安装检查清单

- [ ] 技能目录不存在冲突
- [ ] 依赖已满足（Python/Node.js 等）
- [ ] 文件权限正确
- [ ] 元数据验证通过
- [ ] 技能能被 OpenClaw 发现
- [ ] 技能测试通过
- [ ] 不影响其他技能
- [ ] 不影响 OpenClaw 启动

### 技能验证检查清单

- [ ] `openclaw skills list` 显示技能
- [ ] 技能状态正常（不是 "needs setup"）
- [ ] 技能命令可用
- [ ] 技能功能正常
- [ ] 没有错误日志
- [ ] OpenClaw 启动正常
- [ ] 其他技能不受影响

---

## 最佳实践

### 1. 元数据最佳实践

**✅ 正确**：
```yaml
---
name: my-skill
description: 简洁明了的技能描述
homepage: https://github.com/user/my-skill
metadata: {"openclaw":{"emoji":"🔧"}}
---
```

**❌ 错误**：
```yaml
---
name: my-skill
description: 这是一个非常非常长的描述...
metadata: {"openclaw":{"emoji":"🔧","requires":{"bins":["python3"]}}}
---
```

### 2. 目录结构最佳实践

```
workspace/skills/my-skill/
├── SKILL.md              # 必需，技能主文件
├── scripts/              # 推荐，脚本目录
│   ├── install.sh
│   ├── verify.sh
│   └── test.sh
├── references/           # 推荐，参考文档
├── examples/             # 推荐，使用示例
└── README.md             # 推荐，详细说明
```

### 3. 测试最佳实践

```bash
# 创建测试脚本
cat > workspace/skills/my-skill/scripts/test.sh << 'EOF'
#!/bin/bash
echo "Testing my-skill..."

# 测试 1: 检查技能是否被加载
openclaw skills list | grep "my-skill"
if [ $? -ne 0 ]; then
    echo "❌ 技能未被加载"
    exit 1
fi

# 测试 2: 检查技能功能
# ... 添加具体功能测试

echo "✅ 所有测试通过"
EOF
```

### 4. 故障排查最佳实践

```bash
# 1. 查看技能日志
ls -lt ~/.openclaw/logs/ | head -10

# 2. 检查技能状态
/skill-status my-skill

# 3. 验证 OpenClaw 配置
openclaw doctor

# 4. 查看技能文件
cat workspace/skills/my-skill/SKILL.md

# 5. 回滚（如果需要）
/skill-uninstall my-skill --backup
```

---

## 命令参考

### 核心命令

| 命令 | 用途 | 示例 |
|------|------|------|
| `/skill-create` | 创建新技能 | `/skill-create my-skill` |
| `/skill-verify-metadata` | 验证元数据 | `/skill-verify-metadata my-skill` |
| `/skill-check-deps` | 检查依赖 | `/skill-check-deps my-skill` |
| `/skill-install` | 安装技能 | `/skill-install my-skill` |
| `/skill-test` | 测试技能 | `/skill-test my-skill` |
| `/skill-uninstall` | 卸载技能 | `/skill-uninstall my-skill` |
| `/skill-list` | 列出技能 | `/skill-list --status` |
| `/skill-status` | 查看状态 | `/skill-status my-skill` |

### 高级命令

| 命令 | 用途 | 示例 |
|------|------|------|
| `/skill-backup` | 备份技能 | `/skill-backup my-skill` |
| `/skill-restore` | 恢复技能 | `/skill-restore my-skill` |
| `/skill-update` | 更新技能 | `/skill-update my-skill` |
| `/skill-compare` | 比较版本 | `/skill-compare my-skill v1 v2` |

---

## 错误处理

### 常见错误及解决方案

**错误 1**: `Unrecognized key: "requires"`
- **原因**: SKILL.md 中添加了无效元数据
- **解决**: 移除 `requires` 字段

**错误 2**: `Skill not found`
- **原因**: 技能目录不存在或 SKILL.md 缺失
- **解决**: 检查目录结构和文件

**错误 3**: `needs setup`
- **原因**: 元数据中声明了依赖
- **解决**: 移除 `requires` 声明

**错误 4**: `Permission denied`
- **原因**: 文件权限不正确
- **解决**: `chmod +x scripts/*.sh`

**错误 5**: OpenClaw 无法启动
- **原因**: 技能配置错误
- **解决**: 运行 `openclaw doctor --fix`

---

## 版本历史

- **v1.0.0** (2026-04-15) - 初始版本
  - ✅ 技能创建向导
  - ✅ 元数据验证器
  - ✅ 依赖检查器
  - ✅ 技能安装器
  - ✅ 技能测试器
  - ✅ 技能卸载器
  - ✅ 完整的检查清单
  - ✅ 故障排查指南

---

*Created by 团团 based on skill installation experience* 🔹
