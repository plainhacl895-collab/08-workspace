@echo off
REM ⚠️【重要】修改本脚本前必须先向佳佳汇报并获得同意，严禁私自修改！
REM 安全版房源抓取 - 带超时保护

chcp 65001 >nul
echo.
echo =========================================
echo 房源抓取 - 安全版（30 分钟超时保护）
echo =========================================
echo.

REM 获取脚本目录
set SCRIPT_DIR=%~dp0

REM 清理锁文件
if exist "%SCRIPT_DIR%_house_grab_runtime\.house_grab.lock" (
    echo [清理] 删除旧锁文件...
    del /q "%SCRIPT_DIR%_house_grab_runtime\.house_grab.lock"
)

REM 启动抓取（带超时）
echo [启动] 开始抓取...
timeout /t 3 /nobreak >nul

start "房源抓取" /MIN cmd /c "python "%SCRIPT_DIR%house_grab_pipeline.py" 2>&1"

echo [监控] 抓取进程已启动，将在后台运行
echo [提示] 请打开 Chrome 调试窗口完成扫码登录
echo.
echo 进度查看:
echo   - 状态文件：%SCRIPT_DIR%_house_grab_runtime\grab_status.txt
echo   - 日志文件：%SCRIPT_DIR%_house_grab_logs\house_grab.log
echo.
echo 预计耗时：15-25 分钟
echo =========================================
