---
name: xiaohongshu-property-research
description: 研究小红书房产博主和热门内容。搜索房产领域粉丝多、涨粉快的博主，分析其内容策略和成功秘诀，提取笔记链接。触发词：小红书房产研究、房产博主分析、小红书涨粉、房产内容研究、研究小红书房产
---

# 小红书房产研究技能

## 用途

帮助佳佳研究小红书房产领域做得好的博主，学习他们的内容策略，获取热门笔记链接。

## 工作流程

### 第一步：确保MCP服务运行

```bash
# 检查服务状态
curl -s -X POST http://localhost:18060/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{},"id":1}'

# 如果服务未运行，启动它
cd C:\Users\Huawei\.openclaw\workspace-tuantuan\tools\xiaohongshu-mcp
start /b xiaohongshu-mcp-windows-amd64.exe
```

### 第二步：使用研究脚本

```bash
# 搜索上海房产相关内容
cd C:\Users\Huawei\.openclaw\workspace-tuantuan\tools\xiaohongshu-mcp
node xhs-research.js 上海房产 10

# 搜索二手房相关内容
node xhs-research.js 上海二手房 10

# 搜索买房攻略
node xhs-research.js 上海买房攻略 10
```

### 第三步：分析结果

从搜索结果中提取：
1. 博主昵称
2. 粉丝数（需调用 user_profile 工具）
3. 互动数据（点赞、收藏、评论、分享）
4. 笔记标题和链接
5. 内容类型（图文/视频）

### 第四步：深入分析头部博主

对粉丝最多、互动最高的 3-5 个博主，获取主页详情：

```bash
# 调用 user_profile 工具（需要通过 MCP API）
# 需要 user_id 和 xsec_token（从搜索结果中获取）
```

从主页提取：
- 总粉丝数
- 笔记总数
- 内容方向（干货分享/房源推荐/市场分析/个人IP）
- 更新频率
- 爆款笔记的特征

### 第五步：提炼成功秘诀

基于收集的数据，分析每个博主的：

1. **内容定位** — 他们主打什么方向？
2. **内容形式** — 图文还是视频？封面风格？
3. **标题套路** — 用什么标题吸引点击？
4. **互动策略** — 怎么引导点赞收藏评论？
5. **更新节奏** — 多久发一篇？
6. **差异化优势** — 和同行比，他们做对了什么？

### 第六步：输出报告

整理成结构化报告发给佳佳：

```
📊 小红书房产博主研究报告

== 热门笔记 TOP 5 ==

1. 《标题》
   博主: @昵称
   类型: 视频/图文
   点赞: XX | 收藏: XX | 评论: XX
   链接: https://www.xiaohongshu.com/explore/xxx
   特点: ...

2. ...

== 可借鉴的策略 ==

1. 标题用数字+痛点：如"上海买房必看的5个坑"
2. 封面统一风格...
3. ...

== 热门博主分析 ==

1. @博主A
   粉丝：XX万
   内容方向：上海买房攻略
   成功秘诀：...
```

## 注意事项

- 小红书MCP服务需要保持运行（localhost:18060）
- 首次使用需要扫码登录（xiaohongshu-login-windows-amd64.exe）
- 数据来自真实小红书搜索，包含互动数据（点赞/收藏/评论/分享）
- 每次研究聚焦一个细分方向（如"上海二手房"），不要泛泛搜索
- 搜索结果可能包含广告或推广内容，需要人工筛选

## 常用搜索关键词

- `上海房产` / `上海二手房` / `上海买房`
- `房产博主` / `房产知识` / `买房攻略`
- `上海楼市` / `上海房价` / `上海学区房`
