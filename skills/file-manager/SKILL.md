---
name: file-manager
description: OpenClaw 自动化文件管理技能，提供智能分类、批量重命名、重复清理和目录同步
homepage: https://clawhub.ai/russellfei/file-manager
metadata: {"openclaw":{"emoji":"📁"}}
---

# File Manager - 文件管理技能 📁

## 技能描述

OpenClaw 自动化文件管理技能，提供智能分类、批量重命名、重复清理和目录同步。

**核心功能**：
- ✅ 智能文件分类（按类型、日期、大小）
- ✅ 批量重命名（正则、序列号、日期模式）
- ✅ 重复文件清理（基于内容哈希）
- ✅ 目录同步（单向/双向，支持排除模式）

---

## 🔧 核心功能

### 1. 智能文件分类 (organize)
```bash
# 按文件类型分类
python scripts/organize.py <source_dir> --by-type

# 按日期分类 (年/月/日)
python scripts/organize.py <source_dir> --by-date --date-format year/month
```

### 2. 批量重命名 (batch_rename)
```bash
# 添加前缀/后缀
python scripts/batch_rename.py <pattern> --prefix "IMG_" --suffix "_2024"

# 使用正则替换
python scripts/batch_rename.py "*.jpg" --replace "IMG_(\\d+)" "Photo_\\1"
```

### 3. 重复文件清理 (deduplicate)
```bash
# 扫描并列出重复文件
python scripts/deduplicate.py <directory> --scan-only

# 删除重复文件（保留最旧/最新）
python scripts/deduplicate.py <directory> --keep oldest --action delete
```

### 4. 目录同步 (sync)
```bash
# 单向同步 (源 → 目标)
python scripts/sync.py <source> <target> --mirror

# 排除特定文件
python scripts/sync.py <source> <target> --exclude "*.tmp,*.log,.git"
```

---

## 🔒 安全原则

- ✅ **预览优先**: 所有修改操作默认执行 dry-run 预览，需加 `--execute` 才执行
- ✅ **操作确认**: 执行前需要用户输入 yes 确认
- ✅ **符号链接安全**: 遍历目录时跳过符号链接，避免无限递归
- ✅ **冲突保护**: 目标文件已存在时自动重命名或跳过，不会覆盖

---

## ⚙️ 环境要求

- **Python 3.8+**
- **无外部依赖**，仅使用 Python 标准库

---

## 📋 使用场景

- **整理下载文件夹**: 自动按类型分类
- **清理重复照片**: 基于内容哈希检测重复
- **批量整理项目文件**: 按日期组织
- **自动备份工作目录**: 同步到备份目录

---

## 🛠️ 脚本说明

完整的 Python 脚本实现在 `scripts/` 目录中：
- `organize.py` - 智能文件分类
- `batch_rename.py` - 批量重命名  
- `deduplicate.py` - 重复文件清理
- `sync.py` - 目录同步

每个脚本都支持 `--help` 参数查看详细用法。

---

## 📚 参考链接

- [ClawHub 页面](https://clawhub.ai/russellfei/file-manager)

---

*Remade for OpenClaw from ClawHub* 🔹
