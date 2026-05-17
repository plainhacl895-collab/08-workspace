@echo off
chcp 65001 >nul
echo ========================================
echo 团团助手 - 日常Chrome启动器
echo ========================================
echo.
echo 正在关闭任何现有的Chrome进程...
taskkill /F /IM chrome.exe >nul 2>&1
timeout /t 1 /nobreak >nul

echo 启动Chrome（你的日常已登录状态）...
start "" "C:\Users\Huawei\AppData\Local\Google\Chrome\Application\chrome.exe"

echo.
echo 完成！Chrome已以你的日常账号运行。
echo.
echo 使用说明：
echo - 团团助手运行时，会自动关闭Chrome进行自动化
echo - 团团助手结束后，运行此脚本即可恢复你的Chrome登录状态
echo.
pause
