[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Find the file
$files = Get-ChildItem "D:\ExcelData\*.xlsm" | Where-Object { $_.Name -ne "test.xlsm" }
if (-not $files) {
    Write-Host "No Excel file found"
    exit 1
}
$filePath = $files[0].FullName
Write-Host "File: $filePath"

# Open Excel
$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$wb = $excel.Workbooks.Open($filePath)

# Pre-load worksheets
for ($i = 1; $i -le $wb.Worksheets.Count; $i++) {
    $null = $wb.Worksheets.Item($i).Name
}
$ws = $wb.Worksheets.Item(2)
Write-Host "Worksheet: $($ws.Name)"

# Read header row 11
Write-Host "`n=== HEADERS (Row 11) ==="
$headers = @{}
for ($col = 1; $col -le 20; $col++) {
    $val = $ws.Cells.Item(11, $col).Value2
    if ($val -ne $null -and $val -ne "") {
        $headers[$col] = $val
        Write-Host "Col $col : $val"
    }
}

# Read customers rows 12-20
Write-Host "`n=== CUSTOMERS (Rows 12-20) ==="
for ($row = 12; $row -le 20; $row++) {
    $name = $ws.Cells.Item($row, 9).Value2
    if ($name -ne $null -and $name -ne "") {
        $level = $ws.Cells.Item($row, 6).Value2
        $houseType = $ws.Cells.Item($row, 7).Value2
        $budget = $ws.Cells.Item($row, 8).Value2
        $area = $ws.Cells.Item($row, 10).Value2
        $phone = $ws.Cells.Item($row, 11).Value2
        Write-Host "Row $row | Name: $name | Level: $level | Type: $houseType | Budget: $budget | Area: $area | Phone: $phone"
    }
}

# Close
$wb.Close($false)
$excel.Quit()
Write-Host "`n=== Done ==="
