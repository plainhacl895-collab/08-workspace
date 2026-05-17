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

(Get-Item -LiteralPath $ManifestPath -Force).IsReadOnly = $false
$manifest = Get-Content -LiteralPath $ManifestPath -Raw -Encoding utf8 | ConvertFrom-Json
$workspaceRoot = $manifest.workspace_root
$unlockedPaths = @()

foreach ($relativePath in $manifest.protected_paths) {
    $targetPath = Join-Path $workspaceRoot $relativePath
    if (Test-Path -LiteralPath $targetPath) {
        $item = Get-Item -LiteralPath $targetPath -Force
        if (-not $item.PSIsContainer) {
            $item.IsReadOnly = $false
            $unlockedPaths += $targetPath
        }
    }
}

[pscustomobject]@{
    status = "ok"
    manifest_path = $ManifestPath
    unlocked_count = $unlockedPaths.Count
    unlocked_paths = $unlockedPaths
} | ConvertTo-Json -Depth 4

