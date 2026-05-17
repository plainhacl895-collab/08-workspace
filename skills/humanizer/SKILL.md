---
name: humanizer
description: 识别和移除 AI 写作模式，使文本更自然、更人性化
homepage: https://clawhub.ai/biostartechnology/humanizer
metadata: {"openclaw":{"emoji":"👤"}}
---

# Humanizer - 人性化技能 👤

## 技能描述

识别和移除 AI 写作模式，使文本更自然、更人性化。

**核心功能**：
- ✅ 识别 24 种 AI 写作模式
- ✅ 移除 AI 痕迹
- ✅ 添加人性化表达
- ✅ 保持原意
- ✅ 匹配语调

---

## 🔍 检测的 AI 模式

### 内容模式（6 种）

1. **过度强调重要性**
   - ❌ "This groundbreaking discovery..."
   - ✅ "This discovery..."

2. **过度强调知名度**
   - ❌ "The widely acclaimed author..."
   - ✅ "The author..."

3. **Superficial -ing 结尾**
   - ❌ "Revolutionizing the way we think..."
   - ✅ "Changing how we think..."

4. **推广性语言**
   - ❌ "Unlock the full potential..."
   - ✅ "Use effectively..."

5. **模糊归属**
   - ❌ "Studies have shown..."
   - ✅ "Smith et al. (2023) found..."

6. **公式化"挑战和前景"部分**
   - ❌ "Despite challenges, the future looks promising..."
   - ✅ 具体讨论挑战和机会

---

### 语言模式（6 种）

7. **AI 高频词汇**
   - ❌ leverage, delve, realm, tapestry, landscape
   - ✅ use, explore, area, structure, field

8. **避免使用 is/are**
   - ❌ "The solution presents a framework..."
   - ✅ "The solution is a framework..."

9. **否定平行结构**
   - ❌ "Not only X, but also Y"
   - ✅ "X and Y"

10. **强制三法则**
    - ❌ "First, second, finally..."
    - ✅ 自然过渡

11. **优雅变化（同义词循环）**
    - ❌ "method → approach → technique → methodology"
    - ✅ 一致使用同一术语

12. **虚假范围**
    - ❌ "from X to Y"（当只有两个点时）
    - ✅ 直接列出项目

---

### 样式模式（6 种）

13. **破折号过度使用**
    - ❌ "The result—surprisingly—was positive"
    - ✅ "The result was surprisingly positive"

14. **粗体过度使用**
    - ❌ "**Important**: This is key"
    - ✅ "This is important"

15. **内联标题列表**
    - ❌ "**Strengths**: ... **Weaknesses**: ..."
    - ✅ 使用段落或实际列表

16. **标题大写**
    - ❌ "The Future of Artificial Intelligence"
    - ✅ "The future of artificial intelligence"

17. **Emoji 装饰**
    - ❌ "Great results! 🎉"
    - ✅ "Great results!"

18. **弯引号**
    - ❌ "He said “hello”"
    - ✅ "He said 'hello'"

---

### 沟通模式（3 种）

19. **协作式沟通**
    - ❌ "Let's explore together..."
    - ✅ 直接陈述

20. **知识截止声明**
    - ❌ "As of my last update in 2023..."
    - ✅ 不提及知识截止

21. **谄媚语气**
    - ❌ "Great question! I'm glad you asked..."
    - ✅ 直接回答

---

### 填充和模糊（3 种）

22. **填充短语**
    - ❌ "It's worth noting that...", "In essence..."
    - ✅ 删除填充词

23. **过度模糊**
    - ❌ "various factors", "multiple aspects"
    - ✅ 具体说明

24. **通用积极结尾**
    - ❌ "This represents an exciting step forward!"
    - ✅ 具体总结或无结尾

---

## 🚀 使用方法

### 基本人性化

```bash
# 人性化文本
humanize --text "Your AI-generated text here"

# 从文件读取
humanize --file input.txt --output output.txt
```

---

### 高级选项

```bash
# 保留特定风格
humanize --text "..." --preserve tone,technical

# 只检测不修改
humanize --text "..." --detect-only

# 详细报告
humanize --text "..." --verbose

# 特定模式
humanize --text "..." --patterns 1,3,7,15
```

---

## 📋 命令参考

### 基本参数

| 参数 | 必需 | 说明 |
|------|------|------|
| `--text` | ❌ | 直接文本输入 |
| `--file` | ❌ | 输入文件路径 |
| `--output` | ❌ | 输出文件路径 |

---

### 高级参数

| 参数 | 说明 |
|------|------|
| `--preserve` | 保留的风格（tone, technical, formal） |
| `--detect-only` | 只检测不修改 |
| `--verbose` | 详细输出 |
| `--patterns` | 特定模式编号（1-24） |
| `--confidence` | 置信度阈值（0.0-1.0） |

---

## 📊 使用示例

### 示例 1: 基本人性化

**输入**:
```
This groundbreaking solution leverages cutting-edge technology to revolutionize the way we approach real estate management. Let's explore the key benefits together!
```

**输出**:
```
This solution uses advanced technology to improve how we manage real estate. The key benefits are:
```

---

### 示例 2: 技术文档

**输入**:
```
The methodology presents a comprehensive framework for analyzing property valuations. It's worth noting that this approach delves into multiple aspects of market dynamics.
```

**输出**:
```
The method provides a framework for analyzing property valuations. This approach examines market dynamics.
```

---

### 示例 3: 电子邮件

**输入**:
```
Great question! I'm glad you asked about our services. We unlock the full potential of property management through our innovative platform.
```

**输出**:
```
Thank you for your question about our services. Our platform improves property management.
```

---

## 🎯 保留选项

### 何时保留

| 风格 | 保留场景 |
|------|---------|
| **Technical** | 技术文档、API 文档 |
| **Formal** | 学术论文、正式报告 |
| **Tone** | 营销材料、品牌声音 |
| **None** | 一般内容（默认） |

---

### 保留命令

```bash
# 保留技术术语
humanize --text "..." --preserve technical

# 保留正式语调
humanize --text "..." --preserve formal

# 保留品牌声音
humanize --text "..." --preserve tone
```

---

## 📝 最佳实践

### 1. 分阶段处理

```bash
# 第一阶段：检测
humanize --text "..." --detect-only

# 第二阶段：修改
humanize --text "..." --patterns [检测到的模式]
```

---

### 2. 保留重要内容

```bash
# 技术文档保留专业术语
humanize --text "..." --preserve technical

# 营销材料保留品牌声音
humanize --text "..." --preserve tone
```

---

### 3. 验证结果

```bash
# 对比前后
humanize --text "..." --verbose
```

---

## 📊 输出格式

### 默认输出

```
Original: [原始文本]
Humanized: [人性化文本]
Patterns removed: [移除的模式]
Confidence: [置信度]
```

---

### 详细输出

```bash
humanize --text "..." --verbose
```

**返回**：
```
DETECTION REPORT
===============
Text length: 150 characters
Detected patterns: 5
- Pattern #1: Overemphasis on importance (confidence: 0.95)
- Pattern #7: AI buzzwords (confidence: 0.88)
- Pattern #19: Collaborative framing (confidence: 0.92)
- Pattern #21: Flattery (confidence: 0.85)
- Pattern #24: Generic positive closing (confidence: 0.78)

HUMANIZED TEXT
==============
[修改后的文本]
```

---

## ⚠️ 注意事项

### 不适用场景

- ❌ 诗歌、创意写作
- ❌ 法律文档（需要精确性）
- ❌ 医疗文档（需要精确性）
- ❌ 已经很自然的文本

---

### 过度人性化风险

- ⚠️ 可能改变技术含义
- ⚠️ 可能移除重要修饰词
- ⚠️ 可能简化复杂概念

---

## 🔐 隐私考虑

### 数据处理

- ✅ 纯本地处理
- ✅ 不发送到外部服务
- ✅ 不存储处理历史
- ✅ 不需要网络访问

---

### 敏感内容

- ✅ 安全处理机密信息
- ✅ 适合内部文档
- ✅ 无需担心数据泄露

---

## 📚 参考链接

- [ClawHub 页面](https://clawhub.ai/biostartechnology/humanizer)
- [Wikipedia AI Writing Patterns](https://en.wikipedia.org/wiki/Wikipedia:Identifying_Artificial_Intelligence_writing_patterns)
- [Original Research](https://meta.wikimedia.org/wiki/Research:Identifying_artificially_generated_text_on_Wikimedia_projects)

---

*Remade for OpenClaw from ClawHub* 🔹
