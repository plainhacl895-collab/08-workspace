---
name: telegram
description: Telegram Bot API 集成指南，包含 HTTP 请求模板、路由规则和安全最佳实践
homepage: https://clawhub.ai/codedao12/telegram
metadata: {"openclaw":{"emoji":"📱"}}
---

# Telegram - Telegram Bot 集成技能 📱

## 技能描述

Telegram Bot API 集成指南，提供完整的 HTTP 请求模板、路由规则和安全最佳实践。

**核心功能**：
- ✅ Telegram Bot API 文档
- ✅ HTTP 请求模板
- ✅ 路由规则指南
- ✅ 安全最佳实践
- ✅ Webhook 配置指导

---

## 🔑 凭证设置

### 必需凭证

- **Bot Token**: 从 [@BotFather](https://t.me/BotFather) 获取
- **Base API URL**: `https://api.telegram.org/bot{token}/`

### 环境变量设置

```powershell
# Windows PowerShell
$env:TELEGRAM_BOT_TOKEN="your-bot-token"

# 永久设置
[System.Environment]::SetEnvironmentVariable('TELEGRAM_BOT_TOKEN','your-bot-token',[System.EnvironmentVariableTarget]::User)
```

---

## 🌐 API 端点

### 基础 URL
```
https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/
```

### 常用方法

| 方法 | 用途 | 参数 |
|------|------|------|
| `sendMessage` | 发送消息 | chat_id, text, parse_mode |
| `sendPhoto` | 发送图片 | chat_id, photo, caption |
| `sendDocument` | 发送文件 | chat_id, document, caption |
| `getUpdates` | 获取更新 | offset, limit, timeout |
| `setWebhook` | 设置 webhook | url, certificate, max_connections |

---

## 📋 HTTP 请求模板

### 发送消息

```bash
curl -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": "123456789",
    "text": "Hello from OpenClaw!",
    "parse_mode": "Markdown"
  }'
```

---

### 发送图片

```bash
curl -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendPhoto" \
  -F "chat_id=123456789" \
  -F "photo=@/path/to/image.jpg" \
  -F "caption=Image caption"
```

---

### 设置 Webhook

```bash
curl -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-domain.com/webhook/telegram",
    "secret_token": "your-secret-token",
    "max_connections": 40
  }'
```

---

## 🔄 路由规则

### 消息类型处理

| 消息类型 | 处理逻辑 | 示例 |
|---------|---------|------|
| **文本消息** | 解析命令和内容 | `/start`, `hello` |
| **图片消息** | 下载并处理 | 图片分析、OCR |
| **文档消息** | 验证格式并处理 | PDF、Excel 文件 |
| **位置消息** | 地理编码处理 | 坐标转地址 |
| **联系人消息** | 提取联系信息 | 电话、姓名 |

---

### 命令路由

```javascript
// 伪代码示例
switch(message.text) {
  case '/start':
    handleStart(message.chat.id);
    break;
  case '/help':
    handleHelp(message.chat.id);
    break;
  case '/status':
    handleStatus(message.chat.id);
    break;
  default:
    handleUnknown(message.chat.id, message.text);
}
```

---

## 🔒 安全最佳实践

### 凭证安全

- ✅ **不要在聊天中粘贴 Bot Token**
- ✅ **使用环境变量存储 Token**
- ✅ **定期轮换 Token**
- ✅ **使用专用 Bot 进行测试**

---

### Webhook 安全

- ✅ **使用 HTTPS**
- ✅ **实现 secret_token 验证**
- ✅ **验证请求签名**
- ✅ **限制 IP 范围（如果可能）**

---

### 输入验证

- ✅ **验证 chat_id 格式**
- ✅ **限制消息长度**
- ✅ **过滤恶意内容**
- ✅ **实施速率限制**

---

### 数据安全

- ✅ **不要记录敏感信息**
- ✅ **加密存储用户数据**
- ✅ **实施最小权限原则**
- ✅ **定期清理旧数据**

---

## ⚙️ Webhook 配置

### 设置步骤

1. **获取公网 URL**
   - 使用 ngrok、Cloudflare Tunnel 或 VPS
   - 确保 HTTPS 可用

2. **设置 Webhook**
   ```bash
   curl -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{
       "url": "https://your-domain.com/webhook/telegram",
       "secret_token": "your-32-char-secret-token"
     }'
   ```

3. **验证配置**
   ```bash
   curl "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getWebhookInfo"
   ```

---

### Webhook 处理

```javascript
// 伪代码示例
app.post('/webhook/telegram', (req, res) => {
  // 验证 secret_token
  const secretToken = req.headers['x-telegram-bot-api-secret-token'];
  if (secretToken !== process.env.TELEGRAM_SECRET_TOKEN) {
    return res.status(403).send('Forbidden');
  }
  
  // 处理更新
  const update = req.body;
  handleUpdate(update);
  
  res.status(200).send('OK');
});
```

---

## 🧪 测试

### 基本连接测试

```bash
# 获取 Bot 信息
curl "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getMe"

# 获取更新
curl "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getUpdates"
```

---

### 消息发送测试

```bash
# 发送测试消息到你的聊天
curl -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": "YOUR_CHAT_ID",
    "text": "OpenClaw Telegram integration test successful!"
  }'
```

---

### Webhook 测试

```bash
# 检查 Webhook 状态
curl "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getWebhookInfo"

# 删除 Webhook（如果需要）
curl "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/deleteWebhook"
```

---

## 🚧 故障排除

### 常见问题

#### 1. 401 Unauthorized
- ❌ Bot Token 错误
- ✅ 检查 Token 是否正确
- ✅ 重新从 @BotFather 获取

#### 2. 400 Bad Request
- ❌ 参数格式错误
- ✅ 验证 JSON 格式
- ✅ 检查必填参数

#### 3. Webhook 不工作
- ❌ URL 不可访问
- ✅ 测试公网 URL 可访问性
- ✅ 检查 HTTPS 证书
- ✅ 验证防火墙设置

#### 4. 消息发送失败
- ❌ Chat ID 错误
- ✅ 获取正确的 Chat ID
- ✅ 确保 Bot 可以向该 Chat 发送消息

---

### 调试工具

- **Telegram Web**: [https://web.telegram.org/](https://web.telegram.org/)
- **BotFather**: [https://t.me/BotFather](https://t.me/BotFather)
- **API 文档**: [https://core.telegram.org/bots/api](https://core.telegram.org/bots/api)

---

## 📊 性能优化

### 批量操作

- ✅ 使用 `sendMessage` 批量发送
- ✅ 实现消息队列
- ✅ 缓存常用响应

---

### 错误处理

- ✅ 实现重试机制
- ✅ 记录错误日志
- ✅ 优雅降级

---

### 资源管理

- ✅ 限制并发连接
- ✅ 清理临时文件
- ✅ 监控内存使用

---

## 🔗 相关资源

### 官方文档
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Bot Features](https://core.telegram.org/bots/features)
- [Webhook Setup](https://core.telegram.org/bots/webhooks)

---

### 开发工具
- [@BotFather](https://t.me/BotFather) - Bot 创建和管理
- [@RawDataBot](https://t.me/RawDataBot) - 查看原始消息数据
- [@JsonDumpBot](https://t.me/JsonDumpBot) - JSON 格式化

---

### 社区资源
- [Telegram Bots Group](https://t.me/joinchat/AAAAAEaM2rjIqE7vLzBf0w)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/telegram-bot)
- [GitHub Examples](https://github.com/topics/telegram-bot)

---

## ⚠️ 重要提醒

### 实施责任
- ⚠️ 此技能仅提供文档和模板
- ⚠️ 用户需要自行实现集成代码
- ⚠️ 在生产环境前先在开发 Bot 中测试

---

### 安全责任
- ⚠️ 安全存储 Bot Token
- ⚠️ 实施适当的输入验证
- ⚠️ 遵循最小权限原则
- ⚠️ 定期审查和更新代码

---

## 📚 参考链接

- [ClawHub 页面](https://clawhub.ai/codedao12/telegram)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Webhook Documentation](https://core.telegram.org/bots/webhooks)

---

*Remade for OpenClaw from ClawHub* 🔹
