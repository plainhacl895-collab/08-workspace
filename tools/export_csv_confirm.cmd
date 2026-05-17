@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM export_csv_confirm.cmd - CSV 导出确认脚本
REM 先发 Telegram 确认消息，用户确认后再执行导出

set CONFIRM_FILE=D:\ExcelData\export_csv.confirmed
set LOG_FILE=D:\ExcelData\export_csv_confirm.log

echo [%date% %time%] CSV 导出确认脚本启动 >> "%LOG_FILE%"

REM ===== 1. 检查是否有确认标志 =====
if exist "%CONFIRM_FILE%" (
    echo [%date% %time%] 检测到确认标志，执行 CSV 导出 >> "%LOG_FILE%"
    
    REM 删除确认标志
    del "%CONFIRM_FILE%" 2>nul
    
    REM ===== 2. 执行杀进程 + CSV 导出 =====
    echo [%date% %time%] 开始执行 export_csv.vbs >> "%LOG_FILE%"
    cscript //nologo "D:\ExcelData\export_csv.vbs" >> "%LOG_FILE%" 2>&1
    echo [%date% %time%] export_csv.vbs 执行完成，返回码：!errorlevel! >> "%LOG_FILE%"
    
    exit /b !errorlevel!
) else (
    echo [%date% %time%] 未检测到确认标志，发送 Telegram 确认消息 >> "%LOG_FILE%"
    
    REM ===== 3. 发送 Telegram 确认消息 =====
    REM 通过 OpenClaw sessions_send 发送消息到主会话
    REM 注意：这里需要通过团团助手发送消息
    
    echo.
    echo ========================================
    echo CSV 导出需要确认
    echo ========================================
    echo.
    echo 检测到 Excel 进程可能占用文件，需要先杀进程再导出。
    echo.
    echo 请在团团助手中回复"确认导出 CSV"来继续。
    echo 或者手动运行：D:\ExcelData\export_csv_run.cmd
    echo.
    
    REM 创建等待标志
    echo %date% %time% > "D:\ExcelData\export_csv.pending"
    
    echo [%date% %time%] 已创建等待标志，退出 >> "%LOG_FILE%"
    exit /b 0
)
