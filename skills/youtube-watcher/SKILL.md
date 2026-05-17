---
name: youtube-watcher
description: Fetch and read transcripts from YouTube videos. Use when you need to summarize a video, answer questions about its content, or extract information from it. Uses Windows local script to bypass cloud IP bans.
author: michael gathara / Hermes Agent
version: 2.0.0
triggers:
  - "watch youtube"
  - "summarize video"
  - "video transcript"
  - "youtube summary"
  - "analyze video"
metadata: {"clawdbot":{"emoji":"📺","requires":{"bins":["yt-dlp","python"]}}}
---

# YouTube Watcher

Fetch transcripts from YouTube videos to enable summarization, QA, and content extraction.
**Architecture:** Uses `tools/youtube_transcript.py` (yt-dlp + API backend) to bypass cloud IP bans.

## Usage

### Get Transcript

Retrieve the text transcript of a video using the shared Windows tool.

```bash
python tools\youtube_transcript.py "URL"
```

### Recommended Flags

| Flag | Description |
|------|-------------|
| `--text-only` | Output plain text only (no JSON). |
| `--browser-cookie` | **Highly Recommended**: Uses Chrome login cookie to prevent blocking. |
| `--timestamps` | Include timestamps in output. |
| `--language zh,en` | Specify language priority. |

### Example

**Summarize a video:**

1. Get the transcript (always use --browser-cookie for stability):
   ```bash
   python tools\youtube_transcript.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --browser-cookie --text-only
   ```
2. Read the output and summarize it for the user.

## Notes

- The script is located at `tools/youtube_transcript.py`.
- **Backend Strategy:**
  1. Tries `youtube-transcript-api` first.
  2. Falls back to `yt-dlp` (downloads VTT).
- **IP Ban Protection:** Uses `--cookies-from-browser chrome` when `--browser-cookie` is passed.
- **Dependencies:** `yt-dlp` and `youtube-transcript-api` are installed in Windows Python 3.11.
