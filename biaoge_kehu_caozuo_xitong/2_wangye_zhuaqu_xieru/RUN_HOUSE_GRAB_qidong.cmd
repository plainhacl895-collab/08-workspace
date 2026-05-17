@echo off
setlocal
cd /d C:\Users\Huawei\.openclaw\workspace-tuantuan\biaoge_kehu_caozuo_xitong\2_wangye_zhuaqu_xieru
echo Start house grab, do not close this window or browser...
set HOUSE_GRAB_CMD_ENTRY=1
python C:\Users\Huawei\.openclaw\workspace-tuantuan\biaoge_kehu_caozuo_xitong\2_wangye_zhuaqu_xieru\house_grab_pipeline_zhuapai.py
echo.
echo Grab completed!
pause
