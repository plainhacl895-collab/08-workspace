@echo off
cd /d C:\Users\Huawei\.openclaw\workspace-tuantuan\tools
taskkill /F /IM EXCEL.EXE >nul 2>&1
timeout /t 4 /nobreak >nul
set PYTHONIOENCODING=utf-8
set PYTHONUNBUFFERED=1
echo [START] 复盘脚本启动...
python -u daily_follow_check_v2_jiancha.py > C:\Users\Huawei\Desktop\check_run.log 2>&1
echo [END] 退出码: %ERRORLEVEL%
