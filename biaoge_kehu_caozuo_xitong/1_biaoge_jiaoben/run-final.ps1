param([string]$CustomerName = "Zhang")
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$files = Get-ChildItem "D:\ExcelData\*.xlsm" | Where-Object { $_.Name -ne "test.xlsm" }
if (-not $files) { Write-Host "ERROR: No Excel file found"; exit 1 }
$filePath = $files[0].FullName

$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false
$wb = $excel.Workbooks.Open($filePath)

Write-Host "Worksheets:"
for ($i = 1; $i -le $wb.Worksheets.Count; $i++) {
    Write-Host "  $i : $($wb.Worksheets.Item($i).Name)"
}

$ws = $wb.Worksheets.Item(2)
Write-Host "Searching in worksheet 2: $($ws.Name)"

$foundRow = 0
for ($row = 12; $row -le 100; $row++) {
    $cell = $ws.Cells.Item($row, 9)
    if ($cell -ne $null) {
        $name = $cell.Value2
        if ($name -ne $null -and $name -ne "") {
            Write-Host "Row $row : $name"
            if ($name.ToString().Contains($CustomerName)) {
                $foundRow = $row
                Write-Host ">>> FOUND at row $foundRow"
                break
            }
        }
    }
}

if ($foundRow -eq 0) { Write-Host "NOT_FOUND: $CustomerName" }

$wb.Close($false)
$excel.Quit()
