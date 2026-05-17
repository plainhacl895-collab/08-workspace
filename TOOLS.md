# TOOLS.md

## 统一入口

当前生产命令统一从这里进入：

`C:\Users\Huawei\Desktop\workspace-tuantuan\tools\RUN_TUANTUAN_qidong.cmd`

实际执行链路：

`RUN_TUANTUAN_qidong.cmd` -> `main.py` -> `tools/client|property|followup|experience|core|utils`

## 当前结构说明

- `tools/main.py`：当前生产入口
- `tools/client/`：客户查询、更新、盘点
- `tools/property/`：房源查询、匹配、推荐
- `tools/followup/`：跟进写入与修改
- `tools/experience/`：经验草稿、审阅、批准、查询
- `tools/core/`：健康检查、缓存刷新、核心保护
- `tools/tuantuan_cli.py`、`tools/tuantuan_cli_zhiling.py`：历史单体脚本，默认不作为生产入口

## 当前可用核心命令

### 系统

- `cmd /c tools\RUN_TUANTUAN_qidong.cmd doctor`
- `cmd /c tools\RUN_TUANTUAN_qidong.cmd refresh`
- `cmd /c tools\RUN_TUANTUAN_qidong.cmd core-guard-status`
- `cmd /c tools\RUN_TUANTUAN_qidong.cmd core-guard-freeze`

### 客户

- `cmd /c tools\RUN_TUANTUAN_qidong.cmd client-search --query "<姓名/电话/行号>"`
- `cmd /c tools\RUN_TUANTUAN_qidong.cmd client-context --query "<姓名/电话/行号>"`
- `cmd /c tools\RUN_TUANTUAN_qidong.cmd client-update --query "<客户>" --set key=value`
- `cmd /c tools\RUN_TUANTUAN_qidong.cmd client-update-from-text --query "<客户>" --instruction "<修改意见>"`
- `cmd /c tools\RUN_TUANTUAN_qidong.cmd client-triage --limit 10`
- `cmd /c tools\RUN_TUANTUAN_qidong.cmd client-daily-brief --limit 8`
- `cmd /c tools\RUN_TUANTUAN_qidong.cmd client-grade-adjust --query "<客户>" --new-grade "<等级>"`

### 跟进

- `cmd /c tools\RUN_TUANTUAN_qidong.cmd write-followup --query "<客户>" --date YYYY-MM-DD --content "<内容>" [--dry-run]`
- `cmd /c tools\RUN_TUANTUAN_qidong.cmd update-followup --query "<客户>" --date YYYY-MM-DD --instruction "<修改意见>" [--dry-run]`

### 房源

- `cmd /c tools\RUN_TUANTUAN_qidong.cmd property-search --query "<关键词>"`
- `cmd /c tools\RUN_TUANTUAN_qidong.cmd property-detail --house-id <12位房源编号>`
- `cmd /c tools\RUN_TUANTUAN_qidong.cmd client-match-properties --query "<客户>" --limit 10`
- `cmd /c tools\RUN_TUANTUAN_qidong.cmd client-recommend-properties --query "<客户>" --candidate-limit 5 --final-limit 3`

### 经验

- `cmd /c tools\RUN_TUANTUAN_qidong.cmd experience-draft --text "<内容>"`
- `cmd /c tools\RUN_TUANTUAN_qidong.cmd experience-draft-list`
- `cmd /c tools\RUN_TUANTUAN_qidong.cmd experience-draft-revise --draft-id "<ID>" --instruction "<修改意见>"`
- `cmd /c tools\RUN_TUANTUAN_qidong.cmd experience-approve --draft-id "<ID>"`
- `cmd /c tools\RUN_TUANTUAN_qidong.cmd experience-query --query "<问题>"`

## 外围工作流

以下命令不走 `main.py`，属于独立辅助流程：

- 房源抓取：`tools\RUN_HOUSE_GRAB.cmd`
- 房源详情：`tools\RUN_HOUSE_DETAIL.cmd`
- 每日跟进计划：`tools\RUN_DAILY_FOLLOW_PLAN_jihua.cmd`
- YouTube字幕：`tools\youtube_transcript.py`（详见下方）

## YouTube字幕工具

脚本：`tools\youtube_transcript.py`
启动器：`tools\RUN_YOUTUBE_TRANSCRIPT.cmd`

### 调用方式

```cmd
python tools\youtube_transcript.py "<URL>"
python tools\youtube_transcript.py "<URL>" --text-only --timestamps
python tools\youtube_transcript.py "<URL>" --browser-cookie
```

### 选项

| 选项 | 说明 |
|------|------|
| `--text-only` | 只输出纯文本 |
| `--timestamps` | 带时间戳 |
| `--language zh,en` | 指定语言（默认优先中文） |
| `--browser-cookie` | 使用Chrome登录Cookie，防YouTube封锁（推荐） |

### 输出

JSON格式，包含 `video_id`、`segment_count`、`full_text`、`timestamped_text`。

### 工作原理

双后端策略：优先 `youtube-transcript-api`，失败自动切换 `yt-dlp`。本地运行绕过YouTube对云服务器IP的封锁。

### 依赖

Windows Python311已安装 `youtube-transcript-api` 和 `yt-dlp`，无需额外安装。

## 约束

1. 不允许机器人擅自新增第二入口。
2. 不允许机器人因为“看起来更整洁”就批量搬文件。
3. 结构不清楚时，先看 `workspace/docs/architecture.md`。

