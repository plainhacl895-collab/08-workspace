@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ======================================
echo 客户完整跟进记录读取工具 v2.0
echo （智能缓存版）
echo ======================================
echo.

REM 检查参数
if "%~1"=="" (
    echo 用法：%~nx0 ^<客户行号^> [选项]
    echo.
    echo 选项:
    echo   --all      显示所有跟进记录
    echo   --limit N  显示最近 N 条（默认 20）
    echo   --export   导出到桌面
    echo   --json     JSON 格式输出
    echo   --quiet    安静模式
    echo   --force    强制从 Excel 读取（忽略缓存）
    echo   --refresh  刷新缓存
    echo.
    echo 示例:
    echo   %~nx0 12                    读取行号 12（优先缓存）
    echo   %~nx0 12 --all              读取所有记录
    echo   %~nx0 12 --force            强制 Excel 读取
    echo   %~nx0 12 --refresh          刷新缓存
    echo.
    exit /b 1
)

REM 获取脚本目录
set SCRIPT_DIR=%~dp0
set PYTHON_SCRIPT=%SCRIPT_DIR%read-client-all-followups-v2.py

REM 运行 Python 脚本
python "%PYTHON_SCRIPT%" --row %*

echo.
echo ======================================
echo 完成
echo ======================================
