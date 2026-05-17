$workspace = Split-Path -Parent $PSScriptRoot
$runtimeDir = Join-Path $workspace 'runtime\daily_follow_plan'
$statusFile = Join-Path $runtimeDir 'status.json'
$progressFile = Join-Path $runtimeDir 'progress.json'

if (-not (Test-Path $statusFile)) {
    Write-Output 'STATUS=missing MESSAGE=no_status_file'
    exit 0
}

try {
    $status = Get-Content -Path $statusFile -Raw -Encoding UTF8 | ConvertFrom-Json
    $summary = 'STATUS={0} STAGE={1} UPDATED_AT={2}' -f $status.status, $status.stage, $status.updated_at

    if ($status.message) {
        $summary = '{0} MESSAGE={1}' -f $summary, $status.message
    }

    if (Test-Path $progressFile) {
        try {
            $progress = Get-Content -Path $progressFile -Raw -Encoding UTF8 | ConvertFrom-Json
            if ($progress.total_clients) {
                $summary = '{0} PROGRESS={1}/{2}' -f $summary, $progress.completed_clients, $progress.total_clients
            }
            if ($progress.current_client_name) {
                $summary = '{0} CURRENT={1}' -f $summary, $progress.current_client_name
            }
        } catch {
        }
    }

    Write-Output $summary
} catch {
    Write-Output ('STATUS=error MESSAGE={0}' -f $_.Exception.Message)
}

