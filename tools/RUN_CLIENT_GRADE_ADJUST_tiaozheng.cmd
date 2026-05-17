@echo off
chcp 65001 >nul
setlocal

echo ============================================
echo Client Grade Adjust
echo ============================================
echo.
echo Usage 1: run this script directly
echo Usage 2: use the current main entrypoint
echo        cmd /c C:\Users\Huawei\.openclaw\workspace-tuantuan\tools\RUN_TUANTUAN_qidong.cmd client-grade-adjust --query "client" --new-grade "A"
echo.
echo This wrapper runs:
echo        client_grade_adjust.py
echo.

set "SCRIPT_DIR=%~dp0"
python "%SCRIPT_DIR%client_grade_adjust.py"

echo.
pause
