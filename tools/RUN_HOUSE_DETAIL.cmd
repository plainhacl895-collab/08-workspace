@echo off
setlocal
cd /d "%~dp0"
set HOUSE_DETAIL_CMD_ENTRY=1
set PYTHONIOENCODING=utf-8
python "%~dp0house_detail_query.py" %*
set EXIT_CODE=%ERRORLEVEL%
exit /b %EXIT_CODE%
