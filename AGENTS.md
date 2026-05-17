# AGENTS.md

## 启动顺序

每次开始处理业务前，按这个顺序读取：

1. `IDENTITY.md` — 我是谁
2. `USER.md` — 用户信息
3. `SOUL.md` — 核心行为准则
4. 最近两天的 `memory/YYYY-MM-DD.md` — 近期记忆
5. `TOOLS.md` — 可用工具命令
6. `EXEC_RULES.md` — 执行规则

## 当前生产入口

- 统一命令入口：`tools/RUN_TUANTUAN_qidong.cmd`
- 实际程序入口：`tools/main.py`
- 当前生产代码采用模块化结构：
  `tools/client`、`tools/property`、`tools/followup`、`tools/experience`、`tools/core`、`tools/utils`
- `tools/tuantuan_cli.py` 和 `tools/tuantuan_cli_zhiling.py` 保留为历史单体版本，不是当前生产入口

## 当前工作方式

- 先查事实，再做判断
- 客户问题先查客户，房源问题先查房源
- 多命中、信息不足、缓存过旧时，停止猜测并说明缺口
- 写入类操作必须明确唯一客户和唯一日期
- 不允许机器人自行整理目录、增加新入口、批量搬文件，除非用户明确授权

## 目录认知

- `tools/` 是当前在用的代码入口
- `biaoge_kehu_caozuo_xitong/` 保存 Excel 业务资产和旧版脚本说明
- `runtime/`、`memory/` 是运行产物和记忆，不当作核心源码
- `skills/` 存放各类技能脚本
