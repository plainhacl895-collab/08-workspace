---
name: multi-search-engine
description: 多搜索引擎聚合技能，支持 16 个搜索引擎、高级操作符、时间过滤和 WolframAlpha
homepage: https://clawhub.ai/gpyangyoujun/multi-search-engine
metadata: {"openclaw":{"emoji":"🔍"}}
---

# Multi Search Engine - 多搜索引擎技能 🔍

## 技能描述

聚合 16 个搜索引擎，支持高级搜索操作符、时间过滤和 WolframAlpha 查询。

**核心功能**：
- ✅ 16 个搜索引擎聚合
- ✅ 高级搜索操作符
- ✅ 时间过滤器
- ✅ WolframAlpha 集成
- ✅ 自动绕过临时封锁
- ✅ 会话 Cookie 管理（内存）

---

## ⚠️ 安全注意事项

### 使用前须知

1. **用户代理欺骗** - 设置浏览器样式 headers 以绕过封锁
2. **Cookie 获取** - 被 403/429 封锁时获取会话 cookie
3. **速率限制** - 建议 1-2 秒延迟，避免 IP 被封
4. **ToS 考虑** - 可能触及某些搜索引擎服务条款
5. **隐私** - Cookie 仅内存，不持久化，但请求可能被日志记录

---

## 🔍 支持的搜索引擎

### 主要引擎

| 引擎 | 代码 | 说明 |
|------|------|------|
| **Google** | `google` | 最大搜索引擎 |
| **Bing** | `bing` | 微软搜索引擎 |
| **DuckDuckGo** | `duckduckgo` | 隐私保护 |
| **Yahoo** | `yahoo` | 雅虎搜索 |
| **Baidu** | `baidu` | 百度搜索 |

---

### 专业引擎

| 引擎 | 代码 | 说明 |
|------|------|------|
| **WolframAlpha** | `wolframalpha` | 知识计算引擎 |
| **GitHub** | `github` | 代码搜索 |
| **Stack Overflow** | `stackoverflow` | 编程问答 |
| **Reddit** | `reddit` | 社交新闻 |
| **YouTube** | `youtube` | 视频搜索 |

---

### 学术引擎

| 引擎 | 代码 | 说明 |
|------|------|------|
| **Google Scholar** | `scholar` | 学术文献 |
| **arXiv** | `arxiv` | 物理论文 |
| **PubMed** | `pubmed` | 医学文献 |
| **Semantic Scholar** | `semanticscholar` | AI 论文 |

---

### 其他引擎

| 引擎 | 代码 | 说明 |
|------|------|------|
| **Qwant** | `qwant` | 欧洲隐私搜索 |
| **Ecosia** | `ecosia` | 环保搜索 |
| **Startpage** | `startpage` | Google 结果，隐私保护 |

---

## 🚀 使用方法

### 基本搜索

```bash
# 搜索多个引擎
search --query "AI agents" --engines google,bing,duckduckgo

# 单个引擎
search --query "OpenClaw" --engine google
```

---

### 时间过滤

```bash
# 过去 24 小时
search --query "OpenClaw" --time "past 24 hours"

# 过去一周
search --query "AI news" --time "past week"

# 过去一月
search --query "LLM" --time "past month"

# 过去一年
search --query "agent framework" --time "past year"

# 自定义日期范围
search --query "OpenClaw" --time "2026-01-01..2026-04-19"
```

---

### 高级操作符

```bash
# 精确匹配
search --query "\"exact phrase\""

# 排除词语
search --query "AI -chatbot"

# 站内搜索
search --query "site:github.com OpenClaw"

# 文件类型
search --query "filetype:pdf AI agents"

# 标题包含
search --query "intitle:OpenClaw"

# 相关网站
search --query "related:openclaw.ai"
```

---

### WolframAlpha 查询

```bash
# 事实查询
search --query "population of China" --engine wolframalpha

# 数学计算
search --query "integrate x^2" --engine wolframalpha

# 单位转换
search --query "100 miles to km" --engine wolframalpha

# 化学公式
search --query "H2O molar mass" --engine wolframalpha
```

---

## 📋 命令参考

### 基本参数

| 参数 | 必需 | 说明 |
|------|------|------|
| `--query` | ✅ | 搜索关键词 |
| `--engines` | ❌ | 引擎列表（逗号分隔） |
| `--engine` | ❌ | 单个引擎 |
| `--time` | ❌ | 时间过滤 |
| `--limit` | ❌ | 结果数量（默认 10） |

---

### 高级参数

| 参数 | 说明 |
|------|------|
| `--safe` | 安全搜索（过滤成人内容） |
| `--exact` | 精确匹配模式 |
| `--verbose` | 详细输出 |
| `--json` | JSON 格式输出 |

---

## 📊 使用示例

### 示例 1: 多引擎搜索

```bash
# 搜索 AI 代理框架
search --query "AI agent framework" \
  --engines google,bing,duckduckgo,github \
  --limit 20
```

---

### 示例 2: 带时间过滤

```bash
# 搜索本周的 OpenClaw 新闻
search --query "OpenClaw" \
  --time "past week" \
  --engines google,bing
```

---

### 示例 3: 代码搜索

```bash
# 搜索 GitHub 上的 OpenClaw 技能
search --query "openclaw skills" \
  --engine github \
  --limit 20
```

---

### 示例 4: 学术搜索

```bash
# 搜索 AI 代理论文
search --query "autonomous agents" \
  --engines scholar,arxiv,semanticscholar \
  --time "past year"
```

---

### 示例 5: WolframAlpha

```bash
# 查询人口统计
search --query "population of Shanghai" \
  --engine wolframalpha

# 数学计算
search --query "solve x^2 + 2x + 1 = 0" \
  --engine wolframalpha
```

---

## ⚠️ 速率限制

### 推荐延迟

| 引擎 | 延迟 | 说明 |
|------|------|------|
| **Google** | 2-3 秒 | 严格限制 |
| **Bing** | 1-2 秒 | 中等限制 |
| **DuckDuckGo** | 1 秒 | 宽松 |
| **其他** | 1 秒 | 一般限制 |

---

### 避免封锁

1. ✅ 使用 1-2 秒延迟
2. ✅ 不要并发太多请求
3. ✅ 使用不同引擎交替
4. ✅ 被 403/429 时暂停
5. ✅ 获取会话 cookie（如需要）

---

## 🔐 Cookie 管理

### 自动处理

- ✅ 被 403/429 封锁时自动获取 cookie
- ✅ Cookie 仅保存在内存
- ✅ 会话结束后清除
- ✅ 不持久化到磁盘

---

### 手动清除

```bash
# 清除所有 cookie
search --clear-cookies
```

---

## 📝 最佳实践

### 1. 使用合适的引擎

| 需求 | 推荐引擎 |
|------|---------|
| **通用搜索** | google, bing, duckduckgo |
| **代码** | github, stackoverflow |
| **学术** | scholar, arxiv, semanticscholar |
| **事实** | wolframalpha |
| **隐私** | duckduckgo, startpage, qwant |

---

### 2. 构建有效查询

```bash
# 好：具体明确
search --query "OpenClaw agent skills installation"

# 不好：太宽泛
search --query "OpenClaw"
```

---

### 3. 组合操作符

```bash
# 精确匹配 + 排除 + 时间
search --query "\"AI agent\" -chatbot" \
  --time "past month" \
  --engines google,bing
```

---

### 4. 多引擎验证

```bash
# 交叉验证信息
search --query "OpenClaw security audit" \
  --engines google,bing,duckduckgo,reddit
```

---

## 📊 结果格式

### 默认输出

```
[1] Title
    URL: https://...
    Snippet: ...
    Engine: google

[2] Title
    URL: https://...
    Snippet: ...
    Engine: bing
```

---

### JSON 输出

```bash
search --query "OpenClaw" --json
```

**返回**：
```json
{
  "query": "OpenClaw",
  "engines": ["google", "bing"],
  "results": [
    {
      "title": "...",
      "url": "...",
      "snippet": "...",
      "engine": "google"
    }
  ]
}
```

---

## ⚖️ 服务条款

### 遵守 ToS

- ⚠️ 某些引擎禁止自动化访问
- ⚠️ 遵守 robots.txt
- ⚠️ 不要滥用服务
- ✅ 用于合法研究目的

---

### 责任使用

1. ✅ 遵守速率限制
2. ✅ 尊重 robots.txt
3. ✅ 不用于垃圾邮件
4. ✅ 不用于恶意目的
5. ✅ 遵守当地法律

---

## 🔐 隐私考虑

### 数据保护

- ⚠️ 查询会发送到搜索引擎
- ⚠️ IP 地址可能被记录
- ✅ Cookie 仅内存
- ✅ 不持久化查询历史

---

### 敏感查询

- ❌ 不要搜索个人隐私
- ❌ 不要搜索机密信息
- ❌ 不要搜索非法内容
- ✅ 使用隐私引擎（DuckDuckGo 等）

---

## 📚 参考链接

- [ClawHub 页面](https://clawhub.ai/gpyangyoujun/multi-search-engine)
- [Google 高级搜索](https://support.google.com/websearch/answer/2466433)
- [WolframAlpha API](https://products.wolframalpha.com/api/)

---

*Remade for OpenClaw from ClawHub* 🔹
