@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM export_csv_run.cmd - 直接执行 CSV 导出（杀进程 + 导出）
REM 用于手动触发或确认后执行

set LOG_FILE=D:\ExcelData\export_csv.log

echo ========================================
echo CSV 导出执行中...
echo ========================================
echo.

echo [%date% %time%] 开始执行 CSV 导出 >> "%LOG_FILE%"

REM ===== 1. 执行 VBS 脚本（已包含杀进程逻辑） =====
echo [1/2] 正在杀掉 Excel 进程并导出 CSV...
cscript //nologo "D:\ExcelData\export_csv.vbs" >> "%LOG_FILE%" 2>&1

if !errorlevel! equ 0 (
    echo [2/2] CSV 导出成功！
    echo [%date% %time%] CSV 导出成功 >> "%LOG_FILE%"
    
    REM 显示生成的文件
    echo.
    echo 生成的文件：
    dir "D:\ExcelData\*.csv" /b /o-d 2>nul | findstr /i "clients followup properties"
    
    exit /b 0
) else (
    echo [2/2] CSV 导出失败，返回码：!errorlevel!
    echo [%date% %time%] CSV 导出失败，返回码：!errorlevel! >> "%LOG_FILE%"
    exit /b !errorlevel!
)
