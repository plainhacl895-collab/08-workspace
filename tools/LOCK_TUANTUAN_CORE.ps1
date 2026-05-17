param(
    [string]$ManifestPath
)

$ErrorActionPreference = "Stop"

if (-not $ManifestPath) {
    $workspaceRoot = Split-Path -Parent $PSScriptRoot
    $ManifestPath = Join-Path $workspaceRoot "workspace\config\protected_core.json"
}

if (-not (Test-Path -LiteralPath $ManifestPath)) {
    throw "Protected core manifest not found: $ManifestPath"
}

$manifest = Get-Content -LiteralPath $ManifestPath -Raw -Encoding utf8 | ConvertFrom-Json
$workspaceRoot = $manifest.workspace_root
$lockedPaths = @()

foreach ($relativePath in $manifest.protected_paths) {
    $targetPath = Join-Path $workspaceRoot $relativePath
    if (Test-Path -LiteralPath $targetPath) {
        $item = Get-Item -LiteralPath $targetPath -Force
        if (-not $item.PSIsContainer) {
            $item.IsReadOnly = $true
            $lockedPaths += $targetPath
        }
    }
}

if (Test-Path -LiteralPath $ManifestPath) {
    (Get-Item -LiteralPath $ManifestPath -Force).IsReadOnly = $true
}

[pscustomobject]@{
    status = "ok"
    manifest_path = $ManifestPath
    locked_count = $lockedPaths.Count
    locked_paths = $lockedPaths
} | ConvertTo-Json -Depth 4

