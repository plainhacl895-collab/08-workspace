@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo TuanTuan Automation Chrome Launcher
echo ========================================
echo.
echo This is TuanTuan assistant dedicated Chrome.
echo First time: need to scan QR to login Lianjia (only once^)
echo After that: automatically keeps login state.
echo.
echo Closing all Chrome processes...
taskkill /F /IM chrome.exe >nul 2>&1
timeout /t 2 /nobreak >nul

echo.
echo Creating automation profile directory...
set AUTO_PROFILE=%LOCALAPPDATA%\Google\Chrome\User Data\TuanTuanAuto
if not exist "%AUTO_PROFILE%" (
    mkdir "%AUTO_PROFILE%"
    echo [OK] Created automation profile directory
)

echo.
echo Launching automation Chrome...
start "" "C:\Users\Huawei\AppData\Local\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%AUTO_PROFILE%" --no-first-run --no-default-browser-check

echo.
echo Chrome should be open now^
echo.
echo Please do the following in the Chrome window:
echo   1. Scan QR code with WeChat to login Lianjia
echo   2. Close this Chrome window when done
echo.
echo After first login, TuanTuan will use this Chrome automatically.
echo.
pause
