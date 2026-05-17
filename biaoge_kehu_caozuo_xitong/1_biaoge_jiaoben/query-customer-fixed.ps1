param(
    [string]$CustomerName
)

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$files = Get-ChildItem "D:\ExcelData\*.xlsm" | Where-Object { $_.Name -ne "test.xlsm" }
if (-not $files) {
    Write-Host "ERROR: No Excel file found"
    exit 1
}
$filePath = $files[0].FullName

$excel = $null
$wb = $null
$ws = $null

try {
    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = $false
    $excel.DisplayAlerts = $false
    
    $wb = $excel.Workbooks.Open($filePath)
    
    # Pre-load worksheets
    for ($i = 1; $i -le $wb.Worksheets.Count; $i++) {
        $null = $wb.Worksheets.Item($i).Name
    }
    $ws = $wb.Worksheets.Item(2)
    
    # Find customer
    $foundRow = 0
    for ($row = 12; $row -le 300; $row++) {
        $name = $ws.Cells.Item($row, 9).Value2
        if ($name -ne $null -and $name -ne "" -and $name.ToString().Contains($CustomerName)) {
            $foundRow = $row
            break
        }
    }
    
    if ($foundRow -eq 0) {
        Write-Host "NOT_FOUND: $CustomerName"
        exit 0
    }
    
    # Read customer info
    $name = $ws.Cells.Item($foundRow, 9).Value2
    $level = $ws.Cells.Item($foundRow, 6).Value2
    $houseType = $ws.Cells.Item($foundRow, 7).Value2
    $budget = $ws.Cells.Item($foundRow, 8).Value2
    $area = $ws.Cells.Item($foundRow, 10).Value2
    $phone = $ws.Cells.Item($foundRow, 11).Value2
    $demand = $ws.Cells.Item($foundRow, 16).Value2
    $pain = $ws.Cells.Item($foundRow, 18).Value2
    
    Write-Host "=== CUSTOMER_INFO ==="
    Write-Host "Name: $name"
    Write-Host "Level: $level"
    Write-Host "Type: $houseType"
    Write-Host "Budget: $budget"
    Write-Host "Area: $area"
    Write-Host "Phone: $phone"
    Write-Host "Demand: $demand"
    Write-Host "Pain: $pain"
    
    # Read followup records
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
                $followups += "$date|$value"
            } catch {}
        }
    }
    
    Write-Host "`n=== FOLLOWUP_COUNT: $($followups.Count) ==="
    
    if ($followups.Count -eq 0) {
        Write-Host "NO_FOLLOWUP_RECORDS"
    } else {
        Write-Host "`n=== LAST_3_FOLLOWUPS ==="
        $last3 = $followups | Select-Object -Last 3
        foreach ($f in $last3) {
            $parts = $f.Split("|")
            Write-Host "$($parts[0]) : $($parts[1])"
        }
    }
    
    Write-Host "`n=== DONE ==="
}
catch {
    Write-Host "ERROR: $_"
    exit 1
}
finally {
    if ($wb) { $wb.Close($false) | Out-Null }
    if ($excel) { $excel.Quit() | Out-Null }
}
