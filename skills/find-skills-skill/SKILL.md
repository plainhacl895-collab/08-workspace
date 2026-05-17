---
name: find-skills-skill
description: 搜索和发现 OpenClaw 技能的指南，从各种源找到合适的技能
homepage: https://clawhub.ai/fangkelvin/find-skills-skill
metadata: {"openclaw":{"emoji":"🔍"}}
---

# Find Skills Skill - 技能发现指南 🔍

## 技能描述

搜索和发现 OpenClaw 技能的指南，帮助用户从各种源找到合适的技能。

**核心功能**：
- ✅ 技能搜索策略
- ✅ 技能源目录
- ✅ 安装最佳实践
- ✅ 常见技能分类
- ✅ 故障排除指南

---

## 🎯 使用时机

### ✅ 何时使用此技能

- "Find skills for [task]"
- "Search for OpenClaw skills"  
- "What skills are available?"
- "Discover new skills"
- "Find skills by category"

### ❌ 何时不使用此技能

- **安装技能** → 使用 `clawhub install`
- **管理已安装技能** → 使用 `openclaw skills list`
- **创建新技能** → 使用 `skill-creator` 技能

---

## 🌐 技能源

### 1. ClawHub（主要源）

```bash
# 搜索技能
npx clawhub search "keyword"

# 浏览分类
npx clawhub browse
```

---

### 2. OpenClaw Directory

- **网站**: [https://www.openclawdirectory.dev/skills](https://www.openclawdirectory.dev/skills)
- **功能**: 按分类、流行度浏览或搜索

---

### 3. LobeHub Skills Marketplace

- **网站**: [https://lobehub.com/skills](https://lobehub.com/skills)
- **特点**: 社区贡献的技能

---

### 4. GitHub

- **搜索**: `openclaw skill` 或 `agent-skill`
- **识别**: 寻找包含 `SKILL.md` 文件的仓库

---

### 5. 社区论坛

- **SitePoint**: [https://www.sitepoint.com/community/](https://www.sitepoint.com/community/)
- **Discord**: [https://discord.com/invite/clawd](https://discord.com/invite/clawd)

---

## 🔍 搜索策略

### 按功能搜索

```bash
# 网络搜索技能
npx clawhub search "web search"

# 天气技能
npx clawhub search "weather"

# 文档技能
npx clawhub search "document"
```

---

### 按提供商搜索

```bash
# Tavily 技能
npx clawhub search "tavily"

# GitHub 技能
npx clawhub search "github"

# 日历技能
npx clawhub search "calendar"
```

---

### 按流行度搜索

```bash
# 最多安装的技能
npx clawhub search --sort installs

# 最多星标的技能
npx clawhub search --sort stars
```

---

## 📋 常见技能分类

### 核心技能

- **weather** - 天气预报
- **skill-creator** - 创建新技能
- **healthcheck** - 安全审计

---

### 集成技能

- **github** - GitHub 操作
- **feishu** - 飞书集成
- **notion** - Notion API

---

### 搜索技能

- **tavily-search** - 通过 Tavily 的网络搜索
- **web-search-plus** - 增强的网络搜索

---

### 代理技能

- **proactive-agent** - 主动自动化
- **coding-agent** - 代码生成

---

## 🛠️ 安装提示

### 安装前检查

- ✅ 检查技能要求
- ✅ 阅读 SKILL.md 了解用法
- ✅ 在隔离环境中测试
- ✅ 定期检查更新

---

### 安装命令

```bash
# 安装技能
npx clawhub install skill-name

# 同步已安装技能
npx clawhub sync

# 查看已安装技能
openclaw skills list
```

---

## 🚧 故障排除

### 速率限制

如果遇到 ClawHub 速率限制：

- ✅ 等待 1 小时后重试
- ✅ 使用替代源（网站）
- ✅ 在 GitHub 上手动搜索

---

### 安装问题

- ✅ 检查技能要求
- ✅ 验证网络连接
- ✅ 检查 OpenClaw 版本兼容性
- ✅ 确保已安装 Node.js 和 npx

---

## 📏 最佳实践

### 技能发现

- ✅ **先搜索再创建** - 不要重复造轮子
- ✅ **阅读文档** - 了解技能能力
- ✅ **从小开始** - 一次安装一个技能
- ✅ **彻底测试** - 验证技能按预期工作
- ✅ **提供反馈** - 帮助改进技能

---

### 安全考虑

- ✅ **审查源代码** - 安装前检查 SKILL.md
- ✅ **检查权限** - 注意技能声明的环境变量
- ✅ **隔离测试** - 在生产环境前测试
- ✅ **监控行为** - 观察技能的实际行为

---

## 🔗 相关技能

- **clawhub** - ClawHub CLI 工具
- **skill-creator** - 创建新技能
- **healthcheck** - 系统健康检查

---

## ⚙️ 运行时要求

### 必需工具

- **Node.js** - 运行 npx 命令
- **npx** - 执行 ClawHub CLI
- **网络连接** - 访问技能源

### 验证安装

```bash
# 检查 Node.js
node --version

# 检查 npx
npx --version

# 测试 ClawHub
npx clawhub --help
```

---

## 📊 使用示例

### 示例 1: 搜索天气技能

```bash
npx clawhub search "weather"
```

**预期输出**:
```
Found 3 skills:
1. weather (steipete) - Weather queries using wttr.in
2. weather-forecast (johnsmith) - Detailed weather forecasts
3. climate-data (datascientist) - Historical climate data
```

---

### 示例 2: 按分类浏览

```bash
npx clawhub browse
```

**交互式选择**:
```
Categories:
1. Web & Search
2. Productivity  
3. Development
4. Data & Analytics
5. Communication
Select category: _
```

---

### 示例 3: 搜索特定提供商

```bash
npx clawhub search "github" --sort stars
```

**按星标排序的 GitHub 技能**

---

## 🔐 安全与隐私

### 数据传输

- ✅ 只访问公开技能源
- ✅ 不发送用户数据到第三方
- ✅ 搜索查询可能被日志记录

### 本地影响

- ✅ 不修改本地文件
- ✅ 不安装未经请求的软件
- ✅ 用户控制所有安装决策

---

## 📚 参考链接

- [ClawHub 页面](https://clawhub.ai/fangkelvin/find-skills-skill)
- [OpenClaw Directory](https://www.openclawdirectory.dev/skills)
- [LobeHub Skills](https://lobehub.com/skills)
- [GitHub OpenClaw](https://github.com/search?q=openclaw+skill)
- [Community Discord](https://discord.com/invite/clawd)

---

*Remade for OpenClaw from ClawHub* 🔹
