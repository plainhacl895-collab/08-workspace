@echo off
setlocal
REM 获取脚本所在目录
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"
echo ============================================================
echo 房源抓取任务启动
echo 脚本目录：%SCRIPT_DIR%
echo ============================================================
echo.
set HOUSE_GRAB_CMD_ENTRY=1
set PYTHONIOENCODING=utf-8
python "%SCRIPT_DIR%house_grab_pipeline.py"
echo.
echo ============================================================
echo 抓取完成
echo ============================================================
pause
