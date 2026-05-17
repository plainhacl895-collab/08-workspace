# 技能安装脚本
# 用途：安全地安装技能，包含备份、验证、回滚机制

param(
    [string]$SkillName,
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$SkillsDir = "C:\Users\Huawei\.openclaw\workspace-tuantuan\skills"
$BackupDir = "C:\Users\Huawei\.openclaw\workspace-tuantuan\skills\.backups"
$Timestamp = Get-Date -Format "yyyyMMddHHmmss"

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "技能安装：$SkillName" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# 步骤 1: 检查技能目录是否存在
Write-Host "[1/5] 检查技能..." -ForegroundColor Yellow
$SkillPath = Join-Path $SkillsDir $SkillName
if (Test-Path $SkillPath) {
    if (-not $Force) {
        Write-Host "  ⚠️  技能已存在，使用 --force 覆盖安装" -ForegroundColor Yellow
        Write-Host "     或先运行：/skill-uninstall $SkillName" -ForegroundColor Gray
        exit 1
    } else {
        Write-Host "  ⚠️  技能已存在，将覆盖安装" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ✅ 技能不存在，将创建新技能" -ForegroundColor Green
}

# 步骤 2: 备份现有技能（如果存在）
Write-Host ""
Write-Host "[2/5] 备份现有技能..." -ForegroundColor Yellow
if (Test-Path $SkillPath) {
    if (-not (Test-Path $BackupDir)) {
        New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null
    }
    $BackupPath = Join-Path $BackupDir "$SkillName-$Timestamp"
    Copy-Item $SkillPath $BackupPath -Recurse -Force
    Write-Host "  ✅ 已备份到：$BackupPath" -ForegroundColor Green
} else {
    Write-Host "  ℹ️  无需备份（新技能）" -ForegroundColor Gray
}

# 步骤 3: 验证技能
Write-Host ""
Write-Host "[3/5] 验证技能..." -ForegroundColor Yellow
$VerifyScript = Join-Path $SkillPath "scripts\verify.ps1"
if (Test-Path $VerifyScript) {
    & $VerifyScript -SkillName $SkillName
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "  ❌ 技能验证失败，正在回滚..." -ForegroundColor Red
        if (Test-Path $BackupPath) {
            Remove-Item $SkillPath -Recurse -Force
            Copy-Item $BackupPath $SkillPath -Recurse -Force
            Write-Host "  ✅ 已回滚到备份版本" -ForegroundColor Green
        }
        exit 1
    }
} else {
    Write-Host "  ⚠️  验证脚本不存在，跳过验证" -ForegroundColor Yellow
}

# 步骤 4: 检查 OpenClaw 状态
Write-Host ""
Write-Host "[4/5] 检查 OpenClaw 状态..." -ForegroundColor Yellow
try {
    $status = openclaw status 2>&1
    Write-Host "  ✅ OpenClaw 运行正常" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️  OpenClaw 可能未运行，技能将在下次启动时加载" -ForegroundColor Yellow
}

# 步骤 5: 验证技能可加载
Write-Host ""
Write-Host "[5/5] 验证技能加载..." -ForegroundColor Yellow
Start-Sleep -Seconds 2
$skillList = openclaw skills list 2>&1
if ($skillList -match $SkillName) {
    Write-Host "  ✅ 技能已成功加载" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  技能未被加载（可能需要重启 OpenClaw）" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "安装完成！" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "下一步：" -ForegroundColor Yellow
Write-Host "1. 运行 '/skill-test $SkillName' 测试技能功能" -ForegroundColor White
Write-Host "2. 运行 'openclaw skills list' 查看技能列表" -ForegroundColor White
Write-Host "3. 如有问题，运行 '/skill-uninstall $SkillName --backup' 回滚" -ForegroundColor White
Write-Host ""
