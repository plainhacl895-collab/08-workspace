---
name: gongzuoqu-yunwei
description: 团团工作空间运维规范 — 脚本位置、文件安全、路径协议、双 Agent 共用规则。
---
# 团团工作空间运维规范 (Tuantuan Workspace Operations)

## 0. 单一脚本源原则（红线）

**所有实际运行的业务脚本必须且只能存在于团团工作空间：**
`C:\Users\Huawei\.openclaw\workspace-tuantuan\`

*   **Hermes（上上签）和团团共用同一套脚本和技能**。
*   **Hermes 自己的地盘（`/mnt/d/HermesAgent/`、`~/.hermes/skills/`）不允许存放任何业务脚本和技能**。
*   如果某脚本在两个地方都有副本，**以团团工作区为准，删除另一份**。
*   技能文档也应放在团团工作区的 `skills/` 目录下，与脚本形成闭环。

### 为什么这么做？
1. 团团和 Hermes 都能读取同一份代码，避免"改了一个没改另一个"的版本分裂。
2. 所有路径统一，不存在"团团用的是 C 盘版，Hermes 用的是 D 盘版"的混乱。
3. 技能文档和技能脚本在同一工作区，两个 AI 都能读取和执行。

### 团团工作空间结构
```
C:\Users\Huawei\.openclaw\workspace-tuantuan\
├── tools\                          ← 业务脚本（.py, .cmd）
│   ├── daily_follow_plan_v2_jihua.py   # 每日跟进建议生成
│   ├── daily_follow_check_v2_jiancha.py # 晚间复盘
│   ├── house_grab_pipeline_zhuapai.py   # 房源抓取
│   └── RUN_*.cmd                      # 一键启动脚本
│
├── skills\                         ← 技能文档（SKILL.md）
│   └── 每日跟进建议\SKILL.md
│   └── followup-plan\SKILL.md
│   └── ...
│
├── runtime\                        ← 运行时数据
│   ├── tuantuan_cache.json          # 客户/房源缓存
│   └── daily_follow_plan\           # 跟进计划状态
│
└── biaoge_kehu_caozuo_xitong\      ← 表格操作子系统
```

## 1. 废弃路径（严禁引用）

| 路径 | 状态 |
|------|------|
| `D:\ExcelData\` | 已彻底废弃 |
| `D:\HermesAgent\core\` | **已废弃**，脚本已迁移到团团工作区 |
| `D:\HermesAgent\data\` | **已废弃**，运行时数据在团团工作区 `runtime/` |
| `D:\HermesAgent\scripts\` | **已废弃**，启动脚本在团团工作区 `tools/` |

## 2. Excel 安全规则（.xlsm 红线）

**NEVER use `openpyxl` to write/modify `.xlsm` files.**
*   **原因**：会剥离 VBA 宏，破坏文件结构（文件大小从 ~2.2MB 降到 ~1.6MB）。
*   **安全方法**：必须用 `win32com.client`（Excel COM 对象）。
*   **验证**：写入后检查文件大小，如果下降 >10%，立即从备份回滚。

### Excel 防占用
*   遇到 Excel 占用 → **立即 `taskkill /F /IM EXCEL.EXE` 等 4 秒 → 继续**，不询问用户。
*   写入前强制 taskkill + 检测文件锁 + COM 释放 try/except + finally 块再次 taskkill。

## 3. 动态列检测（跟进写入）
*   **不要猜测列号**。
*   **流程**：从右向左扫描**第 11 行**（日期行）。
    *   如果 `Last_Date == Today`：写入现有列。
    *   如果 `Last_Date != Today`：写入 `Last_Col + 1`。

## 4. 自动化备份协议
写入 Excel 前：
1.  **快照**：复制 `daily_followup.xlsm` 到备份目录 `daily_followup_YYYYMMDD_HHMMSS.xlsm`
2.  **执行**：用 `win32com` 修改
3.  **验证**：检查文件完整性（大小/宏存在）

## 5. API 限流通用规则（百炼 Coding Plan）

*   **端点**：`https://coding.dashscope.aliyuncs.com/v1`
*   **套餐**：Coding Plan Pro（200 元/月），限流 **30,000 RPM / 5,000,000 TPM**
*   **防限流**：每次 API 调用成功后 `sleep(5~10s)` 冷却
*   **429 重试**：指数退避，`sleep(60s × attempt)`
*   **不盲目加固定延迟**：必须先查清实际限流指标，再据此计算 sleep 时间

## 6. 脚本 Telegram 通知规则

*   **后台脚本禁止持续消息轰炸**。
*   允许在 **Excel 被占用等待时** 发**单条** Telegram 通知提醒用户手动关闭。
*   其他场景静默，由 Hermes 汇总汇报结果。

## 7. WSL ↔ Windows 路径适配

*   **WSL 环境下**：使用 `/mnt/c/Users/Huawei/.openclaw/workspace-tuantuan/` 前缀
*   **Windows 环境下**：使用 `C:\Users\Huawei\.openclaw\workspace-tuantuan\` 前缀
*   脚本应能自动检测环境或提供对应的 `.cmd` 启动器处理路径转换

## 8. 缓存刷新

*   缓存文件：`C:\Users\Huawei\.openclaw\workspace-tuantuan\runtime\tuantuan_cache.json`
*   COM 读取 12 万+ 单元格可能卡死 → 修改 `source.workbook_mtime` 为当前时间戳可跳过 COM 读取
*   遇到僵尸态卡死用 `force_build_cache()` 绕过
