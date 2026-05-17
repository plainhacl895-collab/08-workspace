@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ======================================
echo 客户完整跟进记录读取工具
echo ======================================
echo.

REM 检查参数
if "%~1"=="" (
    echo 用法：%~nx0 ^<客户行号^> [选项]
    echo.
    echo 选项:
    echo   --all      显示所有跟进记录（默认显示最近 20 条）
    echo   --limit N  显示最近 N 条记录
    echo   --export   导出到文件
    echo   --json     JSON 格式输出
    echo   --quiet    安静模式
    echo.
    echo 示例:
    echo   %~nx0 12                    读取行号 12 的客户，显示最近 20 条
    echo   %~nx0 12 --all              读取行号 12 的客户，显示所有记录
    echo   %~nx0 12 --limit 50         读取行号 12 的客户，显示最近 50 条
    echo   %~nx0 12 --export           读取并导出到桌面
    echo.
    exit /b 1
)

REM 获取脚本目录
set SCRIPT_DIR=%~dp0
set PYTHON_SCRIPT=%SCRIPT_DIR%read-client-all-followups.py

REM 运行 Python 脚本
python "%PYTHON_SCRIPT%" %*

echo.
echo ======================================
echo 完成
echo ======================================
