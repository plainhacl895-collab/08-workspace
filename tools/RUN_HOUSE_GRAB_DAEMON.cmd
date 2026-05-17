@echo off
setlocal
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
python house_grab_daemon.py
