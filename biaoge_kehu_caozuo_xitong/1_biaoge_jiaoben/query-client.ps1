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
    
    Write-Host "=== Searching for customer Li ==="
    $foundRow = 0
    for ($row = 12; $row -le 200; $row++) {
        $name = $ws.Cells.Item($row, 9).Value2
        if ($name -ne $null -and $name -ne "" -and $name.ToString().Contains("Li")) {
            $foundRow = $row
            Write-Host "Found: Row $row - $name"
            break
        }
    }
    
    if ($foundRow -eq 0) {
        Write-Host "Customer Li not found"
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
    $demand = $ws.Cells.Item($foundRow, 16).Value2
    $thought = $ws.Cells.Item($foundRow, 17).Value2
    $pain = $ws.Cells.Item($foundRow, 18).Value2
    $community = $ws.Cells.Item($foundRow, 19).Value2
    
    Write-Host "`n=== Customer Info ==="
    Write-Host "Name: $name"
    Write-Host "Level: $level"
    Write-Host "Type: $houseType"
    Write-Host "Budget: $budget wan"
    Write-Host "Area: $area"
    Write-Host "Phone: $phone"
    Write-Host "Demand: $demand"
    Write-Host "Thought: $thought"
    Write-Host "Pain: $pain"
    Write-Host "Community: $community"
    
    Write-Host "`n=== Followup Records (After 2026-02-01) ==="
    $baseDate = [DateTime]::Parse("1899-12-30")
    $hasFollowup = $false
    
    for ($col = 20; $col -le 500; $col++) {
        $header = $ws.Cells.Item(11, $col).Value2
        $value = $ws.Cells.Item($foundRow, $col).Value2
        
        if ($header -ne $null -and $header -ne "") {
            try {
                if ($header -is [Double]) {
                    $date = $baseDate.AddDays($header).ToString("yyyy-MM-dd")
                } else {
                    $date = $header.ToString()
                }
                
                if ($value -ne $null -and $value -ne "") {
                    if ($date -ge "2026-02-01") {
                        Write-Host "$date : $value"
                        $hasFollowup = $true
                    }
                }
            } catch {}
        }
    }
    
    if (-not $hasFollowup) {
        Write-Host "No followup records after Feb 2026"
    }
    
    $wb.Close($false)
    $excel.Quit()
    Write-Host "`n=== Done ==="
}
catch {
    Write-Host "Error: $_"
    if ($excel) { $excel.Quit() }
}
