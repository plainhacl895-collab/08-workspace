@echo off
chcp 65001 >nul 2>&1
REM YouTube字幕抓取工具 - 启动器
REM 用法: RUN_YOUTUBE_TRANSCRIPT.cmd ^<URL^> [--language zh,en] [--text-only] [--timestamps]

set "SCRIPT_DIR=%~dp0"
set "PYTHON=C:\Users\Huawei\AppData\Local\Programs\Python\Python311\python.exe"

if "%~1"=="" (
    echo ============================================
    echo YouTube字幕抓取工具 (yt-dlp版)
    echo ============================================
    echo.
    echo 用法:
    echo   RUN_YOUTUBE_TRANSCRIPT.cmd ^<URL或视频ID^>
    echo   RUN_YOUTUBE_TRANSCRIPT.cmd ^<URL^> --language zh,en
    echo   RUN_YOUTUBE_TRANSCRIPT.cmd ^<URL^> --text-only --timestamps
    echo   RUN_YOUTUBE_TRANSCRIPT.cmd ^<URL^> --browser-cookie
    echo.
    echo 选项:
    echo   --browser-cookie   使用Chrome登录状态，防YouTube封锁（推荐）
    echo.
    echo 示例:
    echo   RUN_YOUTUBE_TRANSCRIPT.cmd https://youtube.com/watch?v=dQw4w9WgXcQ
    echo.
    pause
    exit /b 1
)

echo [启动] 正在获取YouTube字幕...
echo.

set PYTHONIOENCODING=utf-8
"%PYTHON%" "%SCRIPT_DIR%youtube_transcript.py" %*

if errorlevel 1 (
    echo.
    echo [错误] 字幕获取失败，请检查上方错误信息
    pause
)
