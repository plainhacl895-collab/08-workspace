---
name: weather
description: 天气查询技能，使用 wttr.in 和 Open-Meteo 免费服务，无需 API 密钥
homepage: https://clawhub.ai/steipete/weather
metadata: {"openclaw":{"emoji":"🌤️"}}
---

# Weather - 天气技能 🌤️

## 技能描述

使用 wttr.in 和 Open-Meteo 免费天气服务，无需 API 密钥。

**核心功能**：
- ✅ 快速天气查询
- ✅ 详细天气预报
- ✅ JSON 格式数据
- ✅ 可选 PNG 图片
- ✅ 无需 API 密钥

---

## 🔧 运行时要求

| 要求 | 状态 | 说明 |
|------|------|------|
| **curl** | ⚠️ 必需 | 用于 HTTP 请求 |
| **网络访问** | ⚠️ 必需 | wttr.in, open-meteo |
| **API 密钥** | ✅ 无需 | 免费服务 |

---

## 🌤️ wttr.in (主要服务)

### 快速查询

```bash
curl -s "wttr.in/London?format=3"
# 输出：London: ⛅️ +8°C
```

---

### 紧凑格式

```bash
curl -s "wttr.in/London?format=%l:+%c+%t+%h+%w"
# 输出：London: ⛅️ +8°C 71% ↙5km/h
```

**格式代码**：
- `%c` - 天气状况
- `%t` - 温度
- `%h` - 湿度
- `%w` - 风速
- `%l` - 地点
- `%m` - 月相

---

### 完整预报

```bash
curl -s "wttr.in/London?T"
```

---

### 使用技巧

| 技巧 | 示例 | 说明 |
|------|------|------|
| **空格编码** | `wttr.in/New+York` | URL 编码空格 |
| **机场代码** | `wttr.in/JFK` | 使用机场代码 |
| **单位** | `?m` (公制) `?u` (美制) | 温度单位 |
| **仅今天** | `?1` | 只看今天 |
| **仅当前** | `?0` | 只看当前 |
| **PNG 图片** | `curl -s "wttr.in/Berlin.png" -o /tmp/weather.png` | 保存为图片 |

---

## 📊 Open-Meteo (备用服务)

### JSON 查询

```bash
curl -s "https://api.open-meteo.com/v1/forecast?latitude=51.5&longitude=-0.12&current_weather=true"
```

**返回**：JSON 格式，包含温度、风速、天气代码

---

### 查找坐标

先查找城市坐标，然后查询。

**文档**: https://open-meteo.com/en/docs

---

## 📝 使用示例

### 示例 1: 查询上海天气

```bash
curl -s "wttr.in/Shanghai?format=3"
# 输出：Shanghai: ☀️ +25°C
```

---

### 示例 2: 详细天气

```bash
curl -s "wttr.in/Shanghai?format=%l:+%c+%t+%h+%w"
# 输出：Shanghai: ☀️ +25°C 60% →3km/h
```

---

### 示例 3: 保存天气图片

```bash
curl -s "wttr.in/Shanghai.png" -o "C:/Users/Huawei/Desktop/weather.png"
```

---

### 示例 4: JSON 格式

```bash
curl -s "https://api.open-meteo.com/v1/forecast?latitude=31.23&longitude=121.47&current_weather=true"
```

**返回**：
```json
{
  "latitude": 31.23,
  "longitude": 121.47,
  "current_weather": {
    "temperature": 25.0,
    "windspeed": 3.0,
    "weathercode": 0
  }
}
```

---

## ⚠️ 注意事项

### 网络访问

- ✅ 会访问 wttr.in 和 open-meteo
- ✅ 查询包含你问的地点
- ⚠️ 如果介意网络访问，不要启用此技能

---

### curl 依赖

- ⚠️ 需要系统有 curl 命令
- ✅ Windows 10+ 自带 curl
- ✅ 可用 `curl --version` 检查

---

### 隐私

- ⚠️ 查询地点会发送到 wttr.in
- ✅ 不存储个人数据
- ✅ 不需要注册

---

## 🔍 检查 curl

```bash
curl --version
```

**如果未安装**：
- Windows 10+: 自带
- macOS: 自带
- Linux: `sudo apt install curl` 或 `sudo yum install curl`

---

## 📊 天气代码

| 代码 | 含义 | 图标 |
|------|------|------|
| 0 | 晴天 | ☀️ |
| 1 | 主要晴天 | 🌤️ |
| 2 | 部分多云 | ⛅ |
| 3 | 多云 | ☁️ |
| 45, 48 | 雾 | 🌫️ |
| 51-55 | 毛毛雨 | 🌦️ |
| 61-65 | 雨 | 🌧️ |
| 71-75 | 雪 | ❄️ |
| 80-82 | 阵雨 | 🌦️ |
| 95-99 | 雷雨 | ⛈️ |

---

## 🌍 地点格式

| 格式 | 示例 | 说明 |
|------|------|------|
| **城市名** | `wttr.in/London` | 直接城市名 |
| **城市 + 国家** | `wttr.in/London,UK` | 避免重名 |
| **机场代码** | `wttr.in/JFK` | 机场代码 |
| **坐标** | `wttr.in/51.5,-0.12` | 纬度，经度 |
| **IP 地址** | `wttr.in/@` | 自动检测位置 |

---

## 📋 命令参考

### 快速查询

```bash
# 当前天气
curl -s "wttr.in/<地点>?format=3"

# 详细格式
curl -s "wttr.in/<地点>?format=%l:+%c+%t+%h+%w"

# 完整预报
curl -s "wttr.in/<地点>?T"

# 仅今天
curl -s "wttr.in/<地点>?1"

# 仅当前
curl -s "wttr.in/<地点>?0"
```

---

### JSON 查询

```bash
# Open-Meteo
curl -s "https://api.open-meteo.com/v1/forecast?latitude=<lat>&longitude=<lon>&current_weather=true"
```

---

### 保存图片

```bash
# PNG 格式
curl -s "wttr.in/<地点>.png" -o /tmp/weather.png
```

---

## 🔐 安全考虑

1. **网络访问** - 会访问外部服务
2. **位置查询** - 地点会发送到 wttr.in
3. **无凭证** - 不需要任何密钥
4. **无存储** - 不存储查询历史

---

## 📚 参考链接

- [wttr.in](https://wttr.in)
- [Open-Meteo](https://open-meteo.com/en/docs)
- [ClawHub 页面](https://clawhub.ai/steipete/weather)

---

*Remade for OpenClaw from ClawHub* 🔹
