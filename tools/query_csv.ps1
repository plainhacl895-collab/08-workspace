param(
    [string]$type = "clients",
    [string]$filter = "",
    [int]$top = 50,
    [string]$sort = "",
    [switch]$desc
)

$files = @{
    "clients"    = "D:\ExcelData\clients.csv"
    "properties" = "D:\ExcelData\properties.csv"
    "followup"   = "D:\ExcelData\followup.csv"
    "experience" = "D:\ExcelData\experience.csv"
}

$path = $files[$type]
if (-not $path -or -not (Test-Path $path)) {
    "ERROR: file not found for type=$type" | Out-File "$env:TEMP\query_result.txt" -Encoding UTF8
    exit 1
}

$data = Import-Csv $path -Encoding UTF8

if ($filter -ne "") {
    $conditions = $filter -split ";"
    foreach ($cond in $conditions) {
        $cond = $cond.Trim()
        if ($cond -eq "") { continue }
        
        if ($cond -match "^(\w+)>(.+)$") {
            $f = $Matches[1]; $v = [double]$Matches[2]
            $data = $data | Where-Object {
                $x = $_.$f
                if ($x -match "^\d+\.?\d*$") { [double]$x -gt $v } else { $false }
            }
        }
        elseif ($cond -match "^(\w+)<(.+)$") {
            $f = $Matches[1]; $v = [double]$Matches[2]
            $data = $data | Where-Object {
                $x = $_.$f
                if ($x -match "^\d+\.?\d*$") { [double]$x -lt $v } else { $false }
            }
        }
        elseif ($cond -match "^(\w+)=(.+)$") {
            $f = $Matches[1]; $v = $Matches[2]
            $data = $data | Where-Object { $_.$f -like $v }
        }
    }
}

if ($sort -ne "") {
    if ($desc) {
        $data = $data | Sort-Object -Property $sort -Descending
    } else {
        $data = $data | Sort-Object -Property $sort
    }
}

$total = @($data).Count
$data = $data | Select-Object -First $top

$output = @()
$output += "TOTAL: $total"
$output += "---"

if ($total -gt 0) {
    $first = $data | Select-Object -First 1
    $headers = ($first | Get-Member -MemberType NoteProperty).Name
    $output += ($headers -join "|")
    foreach ($row in $data) {
        $vals = foreach ($h in $headers) { $row.$h }
        $output += ($vals -join "|")
    }
}

$output | Out-File "$env:TEMP\query_result.txt" -Encoding UTF8
"OK: $total results -> query_result.txt"