import json, pythoncom, win32com.client

cache = json.load(open(r'C:\Users\Huawei\.openclaw\workspace-tuantuan\runtime\tuantuan_cache.json', encoding='utf-8'))
original_grades = {c['row']: c['grade'] for c in cache['clients'] if c.get('grade')}
print(f'缓存中有 {len(original_grades)} 个原始等级')

pythoncom.CoInitialize()
excel = win32com.client.DispatchEx('Excel.Application')
excel.Visible = False
excel.DisplayAlerts = False
wb = excel.Workbooks.Open(r'D:\Unique work form\daily_followup.xlsm', UpdateLinks=0, ReadOnly=False, Password='***')
ws = wb.Worksheets(2)

restored = 0
for row, grade in original_grades.items():
    ws.Cells(row, 6).Value = grade
    restored += 1

wb.Save()
wb.Close(SaveChanges=False)
excel.Quit()
pythoncom.CoUninitialize()
print(f'已恢复 {restored} 个客户等级到原始值')
