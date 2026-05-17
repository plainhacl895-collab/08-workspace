# Excel COM 鎺ュ彛璇诲彇涓枃涔辩爜闂瑙ｅ喅鏂规

**鎶ュ憡鐢熸垚鏃堕棿:** 2026-03-16  
**闂绫诲瀷:** Windows Excel COM 鑷姩鍖栦腑鏂囩紪鐮侀棶棰?
---

## 馃搵 闂姒傝堪

鍦ㄤ娇鐢?PowerShell銆乂BScript 鎴栧叾浠栬剼鏈瑷€閫氳繃 COM 鎺ュ彛鑷姩鍖?Excel 鏃讹紝璇诲彇鍖呭惈涓枃瀛楃鐨勫崟鍏冩牸鍐呭鏃剁粡甯稿嚭鐜颁贡鐮侀棶棰樸€傝繖鏄竴涓暱鏈熷瓨鍦ㄧ殑鎶€鏈棶棰橈紝鍦?2024-2026 骞存湡闂翠粛鐒跺奖鍝嶈澶氱敤鎴枫€?
### 鍏稿瀷鐥囩姸
- 璇诲彇鐨勪腑鏂囨樉绀轰负 ``銆乣???` 鎴栧叾浠栦贡鐮佸瓧绗?- VBA 涓甯告樉绀虹殑鍐呭锛屽湪 PowerShell/VBScript 涓樉绀轰负涔辩爜
- 淇濆瓨鍚庣殑鏂囦欢鍦ㄥ叾浠栫郴缁熶腑鏃犳硶姝ｇ‘鏄剧ず涓枃

---

## 馃攳 闂鏍规簮鍒嗘瀽

### 1. 缂栫爜涓嶅尮閰嶏紙涓昏鍘熷洜锛?```
鈹屸攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?鈹? Excel 鍐呴儴瀛樺偍          COM 鎺ュ彛浼犺緭         鑴氭湰寮曟搸鎺ユ敹    鈹?鈹? Unicode (UTF-16LE)  鈫? BSTR 瀛楃涓?   鈫?  绯荤粺榛樿缂栫爜     鈹?鈹?                          鈫?                                  鈹?鈹?                   浠ｇ爜椤佃浆鎹㈠け璐?                             鈹?鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?```

### 2. 鍏蜂綋鍘熷洜
| 鍘熷洜 | 璇存槑 |
|------|------|
| **绯荤粺鍖哄煙璁剧疆** | Windows 闈?Unicode 绋嬪簭鐨勮瑷€璁剧疆褰卞搷 COM 瀛楃涓茶浆鎹?|
| **PowerShell 鐗堟湰** | PowerShell 5.1 浣跨敤 .NET Framework锛岀紪鐮佸鐞嗕笌 7+ 涓嶅悓 |
| **Excel 鐗堟湰** | 32 浣?vs 64 浣?Excel COM 鎺ュ彛琛屼负鐣ユ湁宸紓 |
| **鏂囦欢缂栫爜** | .xlsm/.xlsx 鏂囦欢鍐呴儴 XML 浣跨敤 UTF-8锛屼絾 COM 鎺ュ彛杩斿洖 UTF-16 |
| **鎺у埗鍙拌緭鍑?* | PowerShell 鎺у埗鍙伴粯璁ょ紪鐮?(GBK/UTF-8) 褰卞搷鏄剧ず |

---

## 鉁?瑙ｅ喅鏂规姹囨€?
### 鏂规涓€锛氫娇鐢?xlwings锛圥ython锛夆瓙 鎺ㄨ崘

**浼樼偣:**
- 璺ㄥ钩鍙版敮鎸?(Windows/macOS)
- 鑷姩澶勭悊缂栫爜闂
- 鏀寔 Pandas DataFrame 鏃犵紳闆嗘垚
- 娲昏穬缁存姢锛?025-2026 骞存寔缁洿鏂?
**缂虹偣:**
- 闇€瑕佸畨瑁?Python 鐜
- 闇€瑕佸畨瑁?xlwings 搴?
**瀹夎:**
```bash
pip install xlwings
```

**浠ｇ爜绀轰緥:**
```python
import xlwings as xw

# 鏂规硶 1: 鐩存帴鎵撳紑鐜版湁鏂囦欢
wb = xw.Book(r'D:\ExcelData\姣忔棩璺熻繘.xlsm')
sheet = wb.sheets['Sheet1']

# 璇诲彇涓枃鍐呭锛堣嚜鍔ㄦ纭鐞嗙紪鐮侊級
value = sheet.range('A1').value
print(value)  # 涓枃姝ｅ父鏄剧ず

# 鏂规硶 2: 浣跨敤 App 瀵硅薄
app = xw.App(visible=False)
wb = app.books.open(r'D:\ExcelData\姣忔棩璺熻繘.xlsm')
sheet = wb.sheets['Sheet1']
data = sheet.used_range.value
app.quit()
```

**xlwings Lite (2025 鏂板姛鑳?:**
- 鏃犻渶鏈湴 Python 瀹夎
- 閫氳繃 Excel 鍔犺浇椤圭洿鎺ヨ繍琛?- 閫傚悎閮ㄧ讲缁欐渶缁堢敤鎴?
---

### 鏂规浜岋細PowerShell + 姝ｇ‘缂栫爜澶勭悊

**浼樼偣:**
- 鏃犻渶棰濆瀹夎
- 鍘熺敓 Windows 鏀寔

**缂虹偣:**
- 闇€瑕佹墜鍔ㄥ鐞嗙紪鐮?- 浠ｇ爜鐩稿澶嶆潅

**浠ｇ爜绀轰緥 (2025 鎺ㄨ崘鍋氭硶):**
```powershell
# 璁剧疆杈撳嚭缂栫爜涓?UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# 鍒涘缓 Excel COM 瀵硅薄
$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false

# 鎵撳紑宸ヤ綔绨?$workbook = $excel.Workbooks.Open("D:\ExcelData\姣忔棩璺熻繘.xlsm")
$worksheet = $workbook.Worksheets.Item("Sheet1")

# 璇诲彇鍗曞厓鏍煎唴瀹?$cellValue = $worksheet.Cells.Item(1, 1).Text

# 姝ｇ‘澶勭悊缂栫爜 - 鏂规硶 1: 浣跨敤 Marshal
$value = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [System.Runtime.InteropServices.Marshal]::StringToHGlobalAuto($cellValue)
)

# 杈撳嚭
Write-Output $value

# 娓呯悊
$workbook.Close($false)
$excel.Quit()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null
```

**鏀硅繘鐗堟湰 (浣跨敤 ADODB 杈呭姪):**
```powershell
function Read-ExcelCell {
    param(
        [string]$FilePath,
        [string]$SheetName,
        [int]$Row,
        [int]$Column
    )
    
    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = $false
    
    $wb = $excel.Workbooks.Open($FilePath)
    $ws = $wb.Worksheets.Item($SheetName)
    
    $rawValue = $ws.Cells.Item($Row, $Column).Value2
    
    # 寮哄埗杞崲涓哄瓧绗︿覆骞跺鐞嗙紪鐮?    if ($rawValue -ne $null) {
        $stringValue = [string]$rawValue
        # 濡傛灉鏄腑鏂囷紝纭繚姝ｇ‘缂栫爜
        $bytes = [System.Text.Encoding]::Unicode.GetBytes($stringValue)
        $result = [System.Text.Encoding]::UTF8.GetString($bytes)
        Write-Output $result
    }
    
    $wb.Close($false)
    $excel.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($excel) | Out-Null
}
```

---

### 鏂规涓夛細VBScript + ADODB.Stream 缂栫爜杞崲

**浼樼偣:**
- 鏃犻渶 Python
- 閫傚悎浼犵粺鑴氭湰鐜

**缂虹偣:**
- 浠ｇ爜澶嶆潅
- 缁存姢鎴愭湰楂?
**浠ｇ爜绀轰緥:**
```vbscript
Option Explicit

Dim excel, workbook, worksheet
Dim cellValue, stream

' 鍒涘缓 Excel 瀵硅薄
Set excel = CreateObject("Excel.Application")
excel.Visible = False
excel.DisplayAlerts = False

' 鎵撳紑宸ヤ綔绨?Set workbook = excel.Workbooks.Open("D:\ExcelData\姣忔棩璺熻繘.xlsm")
Set worksheet = workbook.Worksheets("Sheet1")

' 璇诲彇鍗曞厓鏍?cellValue = worksheet.Cells(1, 1).Value

' 浣跨敤 ADODB.Stream 杩涜缂栫爜杞崲
Set stream = CreateObject("ADODB.Stream")
stream.Type = 2  ' adTypeText
stream.Charset = "utf-8"
stream.Open
stream.WriteText cellValue
stream.Position = 0
stream.Type = 1  ' adTypeBinary
stream.Position = 2  ' Skip BOM
Dim binaryData
binaryData = stream.Read()

stream.Position = 0
stream.Charset = "unicode"
stream.Type = 2
stream.Write binaryData
stream.Position = 0
Dim convertedValue
convertedValue = stream.ReadText()

WScript.Echo convertedValue

' 娓呯悊
stream.Close()
workbook.Close False
excel.Quit
Set stream = Nothing
Set worksheet = Nothing
Set workbook = Nothing
Set excel = Nothing
```

---

### 鏂规鍥涳細浣跨敤 openpyxl锛堜粎閫傜敤浜?.xlsx 鏂囦欢锛?
**浼樼偣:**
- 绾?Python锛屾棤闇€ Excel 瀹夎
- 缂栫爜澶勭悊鑷姩姝ｇ‘
- 杞婚噺绾?
**缂虹偣:**
- 涓嶆敮鎸?.xlsm 瀹忔枃浠?- 涓嶆敮鎸?COM 鑷姩鍖栧姛鑳?
**瀹夎:**
```bash
pip install openpyxl
```

**浠ｇ爜绀轰緥:**
```python
from openpyxl import load_workbook

# 鍔犺浇宸ヤ綔绨?wb = load_workbook(filename=r'D:\ExcelData\鏁版嵁鏂囦欢.xlsx', data_only=True)
ws = wb['Sheet1']

# 璇诲彇鍗曞厓鏍硷紙涓枃鑷姩姝ｇ‘澶勭悊锛?cell_value = ws['A1'].value
print(cell_value)

# 閬嶅巻璇诲彇
for row in ws.iter_rows(values_only=True):
    print(row)

wb.close()
```

---

### 鏂规浜旓細绯荤粺绾т慨澶嶏紙娌绘湰鏂规硶锛?
**淇敼 Windows 鍖哄煙璁剧疆:**

1. 鎵撳紑 **鎺у埗闈㈡澘** 鈫?**鍖哄煙** 鈫?**绠＄悊** 閫夐」鍗?2. 鐐瑰嚮 **鏇存敼绯荤粺鍖哄煙璁剧疆**
3. 鍕鹃€?**Beta 鐗堬細浣跨敤 Unicode UTF-8 鎻愪緵鍏ㄧ悆璇█鏀寔**
4. 閲嶅惎璁＄畻鏈?
**鈿狅笍 娉ㄦ剰:** 姝よ缃彲鑳藉奖鍝嶅叾浠栨棫搴旂敤绋嬪簭锛岃璋ㄦ厧浣跨敤銆?
**PowerShell 閰嶇疆鏂囦欢姘镐箙璁剧疆:**
```powershell
# 娣诲姞鍒?$PROFILE
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['Out-File:Encoding'] = 'UTF8'
$PSDefaultParameterValues['Set-Content:Encoding'] = 'UTF8'
```

---

## 馃搳 鏂规瀵规瘮

| 鏂规 | 缂栫爜澶勭悊 | 瀹夎闇€姹?| 缁存姢鎴愭湰 | 鎺ㄨ崘搴?|
|------|---------|---------|---------|--------|
| **xlwings** | 猸愨瓙猸愨瓙猸?鑷姩 | Python + 搴?| 浣?| 猸愨瓙猸愨瓙猸?|
| **PowerShell+Marshal** | 猸愨瓙猸愨瓙 鎵嬪姩 | 鏃?| 涓?| 猸愨瓙猸愨瓙 |
| **VBScript+ADODB** | 猸愨瓙猸?澶嶆潅 | 鏃?| 楂?| 猸愨瓙 |
| **openpyxl** | 猸愨瓙猸愨瓙猸?鑷姩 | Python + 搴?| 浣?| 猸愨瓙猸愨瓙 |
| **绯荤粺 UTF-8 璁剧疆** | 猸愨瓙猸愨瓙猸?鑷姩 | 鏃?| 浣?| 猸愨瓙猸?|

---

## 馃洜锔?鏁呴殰鎺掓煡鎸囧崡

### 闂 1: COM 瀵硅薄鍒涘缓澶辫触
```powershell
# 娴嬭瘯 COM 绯荤粺
New-Object -ComObject WScript.Shell

# 濡傛灉澶辫触锛屾竻鐞嗚繘绋?taskkill /F /IM excel.exe
taskkill /F /IM dllhost.exe

# 閲嶅惎 COM 鏈嶅姟锛堥渶瑕佺鐞嗗憳锛?Restart-Service DcomLaunch -Force
Restart-Service COMSysApp -Force
```

### 闂 2: 璇诲彇浠嶇劧涔辩爜
```powershell
# 妫€鏌ュ綋鍓嶇紪鐮?[Console]::OutputEncoding
$OutputEncoding

# 寮哄埗璁剧疆涓?UTF-8
chcp 65001  # 璁剧疆鎺у埗鍙颁唬鐮侀〉
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

### 闂 3: 鍐呭瓨娉勬紡锛圕OM 瀵硅薄鏈噴鏀撅級
```powershell
# 濮嬬粓浣跨敤 ReleaseComObject
[System.Runtime.InteropServices.Marshal]::ReleaseComObject($excel) | Out-Null
[System.GC]::Collect()
[System.GC]::WaitForPendingFinalizers()
```

---

## 馃摝 渚濊禆瀹夎

### Python 鐜
```bash
# 瀹夎 Python (濡傛灉鏈畨瑁?
# 浠?https://python.org 涓嬭浇

# 瀹夎 xlwings
pip install xlwings

# 瀹夎 openpyxl
pip install openpyxl

# 瀹夎 pandas (鍙€夛紝鐢ㄤ簬鏁版嵁澶勭悊)
pip install pandas
```

### PowerShell 妯″潡
```powershell
# ImportExcel 妯″潡锛堟浛浠?COM 鐨勫彟涓€绉嶉€夋嫨锛?Install-Module -Name ImportExcel -Scope CurrentUser
```

---

## 馃敆 鍙傝€冭祫婧?
### 瀹樻柟鏂囨。
- [xlwings 瀹樻柟鏂囨。](https://docs.xlwings.org/)
- [openpyxl 鏂囨。](https://openpyxl.readthedocs.io/)
- [Microsoft Excel COM 鍙傝€僝(https://docs.microsoft.com/en-us/office/vba/api/overview/excel)

### GitHub 椤圭洰
- [xlwings/xlwings](https://github.com/xlwings/xlwings)
- [openpyxl/openpyxl](https://foss.heptapod.net/openpyxl/openpyxl)
- [ImportExcel](https://github.com/dfinke/ImportExcel)

### 绀惧尯璧勬簮
- Stack Overflow: [excel-com](https://stackoverflow.com/questions/tagged/excel-com) + [encoding](https://stackoverflow.com/questions/tagged/encoding)
- ExcelHome 鎶€鏈鍧?(涓枃)

---

## 馃挕 鏈€浣冲疄璺靛缓璁?
1. **棣栭€?xlwings**: 瀵逛簬鏂伴」鐩紝寮虹儓鎺ㄨ崘浣跨敤 xlwings锛岀紪鐮侀棶棰樺畬鍏ㄨ嚜鍔ㄥ寲澶勭悊

2. **閬垮厤鐩存帴 COM**: 闄ら潪蹇呴』锛屽惁鍒欓伩鍏嶇洿鎺ヤ娇鐢?PowerShell COM 鎺ュ彛澶勭悊涓枃

3. **鏂囦欢缂栫爜缁熶竴**: 纭繚鎵€鏈夎剼鏈枃浠朵繚瀛樹负 UTF-8 with BOM

4. **娴嬭瘯鐜涓€鑷?*: 寮€鍙戝拰鐢熶骇鐜鐨勭郴缁熷尯鍩熻缃簲淇濇寔涓€鑷?
5. **閿欒澶勭悊**: 濮嬬粓娣诲姞 try-catch 鍜?COM 瀵硅薄娓呯悊浠ｇ爜

---

## 馃摑 閽堝褰撳墠鐜鐨勫缓璁?
鏍规嵁 TOOLS.md 涓殑閰嶇疆锛?- 鏂囦欢浣嶇疆锛歚D:\ExcelData\姣忔棩璺熻繘.xlsm`
- 瀵嗙爜锛歚000`

**鎺ㄨ崘瀹炵幇:**

```python
# workspace/tools/excel_reader.py
import xlwings as xw

def read_excel_chinese(file_path, sheet_name, password="000"):
    """瀹夊叏璇诲彇 Excel 涓枃鍐呭"""
    app = xw.App(visible=False)
    try:
        wb = app.books.open(file_path, password=password)
        sheet = wb.sheets[sheet_name]
        data = sheet.used_range.value
        return data
    finally:
        wb.close()
        app.quit()
```

---

**鎶ュ憡缁撴潫**  
*濡傛湁闂锛岃鍙傝€冩晠闅滄帓鏌ユ寚鍗楁垨鑱旂郴鎶€鏈敮鎸?

