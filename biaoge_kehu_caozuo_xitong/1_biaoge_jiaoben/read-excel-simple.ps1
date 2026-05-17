[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "Start reading Excel..." -ForegroundColor Green

$excel = $null
$wb = $null
$ws = $null

try {
    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = $false
    $excel.DisplayAlerts = $false
    
    Write-Host "Opening file..."
    $wb = $excel.Workbooks.Open("D:\ExcelData\每日跟进.xlsm")
    
    Write-Host "Pre-loading worksheets..."
    for ($i = 1; $i -le $wb.Worksheets.Count; $i++) {
        $null = $wb.Worksheets.Item($i).Name
    }
    
    $ws = $wb.Worksheets.Item(2)
    
    Write-Host "=== Basic Info ===" -ForegroundColor Cyan
    $wsName = $ws.Name
    $rows = $ws.UsedRange.Rows.Count
    $cols = $ws.UsedRange.Columns.Count
    Write-Host "Worksheet: $wsName"
    Write-Host "Rows: $rows"
    Write-Host "Cols: $cols"
    
    Write-Host "`n=== Header Row 11 (First 15 Cols)===" -ForegroundColor Cyan
    for ($col = 1; $col -le 15; $col++) {
        $value = $ws.Cells.Item(11, $col).Value2
        if ($value -ne $null) {
            $colLetter = [char]([int][char]64 + $col)
            Write-Host "Col $col ($colLetter): $value"
        }
    }
    
    Write-Host "`n=== Customers (Rows 12-16)===" -ForegroundColor Cyan
    for ($row = 12; $row -le 16; $row++) {
        $name = $ws.Cells.Item($row, 9).Value2
        if ($name -ne $null -and $name -ne "") {
            $level = $ws.Cells.Item($row, 6).Value2
            $houseType = $ws.Cells.Item($row, 7).Value2
            $budget = $ws.Cells.Item($row, 8).Value2
            $area = $ws.Cells.Item($row, 10).Value2
            $phone = $ws.Cells.Item($row, 11).Value2
            Write-Host "Row $row - Name: $name, Level: $level, Type: $houseType, Budget: $budget, Area: $area, Phone: $phone"
        }
    }
    
    Write-Host "`n=== Complete ===" -ForegroundColor Green
}
catch {
    Write-Host "Error: $_" -ForegroundColor Red
}
finally {
    if ($wb) { $wb.Close($false) | Out-Null }
    if ($excel) { $excel.Quit() | Out-Null }
    Write-Host "Done"
}
