# 娴忚鍣ㄨ嚜鍔ㄥ寲 Windows 浣跨敤缁忛獙

**鍒涘缓鏃ユ湡锛?* 2026-04-13  
**閫傜敤宸ュ叿锛?* agent-browser-clawdbot

---

## 鈿狅笍 閲嶈锛歐indows 涓婄殑姝ｇ‘鐢ㄦ硶

**闂锛?* agent-browser 鑷姩鍚姩 Chrome 鍦?Windows 涓婁細澶辫触

**閿欒淇℃伅锛?*
```
鉁?Chrome exited early (exit code: 0) without writing DevToolsActivePort
```

---

## 鉁?姝ｇ‘娴佺▼锛堝凡楠岃瘉锛?
### 姝ラ 1锛氬厛鍚姩 Chrome
鎵ц锛歚C:\Users\Huawei\.agent-browser\start-chrome.bat`

鎴栨墜鍔ㄥ懡浠わ細
```powershell
& "C:\Users\Huawei\.agent-browser\browsers\chrome-147.0.7727.56\chrome.exe" --remote-debugging-port=9222 --no-sandbox --disable-gpu --user-data-dir="C:\Users\Huawei\.agent-browser\user-data"
```

### 姝ラ 2锛氱瓑寰?5 绉?```powershell
Start-Sleep -Seconds 5
```

### 姝ラ 3锛氱敤 agent-browser 杩炴帴
```powershell
agent-browser --cdp 9222 open <缃戝潃> --snapshot
```

---

## 馃搵 甯哥敤鍛戒护妯℃澘

| 鎿嶄綔 | 鍛戒护 |
|------|------|
| 鎵撳紑缃戦〉 | `agent-browser --cdp 9222 open <URL>` |
| 鑾峰彇椤甸潰缁撴瀯 | `agent-browser --cdp 9222 snapshot -i --json` |
| 鐐瑰嚮鍏冪礌 | `agent-browser --cdp 9222 click @e2` |
| 濉啓琛ㄥ崟 | `agent-browser --cdp 9222 fill @e3 "鍐呭"` |
| 鎴浘 | `agent-browser --cdp 9222 screenshot page.png` |

---

## 馃毇 澶辫触鐨勬柟娉曪紙涓嶈灏濊瘯锛?
```powershell
# 杩欎簺閮戒細澶辫触锛?agent-browser --args "--no-sandbox" open ...
agent-browser --auto-connect ...
agent-browser open ...锛堟病鏈夋彁鍓嶅惎鍔?Chrome锛?```

---

## 馃挕 缁欑敤鎴凤紙浣充匠锛夌殑绠€鍖栨寚浠?
浣充匠鍙渶瑕佽锛?- "鎵撳紑灏忕孩涔?
- "鎵撳紑鏌愪釜缃戠珯"
- "鎴浘杩欎釜椤甸潰"

鍥㈠洟浼氳嚜鍔ㄦ墽琛岋細
1. 鍚姩 Chrome
2. 绛夊緟 5 绉?3. 杩炴帴骞舵墦寮€缃戦〉
4. 杩斿洖缁撴灉

---

## 馃搧 鐩稿叧鏂囦欢浣嶇疆

| 鏂囦欢 | 浣嶇疆 |
|------|------|
| 鍚姩鑴氭湰 | `C:\Users\Huawei\.agent-browser\start-chrome.bat` |
| Chrome 璺緞 | `C:\Users\Huawei\.agent-browser\browsers\chrome-147.0.7727.56\chrome.exe` |
| 鐢ㄦ埛鏁版嵁 | `C:\Users\Huawei\.agent-browser\user-data\` |
| 鎶€鑳戒綅缃?| `C:\Users\Huawei\.openclaw\workspace-tuantuan\skills\agent-browser-clawdbot\` |

