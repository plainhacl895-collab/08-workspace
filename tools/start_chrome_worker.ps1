param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"

$DebugPort = 9222
$ProfileDir = "C:\Users\Huawei\.openclaw\workspace-tuantuan\tools\ChromeDebugProfile"
$TargetUrl = "https://house.link.lianjia.com/search/sale/default/gdiv_mt"

function Test-DebugPort {
    param([int]$Port)

    try {
        $client = New-Object System.Net.Sockets.TcpClient
        $async = $client.BeginConnect("127.0.0.1", $Port, $null, $null)
        $ok = $async.AsyncWaitHandle.WaitOne(1000, $false)
        if ($ok -and $client.Connected) {
            $client.EndConnect($async) | Out-Null
            $client.Close()
            return $true
        }
        $client.Close()
        return $false
    } catch {
        return $false
    }
}

function Get-ChromePath {
    $candidates = @(
        "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
        "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
        "$env:LocalAppData\Google\Chrome\Application\chrome.exe"
    )

    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path -LiteralPath $candidate)) {
            return $candidate
        }
    }

    throw "Chrome executable not found"
}

if ($Force) {
    Get-CimInstance Win32_Process |
        Where-Object { $_.Name -eq "chrome.exe" -and $_.CommandLine -match "--remote-debugging-port=$DebugPort" -and $_.CommandLine -match [regex]::Escape($ProfileDir) } |
        ForEach-Object {
            Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        }
    Start-Sleep -Seconds 2
}

if (Test-DebugPort -Port $DebugPort) {
    Write-Output "DEBUG_PORT_READY:$DebugPort"
    exit 0
}

New-Item -ItemType Directory -Force -Path $ProfileDir | Out-Null
$chromePath = Get-ChromePath

$arguments = @(
    "--remote-debugging-port=$DebugPort",
    "--user-data-dir=$ProfileDir",
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-gpu",
    "--disable-software-rasterizer",
    "--disable-dev-shm-usage",
    "--disable-extensions-except=*",
    "--disable-notifications",
    "--disable-background-networking",
    "--disable-default-apps",
    "--disable-hang-monitor",
    "--disable-sync",
    "--no-first-run",
    "--no-default-browser-check",
    "--start-maximized",
    $TargetUrl
)

Write-Output "Starting Chrome with debugger..."
Start-Process -FilePath $chromePath -ArgumentList $arguments -WindowStyle Normal | Out-Null

Write-Output "Waiting for Chrome debugger port..."
for ($i = 0; $i -lt 45; $i++) {
    Start-Sleep -Seconds 1
    if (Test-DebugPort -Port $DebugPort) {
        Write-Output "DEBUG_PORT_READY:$DebugPort"
        Write-Output "Chrome started successfully on port $DebugPort"
        exit 0
    }
    if ($i % 10 -eq 9) {
        Write-Output "Still waiting... ($($i + 1)/45)"
    }
}

throw "Chrome debug port $DebugPort failed to start after 45 seconds"
