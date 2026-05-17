param(
    [switch]$Foreground,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ScriptArgs
)

$workspace = "C:\Users\Huawei\.openclaw\workspace-tuantuan"
$scriptPath = Join-Path $workspace "tools\daily_follow_plan_v2_jihua.py"
$runtimeDir = Join-Path $workspace "runtime\daily_follow_plan"
$pidFile = Join-Path $runtimeDir "runner.pid"
$statusFile = Join-Path $runtimeDir "status.json"
$progressFile = Join-Path $runtimeDir "progress.json"

New-Item -ItemType Directory -Path $runtimeDir -Force | Out-Null

if ($Foreground) {
    $env:PYTHONIOENCODING = "utf-8"
    Push-Location $workspace
    try {
        & python $scriptPath @ScriptArgs
        exit $LASTEXITCODE
    } finally {
        Pop-Location
    }
}

$runningPid = $null
if (Test-Path $pidFile) {
    $pidText = (Get-Content -Path $pidFile -Encoding UTF8 -ErrorAction SilentlyContinue | Select-Object -First 1).Trim()
    if ($pidText -match '^\d+$') {
        try {
            $existing = Get-Process -Id ([int]$pidText) -ErrorAction Stop
            $runningPid = $existing.Id
        } catch {
        }
    }
}

if ($runningPid) {
    $summary = "ALREADY_RUNNING PID={0}" -f $runningPid
    if (Test-Path $statusFile) {
        try {
            $status = Get-Content -Path $statusFile -Raw -Encoding UTF8 | ConvertFrom-Json
            $summary = "{0} STATUS={1} STAGE={2}" -f $summary, $status.status, $status.stage
            if ($status.updated_at) {
                $summary = "{0} UPDATED_AT={1}" -f $summary, $status.updated_at
            }
            if ($status.current_client -and $status.current_client.name) {
                $summary = "{0} CURRENT={1}" -f $summary, $status.current_client.name
            }
        } catch {
        }
    }
    if (Test-Path $progressFile) {
        try {
            $progress = Get-Content -Path $progressFile -Raw -Encoding UTF8 | ConvertFrom-Json
            if ($progress.total_clients) {
                $summary = "{0} PROGRESS={1}/{2}" -f $summary, $progress.completed_clients, $progress.total_clients
            }
        } catch {
        }
    }
    Write-Output $summary
    exit 0
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logPath = Join-Path $runtimeDir ("run_" + $timestamp + ".log")
$scriptArgString = (($ScriptArgs | ForEach-Object { '"' + $_.Replace('"', '\"') + '"' }) -join ' ').Trim()
$command = 'set PYTHONIOENCODING=utf-8 && cd /d "{0}" && python "{1}" {2} >> "{3}" 2>&1' -f $workspace, $scriptPath, $scriptArgString, $logPath
$process = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", $command -WorkingDirectory $workspace -WindowStyle Hidden -PassThru

Write-Output ("STARTED PID={0} LOG={1} STATUS={2}" -f $process.Id, $logPath, $statusFile)
