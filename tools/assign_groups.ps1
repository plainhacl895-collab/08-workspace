# assign_groups.ps1 - Wrapper for assign_groups.vbs
# Usage: powershell -File assign_groups.ps1
# Actual work is done by assign_groups.vbs (more stable with Excel COM)

cscript //nologo "D:\ExcelData\assign_groups.vbs"
