[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$filePath = "D:\ExcelData\meiri-genjin - fuben.xlsm"
Write-Host "Looking for Excel file..."

$files = Get-ChildItem "D:\ExcelData\*.xlsm" | Where-Object { $_.Name -notmatch "test" }
if ($files.Count -eq 0) { Write-Host "No Excel file found"; exit 1 }
$filePath = $files[0].FullName
Write-Host "Using: $filePath"

$connStr = "Provider=Microsoft.ACE.OLEDB.12.0;Data Source=$filePath;Extended Properties='Excel 12.0 Xml;HDR=YES;IMEX=1';"

try {
    $conn = New-Object System.Data.OleDb.OleDbConnection($connStr)
    $conn.Open()
    Write-Host "Connected!"
    
    $tables = $conn.GetOleDbSchemaTable([System.Data.OleDb.OleDbSchemaGuid]::Tables, $null)
    Write-Host "Tables:"
    foreach ($t in $tables) { Write-Host "  - $($t.TABLE_NAME)" }
    
    $cmd = $conn.CreateCommand()
    $cmd.CommandText = "SELECT * FROM [Sheet1$]"
    $adapter = New-Object System.Data.OleDb.OleDbDataAdapter($cmd)
    $ds = New-Object System.Data.DataSet
    $adapter.Fill($ds)
    
    Write-Host "Rows: $($ds.Tables[0].Rows.Count)"
    
    foreach ($row in $ds.Tables[0].Rows) {
        $name = $row[8]
        if ($name -ne $null -and $name.ToString().Contains("Zhang")) {
            Write-Host "FOUND: $name"
        }
    }
    
    $conn.Close()
} catch {
    Write-Host "Error: " $_.Exception.Message
}
