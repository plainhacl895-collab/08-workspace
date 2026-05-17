---
name: news-summary
description: 从国际可信源获取新闻摘要，支持文本和可选语音输出
homepage: https://clawhub.ai/joargp/news-summary
metadata: {"openclaw":{"emoji":"📰"}}
---

# News Summary - 新闻摘要技能 📰

## 技能描述

从国际可信源获取新闻摘要，支持文本和可选语音输出。

**核心功能**：
- ✅ 国际可信源（BBC、Reuters、NPR、Al Jazeera）
- ✅ RSS 解析和摘要
- ✅ 按地区/主题分组
- ✅ 可选语音摘要（OpenAI TTS）
- ✅ 平衡视角（西方 + 全球南方）

---

## 🌐 RSS 源

### BBC（主要源）

```bash
# 世界新闻
curl -s "https://feeds.bbci.co.uk/news/world/rss.xml"

# 头条新闻
curl -s "https://feeds.bbci.co.uk/news/rss.xml"

# 商业新闻
curl -s "https://feeds.bbci.co.uk/news/business/rss.xml"

# 科技新闻
curl -s "https://feeds.bbci.co.uk/news/technology/rss.xml"
```

---

### 其他国际源

```bash
# Reuters（路透社）
curl -s "https://www.reutersagency.com/feed/?best-regions=world&post_type=best"

# NPR（美国视角）
curl -s "https://feeds.npr.org/1001/rss.xml"

# Al Jazeera（全球南方视角）
curl -s "https://www.aljazeera.com/xml/rss/all.xml"
```

---

## 🔧 工作流程

### 文本摘要

1. **获取 BBC 世界头条**
2. **可选补充 Reuters/NPR**
3. **摘要关键故事**
4. **按地区或主题分组**

---

### 语音摘要（可选）

1. **创建文本摘要**
2. **使用 OpenAI TTS 生成语音**
3. **发送音频消息**

```bash
curl -s https://api.openai.com/v1/audio/speech \
 -H "Authorization: Bearer $OPENAI_API_KEY" \
 -H "Content-Type: application/json" \
 -d '{
 "model": "tts-1-hd",
 "input": "<news summary text>",
 "voice": "onyx",
 "speed": 0.95
 }' \
 --output /tmp/news.mp3
```

---

## 📋 输出格式

```markdown
📰 News Summary [date]

🌍 WORLD
- [headline 1]
- [headline 2]

💼 BUSINESS
- [headline 1]

💻 TECH
- [headline 1]
```

---

## ⚙️ 配置选项

### 环境变量（可选）

| 变量 | 用途 | 默认 |
|------|------|------|
| `OPENAI_API_KEY` | OpenAI TTS 语音生成 | 无（禁用语音） |

---

### 设置 API 密钥（Windows）

```powershell
# 临时设置
$env:OPENAI_API_KEY="your-api-key"

# 永久设置
[System.Environment]::SetEnvironmentVariable('OPENAI_API_KEY','your-api-key',[System.EnvironmentVariableTarget]::User)
```

---

## 📝 使用示例

### 基本新闻摘要

```bash
# 获取世界新闻
curl -s "https://feeds.bbci.co.uk/news/world/rss.xml" | \
 grep -E "<title>|<description>" | \
 sed 's/<[^>]*>//g' | \
 sed 's/^[ \t]*//' | \
 head -30
```

---

### 完整工作流

```bash
# 1. 获取多个源
bbc_news=$(curl -s "https://feeds.bbci.co.uk/news/world/rss.xml")
reuters_news=$(curl -s "https://www.reutersagency.com/feed/?best-regions=world&post_type=best")

# 2. 解析和摘要
# [AI 处理逻辑]

# 3. 可选语音生成
if [ -n "$OPENAI_API_KEY" ]; then
  curl -s https://api.openai.com/v1/audio/speech \
   -H "Authorization: Bearer $OPENAI_API_KEY" \
   -H "Content-Type: application/json" \
   -d '{
   "model": "tts-1-hd",
   "input": "'"$summary_text"'",
   "voice": "onyx",
   "speed": 0.95
   }' \
   --output "C:\temp\news.mp3"
fi
```

---

## 🎯 最佳实践

### 内容选择
- ✅ 保持简洁（5-8 个头条新闻）
- ✅ 优先突发新闻和重大事件
- ✅ 平衡视角（西方 + 全球南方）
- ✅ 按需引用来源

---

### 语音输出
- ✅ 时长控制在 ~2 分钟内
- ✅ 使用清晰的语音模型（onyx）
- ✅ 适当调整语速（0.95）

---

### 性能优化
- ✅ 缓存 RSS 结果避免重复请求
- ✅ 并行获取多个源
- ✅ 限制摘要长度

---

## ⚠️ 重要注意事项

### API 密钥安全
- ⚠️ OpenAI API 密钥是可选的
- ⚠️ 如果提供密钥，内容会发送到 OpenAI
- ⚠️ 建议使用专用密钥并设置用量限制
- ⚠️ 技能元数据未声明此要求（透明度问题）

---

### 作者信息
- ⚠️ 作者未知（joargp）
- ⚠️ 无主页或源代码链接
- ⚠️ 建议谨慎使用

---

### 文件写入
- ⚠️ 语音功能会创建临时文件（/tmp/news.mp3）
- ⚠️ Windows 路径：C:\temp\news.mp3

---

## 🔐 安全考虑

### 数据隐私
- ⚠️ 如果启用语音，摘要文本会发送到 OpenAI
- ✅ 纯文本模式不发送任何数据
- ✅ RSS 源都是公开可信的

---

### 网络访问
- ✅ BBC、Reuters、NPR、Al Jazeera（可信源）
- ⚠️ OpenAI TTS（如果启用语音）

---

### 凭证管理
- ✅ 环境变量方式安全
- ⚠️ 不在代码中硬编码密钥
- ⚠️ 可完全禁用语音功能

---

## 📊 故障排除

### RSS 获取失败
- ✅ 检查网络连接
- ✅ 验证 RSS URL 是否有效
- ✅ 检查防火墙设置

---

### 语音生成失败
- ✅ 验证 OPENAI_API_KEY 是否正确
- ✅ 检查 OpenAI 账户余额
- ✅ 确认 API 权限

---

### 临时文件问题
- ✅ 确保 C:\temp 目录存在
- ✅ 检查写入权限
- ✅ 清理旧的临时文件

---

## 📚 参考链接

- [ClawHub 页面](https://clawhub.ai/joargp/news-summary)
- [BBC RSS Feeds](https://feeds.bbci.co.uk/news/rss.xml)
- [Reuters Feeds](https://www.reutersagency.com/feed/)
- [NPR RSS](https://feeds.npr.org/1001/rss.xml)
- [Al Jazeera RSS](https://www.aljazeera.com/xml/rss/all.xml)
- [OpenAI TTS API](https://platform.openai.com/docs/api-reference/audio/createSpeech)

---

*Remade for OpenClaw from ClawHub* 🔹
