---
name: edge-tts
description: 使用 Microsoft Edge 神经 TTS 服务生成高质量文本转语音音频
homepage: https://clawhub.ai/i3130002/edge-tts
metadata: {"openclaw":{"emoji":"🔊"}}
---

# Edge TTS - 文本转语音技能 🔊

## 技能描述

使用 Microsoft Edge 神经 TTS 服务生成高质量文本转语音音频。

**核心功能**：
- ✅ 高质量神经 TTS
- ✅ 多语言支持
- ✅ 可调节语速、音调、音量
- ✅ 字幕生成
- ✅ 多种音频质量选项

---

## 🚀 快速开始

### 内置 TTS 工具（推荐）

当检测到 TTS 意图时，直接使用内置工具：

```javascript
// 示例：内置 tts 工具用法
tts("Your text to convert to speech")
// 返回：MEDIA: /path/to/audio.mp3
```

---

### 触发检测

- ✅ 识别 "tts" 关键词作为 TTS 请求
- ✅ 自动过滤 TTS 相关关键词，避免转换触发词本身

---

## ⚙️ 高级自定义

### 使用 Node.js 脚本

对于更多控制，直接使用捆绑的脚本：

#### TTS 转换器

```bash
cd scripts
npm install
node tts-converter.js "Your text" --voice en-US-AriaNeural --rate +10% --output output.mp3
```

#### 选项参数

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--voice` | `-v` | 语音名称 | en-US-AriaNeural |
| `--lang` | `-l` | 语言代码 | en-US |
| `--format` | `-o` | 输出格式 | audio-24khz-48kbitrate-mono-mp3 |
| `--pitch` | | 音调调整 | default |
| `--rate` | `-r` | 语速调整 | default |
| `--volume` | | 音量调整 | default |
| `--save-subtitles` | `-s` | 保存字幕为 JSON | false |
| `--output` | `-f` | 输出文件路径 | tts_output.mp3 |
| `--proxy` | `-p` | 代理 URL | none |
| `--timeout` | | 请求超时(ms) | 10000 |
| `--list-voices` | `-L` | 列出可用语音 | false |

---

### 配置管理器

```bash
cd scripts
npm install
node config-manager.js --set-voice en-US-AriaNeural
node config-manager.js --set-rate +10%
node config-manager.js --get
node config-manager.js --reset
```

---

## 🎙️ 语音选择

### 英语语音

- **en-US-MichelleNeural** (女性, 自然, 默认)
- **en-US-AriaNeural** (女性, 自然)
- **en-US-GuyNeural** (男性, 自然)
- **en-GB-SoniaNeural** (女性, 英国)
- **en-GB-RyanNeural** (男性, 英国)

---

### 其他语言

- **es-ES-ElviraNeural** (西班牙语, 西班牙)
- **fr-FR-DeniseNeural** (法语)
- **de-DE-KatjaNeural** (德语)
- **ja-JP-NanamiNeural** (日语)
- **zh-CN-XiaoxiaoNeural** (中文)
- **ar-SA-ZariyahNeural** (阿拉伯语)

---

## 📏 语速指南

| 值 | 用途 |
|-----|------|
| `"default"` | 正常速度 |
| `"-20%" to "-10%"` | 慢速, 清晰 (教程, 故事, 无障碍) |
| `"+10%" to "+20%"` | 稍快 (摘要) |
| `"+30%" to "+50%"` | 快速 (新闻, 效率) |

---

## 🎵 输出格式

根据用例选择音频质量：

- **audio-24khz-48kbitrate-mono-mp3**: 标准质量 (语音消息)
- **audio-24khz-96kbitrate-mono-mp3**: 高质量 (演示, 内容)
- **audio-48khz-96kbitrate-stereo-mp3**: 最高质量 (专业音频)

---

## 📁 资源文件

### scripts/tts-converter.js
主 TTS 转换脚本，使用 node-edge-tts。生成可自定义语音、语速、音量、音调和格式的音频文件。支持字幕生成和语音列表。

### scripts/config-manager.js
管理 TTS 设置的持久化用户偏好（语音、语言、格式、音调、语速、音量）。配置存储在 `~/.tts-config.json`。

### scripts/package.json
NPM 包配置，包含 node-edge-tts 依赖。

### references/node_edge_tts_guide.md
node-edge-tts npm 包的完整文档，包括：
- 按语言的完整语音列表
- 韵律选项（语速、音调、音量）
- 使用示例（CLI 和模块）
- 字幕生成
- 输出格式
- 最佳实践和限制

---

## 🧪 测试

### 基本测试
```bash
cd scripts
npm test
```
生成测试音频文件并验证 TTS 服务是否正常工作。

### 语音测试
在 [https://tts.travisvn.com/](https://tts.travisvn.com/) 测试不同语音和预览音频质量。

### 集成测试
```javascript
// 示例：使用默认设置测试 TTS
tts("This is a test of the TTS functionality.")
```

---

## 🚧 故障排除

- **测试连接性**: 运行 `npm test` 检查 TTS 服务是否可访问
- **检查语音可用性**: 使用 `node tts-converter.js --list-voices` 查看可用语音
- **验证代理设置**: 如果使用代理，测试 `node tts-converter.js "test" --proxy http://localhost:7890`
- **检查音频输出**: 测试应在 scripts 目录生成 test-output.mp3

---

## ⚠️ 重要说明

- **在线服务**: node-edge-tts 使用 Microsoft Edge 在线 TTS 服务
- **免费服务**: 无需 API 密钥
- **MP3 格式**: 默认输出 MP3 格式
- **互联网连接**: 需要互联网连接
- **字幕生成**: 支持字幕生成（JSON 格式，带单词级时间戳）
- **临时文件处理**: 音频文件默认保存到系统临时目录，调用应用应处理清理
- **TTS 关键词过滤**: 自动过滤 TTS 相关关键词
- **默认语音**: en-US-MichelleNeural (女性, 自然)
- **神经语音**: 以 Neural 结尾的语音提供比 Standard 语音更高的质量

---

## 🔐 安全考虑

### 数据隐私
- ✅ 不存储用户文本
- ✅ 临时文件自动清理
- ✅ 无数据持久化

### 网络安全
- ✅ 使用 HTTPS 连接
- ✅ 无敏感数据传输
- ✅ 微软官方服务

---

## 📚 参考链接

- [ClawHub 页面](https://clawhub.ai/i3130002/edge-tts)
- [语音测试](https://tts.travisvn.com/)
- [Node Edge TTS 文档](https://github.com/TravisVn/node-edge-tts)

---

*Remade for OpenClaw from ClawHub* 🔹
