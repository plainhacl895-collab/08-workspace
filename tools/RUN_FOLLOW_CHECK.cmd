@echo off
setlocal
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
python daily_follow_check_v2_jiancha.py %*
