[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$files = Get-ChildItem "D:\ExcelData\*.xlsm" | Where-Object { $_.Name -ne "test.xlsm" }
$filePath = $files[0].FullName

$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false

try {
    $wb = $excel.Workbooks.Open($filePath)
    
    for ($i = 1; $i -le $wb.Worksheets.Count; $i++) {
        $null = $wb.Worksheets.Item($i).Name
    }
    $ws = $wb.Worksheets.Item(2)
    
    Write-Host "=== Searching for 张逸林 ==="
    $foundRow = 0
    for ($row = 12; $row -le 300; $row++) {
        $name = $ws.Cells.Item($row, 9).Value2
        if ($name -ne $null -and $name -ne "" -and $name.ToString().Contains("张逸林")) {
            $foundRow = $row
            Write-Host "Found: Row $row - $name"
            break
        }
    }
    
    if ($foundRow -eq 0) {
        Write-Host "Customer 张逸林 not found"
        $wb.Close($false)
        $excel.Quit()
        exit 0
    }
    
    $name = $ws.Cells.Item($foundRow, 9).Value2
    $level = $ws.Cells.Item($foundRow, 6).Value2
    $houseType = $ws.Cells.Item($foundRow, 7).Value2
    $budget = $ws.Cells.Item($foundRow, 8).Value2
    $area = $ws.Cells.Item($foundRow, 10).Value2
    $phone = $ws.Cells.Item($foundRow, 11).Value2
    
    Write-Host "`n=== Customer Info ==="
    Write-Host "Name: $name"
    Write-Host "Level: $level"
    Write-Host "Type: $houseType"
    Write-Host "Budget: $budget wan"
    Write-Host "Area: $area"
    Write-Host "Phone: $phone"
    
    Write-Host "`n=== All Followup Records ==="
    $baseDate = [DateTime]::Parse("1899-12-30")
    $followups = @()
    
    for ($col = 20; $col -le 500; $col++) {
        $header = $ws.Cells.Item(11, $col).Value2
        $value = $ws.Cells.Item($foundRow, $col).Value2
        
        if ($header -ne $null -and $header -ne "" -and $value -ne $null -and $value -ne "") {
            try {
                if ($header -is [Double]) {
                    $date = $baseDate.AddDays($header).ToString("yyyy-MM-dd")
                } else {
                    $date = $header.ToString()
                }
                $followups += "$date : $value"
            } catch {}
        }
    }
    
    if ($followups.Count -eq 0) {
        Write-Host "No followup records found"
    } else {
        Write-Host "Total: $($followups.Count) records"
        Write-Host "`n=== Last 3 Followups ==="
        $last3 = $followups | Select-Object -Last 3
        foreach ($f in $last3) {
            Write-Host $f
        }
    }
    
    $wb.Close($false)
    $excel.Quit()
    Write-Host "`n=== Done ==="
}
catch {
    Write-Host "Error: $_"
    if ($excel) { $excel.Quit() }
}
