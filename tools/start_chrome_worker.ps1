param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"

$DebugPort = 9222
$ProfileDir = "$env:LOCALAPPDATA\Google\Chrome\User Data"
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

# 端口已就绪 → 直接复用
if (Test-DebugPort -Port $DebugPort) {
    Write-Output "DEBUG_PORT_READY:$DebugPort"
    exit 0
}

# 端口未就绪 → 需要启动带调试端口的 Chrome
# 因为现在复用日常 Chrome Profile，必须关掉已有的 Chrome 才能加 --remote-debugging-port
$runningChrome = Get-CimInstance Win32_Process |
    Where-Object { $_.Name -eq "chrome.exe" -and $_.CommandLine -notmatch "--type=crashpad-handler" }

if ($runningChrome) {
    if (-not $Force) {
        Write-Output "CHROME_RUNNING_WITHOUT_DEBUG_PORT"
        Write-Output "日常 Chrome 正在运行但没有调试端口，请先关闭 Chrome 或加 -Force 自动重启。"
        exit 2
    }
    # Force 模式：关闭所有 Chrome 后重新以调试端口启动
    Get-CimInstance Win32_Process | Where-Object { $_.Name -eq "chrome.exe" } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
    Start-Sleep -Seconds 2
}
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
