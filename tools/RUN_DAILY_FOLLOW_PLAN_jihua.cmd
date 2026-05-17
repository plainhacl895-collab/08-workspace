@echo off
setlocal
set PYTHONIOENCODING=utf-8

cd /d "%~dp0"

echo ============================================================
echo Daily Followup Plan Generator - Starting
echo ============================================================

echo Cleaning environment...
taskkill /F /IM python.exe 2>nul
taskkill /F /IM EXCEL.EXE 2>nul

echo Cleaning PID lock...
if exist "runtime\daily_follow_plan\runner.pid" del /f /q "runtime\daily_follow_plan\runner.pid"

echo Bypassing bad cache...
python -c "import json,time,os; p='runtime/tuantuan_cache.json'; [json.dump({**json.load(open(p,encoding='utf-8')),'source':{'workbook_mtime':str(time.time())}},open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2) or print('Cache marked fresh.')] if os.path.exists(p) else print('Cache not found.')"

echo Launching AI suggestion generator (35-40 mins)...
echo Telegram notification will be sent when done.
echo.

set SCRIPT=%~dp0daily_follow_plan_v2_jihua.py

where python >nul 2>nul && (python "%SCRIPT%" & goto :end)
if exist "C:\Users\Huawei\AppData\Local\Programs\Python\Python311\python.exe" (
    "C:\Users\Huawei\AppData\Local\Programs\Python\Python311\python.exe" "%SCRIPT%" & goto :end
)
echo ERROR: Python not found
goto :end

:end
echo ============================================================
echo Done
echo ============================================================
pause
