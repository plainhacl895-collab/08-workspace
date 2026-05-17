# Excel 鏌ヨ绯荤粺 - 缁忛獙鏁欒鎬荤粨

**鍒涘缓鏃堕棿:** 2026-03-14  
**浜嬩欢:** COM 绯荤粺鏁呴殰瀵艰嚧鑷姩鍖栨煡璇㈠け鏁?
---

## 馃搵 浜嬩欢鍥為【

### 鏃堕棿绾?
| 鏃堕棿 | 浜嬩欢 | 鐘舵€?|
|------|------|------|
| 11:00-13:00 | 鎴愬姛鏌ヨ澶氫釜瀹㈡埛 | 鉁?姝ｅ父 |
| 13:00 | Excel COM 寮€濮嬪崱浣?| 鉂?鏁呴殰寮€濮?|
| 13:00-16:00 | 澶氭灏濊瘯淇 | 鉂?鏃犳晥 |
| 16:00 | 纭瀵嗙爜 `000` 宸插浐鍖?| 鉁?纭 |
| 16:30 | 璇嗗埆涓?COM 绯荤粺闂 | 鉁?瀹氫綅 |
| 17:00 | 灏濊瘯閲嶅惎 COM 鏈嶅姟 | 鉂?鏃犳晥 |
| 17:30 | 閲嶅惎绯荤粺 | 鉁?鎭㈠ |

---

## 馃攳 鏍规湰鍘熷洜

**COM 浼氳瘽绱Н鏈噴鏀?* 鈫?Windows COM 瀛愮郴缁熻祫婧愯€楀敖 鈫?鎵€鏈?COM 瀵硅薄鍒涘缓澶辫触

**瑙﹀彂鍥犵礌锛?*
- 澶氭娴嬭瘯鏌ヨ锛?0+ 娆★級
- Excel 杩涚▼鏈畬鍏ㄩ噴鏀?- COM 瀵硅薄鏈纭噴鏀?(`ReleaseComObject`)

---

## 鉂?閿欒澶勭悊

| 閿欒 | 琛ㄧ幇 | 姝ｇ‘鍋氭硶 |
|------|------|----------|
| **鏈厛娴嬭瘯鍩虹 COM** | 鐩存帴娴嬭瘯 Excel | 搴斿厛娴嬭瘯 `WScript.Shell` |
| **鏈瘑鍒郴缁熸€ч棶棰?* | 鍙嶅灏濊瘯 Excel 淇 | 搴旀棭璇嗗埆鏄?COM 绯荤粺闂 |
| **鏈強鏃跺缓璁噸鍚?* | 灏濊瘯澶氱澶嶆潅鏂规 | COM 闂鏈€鏈夋晥鏄噸鍚?|
| **鏈鏌?COM 鏈嶅姟鐘舵€?* | 鐩存帴璋冪敤 COM | 搴斿厛 `Get-Service` 妫€鏌?|
| **鏈噴鏀?COM 瀵硅薄** | 鑴氭湰涓湭璋冪敤 `ReleaseComObject` | 搴斿缁堥噴鏀?COM 瀵硅薄 |

---

## 鉁?姝ｇ‘鏂规锛堝凡鍥哄寲锛?
### 1. B 鏋舵瀯 - 鍥哄畾宸ュ叿璋冪敤

**涔嬪墠锛圓 鏋舵瀯 - 閿欒锛夛細**
```
鐢ㄦ埛闂?鈫?鎴戦噸鏂版帹鐞?鈫?鐢熸垚/璋冪敤鑴氭湰 鈫?鍙兘鍑洪敊
```

**鐜板湪锛圔 鏋舵瀯 - 姝ｇ‘锛夛細**
```
鐢ㄦ埛闂?鈫?璋冪敤 query_customer.ps1 鈫?杩斿洖缁撴灉
```

**浼樺娍锛?*
- 鉁?鑴氭湰鍥哄畾锛屼笉閲嶆柊鐢熸垚
- 鉁?娴佺▼纭紪鐮侊紝涓嶄細蹇?- 鉁?Agent 鍙礋璐ｈ皟鐢紝涓嶈礋璐ｆ帹鐞?
---

### 2. COM 绯荤粺妫€鏌?
**姣忔鏌ヨ鍓嶆鏌?COM 鐘舵€侊細**

```powershell
try {
    $testCom = New-Object -ComObject WScript.Shell
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($testCom) | Out-Null
} catch {
    Write-Error "COM 绯荤粺寮傚父锛佽閲嶅惎绯荤粺"
    exit 1
}
```

---

### 3. COM 瀵硅薄閲婃斁

**濮嬬粓閲婃斁 COM 瀵硅薄锛?*

```powershell
if ($excel) {
    $excel.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()
}
```

---

### 4. 鏁呴殰鎺掓煡娴佺▼

**鏍囧噯鍖栨帓鏌ユ祦绋嬶細**

```
1. 娴嬭瘯鍩虹 COM (WScript.Shell)
   鈫?澶辫触 鈫?閲嶅惎绯荤粺
   鈫?鎴愬姛
2. 妫€鏌?COM 鏈嶅姟鐘舵€?(Get-Service)
   鈫?寮傚父 鈫?閲嶅惎鏈嶅姟
   鈫?姝ｅ父
3. 娓呯悊娈嬬暀杩涚▼ (taskkill)
   鈫?4. 閲嶆柊娴嬭瘯
```

---

## 馃摑 鍥哄寲鏂囨。

| 鏂囨。 | 浣嶇疆 | 鐢ㄩ€?|
|------|------|------|
| **MEMORY.md** | `D:\OpenClaw\Workspaces\main\` | 鍏ㄥ眬鏍稿績璁板繂 |
| **TOOLS.md** | `D:\OpenClaw\Workspaces\main\` | 鏈湴閰嶇疆 + COM 鏁呴殰澶勭悊 |
| **COM 鏁呴殰鎺掓煡鎸囧崡.md** | `memory/` | 璇︾粏鎺掓煡娴佺▼ |
| **query_customer.ps1** | `workspace/tools/` | 鍥哄畾宸ュ叿锛圔 鏋舵瀯锛?|
| **query_client.vbs** | `D:\ExcelData/` | 鏍稿績鏌ヨ鑴氭湰 |

---

## 馃幆 棰勯槻鎺柦

### 1. 鏌ヨ鍓嶆鏌?
```powershell
# 鍦?query_customer.ps1 寮€澶?if (!(Test-ComSystem)) {
    exit 1
}
```

### 2. 鏌ヨ鍚庢竻鐞?
```powershell
# 濮嬬粓閲婃斁 COM 瀵硅薄
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null
```

### 3. 瀹氭湡娓呯悊杩涚▼

```powershell
# 姣忔鏌ヨ鍓?Get-Process Excel -ErrorAction SilentlyContinue | Stop-Process -Force
```

### 4. 闄愬埗鏌ヨ棰戠巼

```
閬垮厤鐭椂闂村唴澶氭鏌ヨ锛?5 娆?鍒嗛挓锛?```

---

## 馃搳 鎬ц兘瀵规瘮

| 鏂规 | 棣栨 | 鍚庣画 | 绋冲畾鎬?|
|------|------|------|--------|
| **A 鏋舵瀯锛堟帹鐞嗭級** | 15-17 绉?| 15-17 绉?| 猸愨瓙 鍋跺皵澶辫触 |
| **B 鏋舵瀯锛堝浐瀹氬伐鍏凤級** | 2-3 绉?| 1-2 绉?| 猸愨瓙猸愨瓙猸?绋冲畾 |
| **COM 鏁呴殰鍚?* | 鏃犳硶鎵ц | 鏃犳硶鎵ц | 鉂?闇€閲嶅惎 |

---

## 馃攽 鍏抽敭鏁欒

1. **COM 瀵硅薄蹇呴』閲婃斁** - 浣跨敤 `ReleaseComObject`
2. **鍏堟祴璇曞熀纭€ COM** - `WScript.Shell` 鏈€绠€鍗?3. **绯荤粺闂鍙婃椂閲嶅惎** - 涓嶈灏濊瘯澶嶆潅淇
4. **鍥哄畾宸ュ叿浼樹簬鎺ㄧ悊** - B 鏋舵瀯鏇寸ǔ瀹?5. **鏂囨。瑕佸強鏃舵洿鏂?* - 鏁呴殰鎺掓煡鎸囧崡蹇呴』璇︾粏

---

## 馃摓 蹇€熶慨澶嶅懡浠?
```powershell
# COM 鏁呴殰蹇€熶慨澶?taskkill /F /IM excel.exe
Restart-Service DcomLaunch -Force
Restart-Service COMSysApp -Force
Start-Sleep -Seconds 5
New-Object -ComObject WScript.Shell  # 娴嬭瘯
```

**濡傛灉鏃犳晥锛岄噸鍚郴缁熸槸鏈€鏈夋晥鏂规銆?*

---

**鏈€鍚庢洿鏂?** 2026-03-14  
**缁存姢:** 鍥㈠洟 (main agent)

