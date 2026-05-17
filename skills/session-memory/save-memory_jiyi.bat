@echo off
REM 保存错误教训记忆
REM 用法：save-memory.bat "主题" "内容" [标签...]

setlocal enabledelayedexpansion

set TOPIC=%1
set CONTENT=%2
shift
shift
set TAGS=%*

set MEMORY_DIR=%USERPROFILE%\.agent-memory
set YEAR=%date:~10,4%
set MONTH=%date:~4,2%
set DAY=%date:~7,2%

if not exist "%MEMORY_DIR%" mkdir "%MEMORY_DIR%"
if not exist "%MEMORY_DIR%\%YEAR%" mkdir "%MEMORY_DIR%\%YEAR%"
if not exist "%MEMORY_DIR%\%YEAR%\%MONTH%" mkdir "%MEMORY_DIR%\%YEAR%\%MONTH%"

set TIMESTAMP=%date:~10,4%%date:~4,2%%date:~7,2%%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%

echo {"ts":"%TIMESTAMP%","topic":"%TOPIC%","content":"%CONTENT%","tags":[%TAGS%],"importance":"critical"} >> "%MEMORY_DIR%\%YEAR%\%MONTH%\%DAY%.jsonl"

echo ✅ 记忆已保存：%TOPIC%
echo 📁 文件：%MEMORY_DIR%\%YEAR%\%MONTH%\%DAY%.jsonl
