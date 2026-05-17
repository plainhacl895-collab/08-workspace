---
name: client-followup-reader
description: 客户完整跟进记录读取工具，优先读取 CSV 缓存（30 分钟内），自动回退 Excel 直读，支持分析、导出、JSON 输出
homepage: https://github.com/tuantuan-assistant/client-followup-reader
metadata: {"openclaw":{"emoji":"📋"}}
---

# Client Followup Reader - 客户跟进记录读取工具 📋

## 技能描述

专业读取客户所有跟进记录的工具，**智能缓存策略**，平衡速度和数据新鲜度。

**核心特性**：
- ✅ **智能缓存** - 优先读取 CSV 缓存（30 分钟内），自动回退 Excel
- ✅ **完整读取** - 不限跟进记录数量
- ✅ **深度分析** - 月度统计、关键词分析
- ✅ **多种输出** - 文本/JSON/导出文件
- ✅ **安静模式** - 只输出关键信息

---

## 🚀 使用方法

### 方式 1: 使用 CMD 脚本

```cmd
REM 基本用法（优先缓存）
cmd /c RUN_READ_ALL_FOLLOWUPS_V2.cmd <行号>

REM 显示所有记录
cmd /c RUN_READ_ALL_FOLLOWUPS_V2.cmd <行号> --all

REM 强制从 Excel 读取（忽略缓存）
cmd /c RUN_READ_ALL_FOLLOWUPS_V2.cmd <行号> --force

REM 刷新缓存
cmd /c RUN_READ_ALL_FOLLOWUPS_V2.cmd <行号> --refresh
```

### 方式 2: 直接使用 Python

```cmd
python tools\read-client-all-followups-v2.py --row <行号> [选项]
```

### 方式 3: 通过团团 CLI

```cmd
cmd /c RUN_TUANTUAN_qidong.cmd read-followups --client <行号> [选项]
```

---

## 📖 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--row <行号>` | **必需**，客户行号 | - |
| `--all` | 显示所有跟进记录 | 否 |
| `--limit <N>` | 显示最近 N 条 | 20 |
| `--export` | 导出到桌面 | 否 |
| `--json` | JSON 格式输出 | 否 |
| `--quiet` | 安静模式 | 否 |
| `--force` | 强制 Excel 读取 | 否 |
| `--refresh` | 刷新缓存 | 否 |

---

## 📊 缓存策略

### 缓存位置
```
C:\Users\Huawei\.openclaw\workspace-tuantuan\runtime\client_cache\client_<行号>_followups.json
```

### 缓存规则

| 情况 | 行为 |
|------|------|
| 缓存存在且<30 分钟 | ✅ 使用缓存（速度快） |
| 缓存不存在或>30 分钟 | 🔄 读取 Excel 并更新缓存 |
| 使用 `--force` | 🔄 强制读取 Excel |
| 使用 `--refresh` | 🔄 刷新缓存 |

### 缓存优势

- ⚡ **速度快** - JSON 读取比 Excel 快 10 倍
- 🔄 **自动更新** - 30 分钟自动刷新
- 💾 **离线可用** - Excel 关闭时也能读取

---

## 💡 使用示例

### 示例 1: 快速查看（使用缓存）

```cmd
cmd /c RUN_READ_ALL_FOLLOWUPS_V2.cmd 12
```

**输出**：
```
检查缓存...
✅ 使用缓存 (valid)
================================================================================
客户：刘先生微信 (行号:12)
等级：A | 预算：1500 万
数据来源：cache (valid)
================================================================================

跟进记录（共 56 条，显示 20 条）:
================================================================================

[  1] 2026-04-10
     通电话：邀约来看仁恒，客户说自己没空这段时间...

...

================================================================================
分析：总计 56 条 | 2025-12-10 至 2026-04-10
月度统计:
  2026-04: 2 条
  2026-03: 8 条
  2026-01: 1 条
  2025-12: 2 条
```

---

### 示例 2: 强制读取最新数据

```cmd
cmd /c RUN_READ_ALL_FOLLOWUPS_V2.cmd 12 --force
```

**输出**：
```
从 Excel 读取...
✅ 已更新缓存
...
数据来源：excel
```

---

### 示例 3: JSON 格式输出（程序调用）

```cmd
cmd /c RUN_READ_ALL_FOLLOWUPS_V2.cmd 12 --json
```

**输出**：
```json
{
  "client": {
    "row": 12,
    "name": "刘先生微信",
    "grade": "A",
    "budget": 1500
  },
  "followups": [...],
  "analysis": {
    "total_count": 56,
    "monthly_stats": {...},
    "keywords": {...}
  },
  "source": "cache",
  "timestamp": "2026-04-17T12:45:00"
}
```

---

### 示例 4: 导出到桌面

```cmd
cmd /c RUN_READ_ALL_FOLLOWUPS_V2.cmd 12 --export
```

**输出**：
```
✅ 已导出：C:\Users\Huawei\Desktop\client_12_followups.txt
```

---

## 🔧 技术实现

### 读取流程

```
开始
  ↓
检查缓存是否存在且<30 分钟？
  ↓
是 → 使用缓存（快速）
  ↓
否 → 读取 Excel（实时）
  ↓
更新缓存
  ↓
分析跟进记录
  ↓
输出结果
  ↓
结束
```

### 缓存文件格式

```json
{
  "client": {...},
  "followups": [...],
  "source": "excel",
  "timestamp": "2026-04-17T12:45:00"
}
```

---

## 📋 输出说明

### 客户信息

| 字段 | 说明 |
|------|------|
| `row` | Excel 行号 |
| `name` | 客户姓名 |
| `phone` | 电话 |
| `grade` | 等级 |
| `budget` | 预算（万） |
| `rooms` | 房型 |
| `district` | 区域 |

### 跟进记录

| 字段 | 说明 |
|------|------|
| `date` | 跟进日期 |
| `content` | 跟进内容 |
| `column` | Excel 列号 |

### 分析报告

| 字段 | 说明 |
|------|------|
| `total_count` | 总跟进数 |
| `time_span` | 时间跨度 |
| `monthly_stats` | 月度统计 |
| `keywords` | 关键词统计 |

---

## ⚠️ 注意事项

1. **首次读取较慢** - 需要从 Excel 读取，后续使用缓存
2. **缓存有效期 30 分钟** - 超时自动刷新
3. **Excel 必须关闭** - 直接读取时
4. **需要 Python 环境** - pywin32 库

---

## 🐛 故障排查

### 问题 1: "缓存不存在"

**解决**：首次使用会直接从 Excel 读取并创建缓存

### 问题 2: "Excel 读取失败"

**解决**：
- 检查 Excel 文件路径
- 确保 Excel 文件未打开
- 使用 `--force` 强制读取

### 问题 3: "跟进记录为空"

**解决**：
- 检查行号是否正确
- 确认跟进记录存在
- 使用 `--all` 显示全部

---

## 📚 相关文件

| 文件 | 用途 |
|------|------|
| `read-client-all-followups-v2.py` | 主脚本（Python） |
| `RUN_READ_ALL_FOLLOWUPS_V2.cmd` | 启动脚本（CMD） |
| `runtime/client_cache/` | 缓存目录 |

---

## 🎯 版本历史

- **v2.0** (2026-04-17) - 智能缓存版本
  - ✅ 优先读取缓存
  - ✅ 自动回退 Excel
  - ✅ 30 分钟自动刷新
  - ✅ 支持强制读取

- **v1.0** (2026-04-17) - 初始版本
  - ✅ 直接读取 Excel
  - ✅ 完整跟进记录
  - ✅ 分析功能

---

*Created by 团团助手 based on client followup reading requirements* 🔹
