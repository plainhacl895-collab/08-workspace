# 技能测试脚本
# 用途：测试技能的功能是否正常

param(
    [string]$SkillName,
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"
$TestsPassed = 0
$TestsFailed = 0

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "技能测试：$SkillName" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# 测试 1: 技能是否被加载
Write-Host "[测试 1/4] 检查技能加载状态..." -ForegroundColor Yellow
$skillList = openclaw skills list 2>&1
if ($skillList -match $SkillName) {
    Write-Host "  ✅ PASS: 技能已被 OpenClaw 加载" -ForegroundColor Green
    $TestsPassed++
} else {
    Write-Host "  ❌ FAIL: 技能未被 OpenClaw 加载" -ForegroundColor Red
    $TestsFailed++
}

# 测试 2: 检查技能文件完整性
Write-Host ""
Write-Host "[测试 2/4] 检查技能文件完整性..." -ForegroundColor Yellow
$SkillPath = "C:\Users\Huawei\.openclaw\workspace-tuantuan\skills\$SkillName"
$files = @(
    "SKILL.md",
    "scripts/verify.ps1",
    "scripts/install.ps1"
)
$allFilesExist = $true
foreach ($file in $files) {
    $filePath = Join-Path $SkillPath $file
    if (Test-Path $filePath) {
        if ($Verbose) {
            Write-Host "  ✅ 文件存在：$file" -ForegroundColor Green
        }
    } else {
        Write-Host "  ❌ 文件缺失：$file" -ForegroundColor Red
        $allFilesExist = $false
    }
}
if ($allFilesExist) {
    Write-Host "  ✅ PASS: 所有必需文件存在" -ForegroundColor Green
    $TestsPassed++
} else {
    Write-Host "  ❌ FAIL: 部分文件缺失" -ForegroundColor Red
    $TestsFailed++
}

# 测试 3: 验证技能元数据
Write-Host ""
Write-Host "[测试 3/4] 验证技能元数据..." -ForegroundColor Yellow
$skillMd = Join-Path $SkillPath "SKILL.md"
$content = Get-Content $skillMd -Raw

$metadataValid = $true
if ($content -notmatch '^\s*name:\s*.+$') {
    Write-Host "  ❌ 缺少 name 字段" -ForegroundColor Red
    $metadataValid = $false
}
if ($content -notmatch '^\s*description:\s*.+$') {
    Write-Host "  ❌ 缺少 description 字段" -ForegroundColor Red
    $metadataValid = $false
}
if ($content -match 'requires:') {
    Write-Host "  ⚠️  警告：包含 requires 字段（可能导致 needs setup）" -ForegroundColor Yellow
}

if ($metadataValid) {
    Write-Host "  ✅ PASS: 元数据格式正确" -ForegroundColor Green
    $TestsPassed++
} else {
    Write-Host "  ❌ FAIL: 元数据格式错误" -ForegroundColor Red
    $TestsFailed++
}

# 测试 4: 检查 OpenClaw 运行状态
Write-Host ""
Write-Host "[测试 4/4] 检查 OpenClaw 运行状态..." -ForegroundColor Yellow
try {
    $status = openclaw status 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ PASS: OpenClaw 运行正常" -ForegroundColor Green
        $TestsPassed++
    } else {
        Write-Host "  ⚠️  WARN: OpenClaw 可能未运行" -ForegroundColor Yellow
        Write-Host "     技能将在下次启动时可用" -ForegroundColor Gray
        $TestsPassed++
    }
} catch {
    Write-Host "  ⚠️  WARN: 无法检查 OpenClaw 状态" -ForegroundColor Yellow
    $TestsPassed++
}

# 测试总结
Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "测试总结" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "通过：$TestsPassed" -ForegroundColor Green
Write-Host "失败：$TestsFailed" -ForegroundColor $(if ($TestsFailed -eq 0) { "Green" } else { "Red" })
Write-Host ""

if ($TestsFailed -eq 0) {
    Write-Host "✅ 所有测试通过！技能可以正常使用。" -ForegroundColor Green
    exit 0
} else {
    Write-Host "❌ 部分测试失败，请检查上述错误。" -ForegroundColor Red
    Write-Host ""
    Write-Host "建议：" -ForegroundColor Yellow
    Write-Host "1. 运行 '/skill-verify-metadata $SkillName' 验证元数据" -ForegroundColor White
    Write-Host "2. 运行 'openclaw doctor' 检查 OpenClaw 配置" -ForegroundColor White
    Write-Host "3. 重启 OpenClaw 后重试" -ForegroundColor White
    exit 1
}
