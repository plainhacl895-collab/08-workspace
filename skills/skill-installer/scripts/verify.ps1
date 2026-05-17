# 技能验证脚本
# 用途：验证技能的元数据、依赖、结构是否正确

param(
    [string]$SkillName
)

$ErrorActionPreference = "Stop"
$SkillsDir = "C:\Users\Huawei\.openclaw\workspace-tuantuan\skills"
$SkillPath = Join-Path $SkillsDir $SkillName

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "技能验证：$SkillName" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# 检查 1: 技能目录是否存在
Write-Host "[1/6] 检查技能目录..." -ForegroundColor Yellow
if (Test-Path $SkillPath) {
    Write-Host "  ✅ 技能目录存在：$SkillPath" -ForegroundColor Green
} else {
    Write-Host "  ❌ 技能目录不存在：$SkillPath" -ForegroundColor Red
    exit 1
}

# 检查 2: SKILL.md 是否存在
Write-Host ""
Write-Host "[2/6] 检查 SKILL.md..." -ForegroundColor Yellow
$SkillMd = Join-Path $SkillPath "SKILL.md"
if (Test-Path $SkillMd) {
    Write-Host "  ✅ SKILL.md 存在" -ForegroundColor Green
    $lines = (Get-Content $SkillMd | Measure-Object -Line).Lines
    Write-Host "  📊 文件大小：$lines 行" -ForegroundColor Gray
} else {
    Write-Host "  ❌ SKILL.md 不存在" -ForegroundColor Red
    exit 1
}

# 检查 3: 元数据格式
Write-Host ""
Write-Host "[3/6] 验证元数据格式..." -ForegroundColor Yellow
$content = Get-Content $SkillMd -Raw

# 检查必需的元数据字段
if ($content -match '^\s*name:\s*(.+)$' -and $content -match '^\s*description:\s*(.+)$') {
    Write-Host "  ✅ 必需字段存在（name, description）" -ForegroundColor Green
} else {
    Write-Host "  ❌ 缺少必需字段（name 或 description）" -ForegroundColor Red
    exit 1
}

# 检查是否有无效的元数据字段
if ($content -match 'requires:') {
    Write-Host "  ⚠️  警告：发现 'requires' 字段（可能导致 needs setup 状态）" -ForegroundColor Yellow
    Write-Host "     建议移除：metadata 中不要包含 requires" -ForegroundColor Gray
}

# 检查 emoji
if ($content -match 'emoji:') {
    Write-Host "  ✅ emoji 字段存在" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  警告：缺少 emoji 字段" -ForegroundColor Yellow
}

# 检查 4: 目录结构
Write-Host ""
Write-Host "[4/6] 检查目录结构..." -ForegroundColor Yellow
$requiredDirs = @("scripts", "references")
foreach ($dir in $requiredDirs) {
    $dirPath = Join-Path $SkillPath $dir
    if (Test-Path $dirPath) {
        Write-Host "  ✅ 目录存在：$dir/" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  目录缺失：$dir/（推荐创建）" -ForegroundColor Yellow
    }
}

# 检查 5: 依赖检查
Write-Host ""
Write-Host "[5/6] 检查依赖..." -ForegroundColor Yellow
if ($content -match 'bins.*python') {
    Write-Host "  📌 需要 Python..." -ForegroundColor Gray
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        Write-Host "  ✅ Python 已安装：$($python.Version)" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Python 未安装" -ForegroundColor Red
    }
}

if ($content -match 'bins.*node') {
    Write-Host "  📌 需要 Node.js..." -ForegroundColor Gray
    $node = Get-Command node -ErrorAction SilentlyContinue
    if ($node) {
        Write-Host "  ✅ Node.js 已安装：$($node.Version)" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Node.js 未安装" -ForegroundColor Red
    }
}

# 检查 6: OpenClaw 是否能发现技能
Write-Host ""
Write-Host "[6/6] 检查 OpenClaw 技能发现..." -ForegroundColor Yellow
Write-Host "  📌 运行 openclaw skills list..." -ForegroundColor Gray
$skillList = openclaw skills list 2>&1
if ($skillList -match $SkillName) {
    Write-Host "  ✅ 技能已被 OpenClaw 发现" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  技能未被 OpenClaw 发现（可能需要重启）" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "验证完成！" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""
