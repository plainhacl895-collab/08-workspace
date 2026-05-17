---
name: local-whisper
description: Local speech-to-text using OpenAI Whisper. Runs fully offline after model download.
metadata: {"openclaw":{"emoji":"🎙️"}}
---

# Local Whisper STT

Local speech-to-text using OpenAI's Whisper. **Fully offline** after initial model download.

## Usage

```bash
# Basic transcription
whisper audio.wav --model base --language zh

# With timestamps
whisper audio.wav --model base --language zh --word_timestamps True
```

## Models

| Model | Size | Speed | Accuracy |
|-------|------|-------|----------|
| `tiny` | 39M | Fastest | Basic |
| `base` | 74M | Fast | Good (Default) |
| `small` | 244M | Medium | Better |
| `medium` | 769M | Slow | Best |
| `large` | 1.5G | Slowest | Maximum |

## Setup

Whisper is already installed via pip. Models download automatically on first use.

## Configuration for Telegram Voice

To enable automatic Telegram voice transcription, add to openclaw.json:

```json
{
  "plugins": {
    "entries": {
      "telegram": {
        "enabled": true,
        "voiceTranscription": {
          "enabled": true,
          "provider": "whisper-local",
          "model": "base",
          "language": "zh-CN"
        }
      }
    }
  }
}
```
