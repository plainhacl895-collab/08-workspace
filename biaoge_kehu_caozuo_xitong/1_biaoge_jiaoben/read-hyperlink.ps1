$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$wb = $excel.Workbooks.Open("D:\ExcelData\每日跟进.xlsm", $false, $true, $null, "000")
$ws = $wb.Worksheets.Item(4)

Write-Host "=== Reading Hyperlinks ==="
Write-Host "Total Hyperlinks: $($ws.Hyperlinks.Count)"
Write-Host ""

# Try to read hyperlink from specific cell
for ($row = 5; $row -le 10; $row++) {
    $cell = $ws.Cells.Item($row, 3)
    $value = $cell.Value2
    $hasHL = $cell.Hyperlinks.Count -gt 0
    
    Write-Host "Row $row Col 3: $value"
    Write-Host "  Hyperlink Count: $($cell.Hyperlinks.Count)"
    
    if ($cell.Hyperlinks.Count -gt 0) {
        $hl = $cell.Hyperlinks.Item(1)
        Write-Host "  Address: $($hl.Address)"
        Write-Host "  SubAddress: $($hl.SubAddress)"
    }
    Write-Host ""
}

$wb.Close($false)
$excel.Quit()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($ws) | Out-Null
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($wb) | Out-Null
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null

Write-Host "DONE"
