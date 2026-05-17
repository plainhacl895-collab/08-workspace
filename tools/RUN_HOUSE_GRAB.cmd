@echo off
setlocal
cd /d "%~dp0"
set HOUSE_GRAB_PIPELINE_RUN=1
set PYTHONIOENCODING=utf-8
python house_grab_pipeline.py --direct
