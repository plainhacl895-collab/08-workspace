@echo off
chcp 65001 >nul
echo ========================================
echo 团团助手 - Chrome调试端口启动器
echo ========================================
echo.
echo 正在检查调试端口状态...

:: 检查调试端口是否已被占用
netstat -ano | findstr ":9222" >nul
if %errorlevel%==0 (
    echo [OK] 调试端口9222已被占用，可能是之前的Chrome调试实例仍在运行
    echo.
    echo 正在验证...
    :: 尝试连接
    powershell -Command "try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1:9222/json' -TimeoutSec 3 -ErrorAction Stop; Write-Host '[OK] 调试端口正常' } catch { Write-Host '[FAIL] 端口被占用但无法连接，将尝试重启'; exit 1 }"
    if %errorlevel%==0 (
        echo.
        echo 可以直接使用！
        echo 1. 点击Excel中的HYPERLINK链接
        echo 2. 也可以直接运行自动化脚本
        pause
        exit /b 0
    )
)

echo.
echo 正在关闭现有的Chrome窗口（为启动调试版本释放资源）...
:: 关闭所有Chrome窗口
taskkill /F /IM chrome.exe >nul 2>&1
timeout /t 2 /nobreak >nul

echo.
echo 正在启动Chrome调试版本（使用你的日常Profile）...
echo.

:: 获取Chrome路径
where chrome >nul 2>&1
if %errorlevel%==0 (
    set "CHROME_PATH=chrome"
) else (
    set "CHROME_PATH=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
    if not exist "%CHROME_PATH%" (
        set "CHROME_PATH=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
    )
)

echo Chrome路径: %CHROME_PATH%
echo.

:: 启动Chrome调试版本，使用用户日常Profile
start "" "%CHROME_PATH%" --remote-debugging-port=9222 --user-data-dir="%LOCALAPPDATA%\Google\Chrome\User Data"

echo Chrome调试版本已启动！
echo.
echo 请等待3秒让Chrome完全加载...
timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo 验证连接...
powershell -Command "try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1:9222/json' -TimeoutSec 5 -ErrorAction Stop; Write-Host '[OK] 连接成功！' } catch { Write-Host '[FAIL] 连接失败，请手动检查Chrome是否正常启动'; exit 1 }"

echo.
echo 完成！
echo.
echo 使用说明：
echo 1. Chrome已用你的日常账号登录（扫码后会自动保持）
echo 2. 以后点击Excel中的HYPERLINK链接，会在这个窗口打开
echo 3. 运行自动化脚本时，也会复用这个窗口
echo 4. 关闭此窗口后，Chrome调试版本会一起关闭
echo.
pause
