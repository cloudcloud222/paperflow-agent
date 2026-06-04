# pack_source.ps1
# Paper-Agent 脱敏源码打包脚本
# 会排除虚拟环境、API Key、真实论文材料、输出结果、缓存文件等

$ProjectPath = "E:\paper-agent"
$OutputDir = "E:\"
$ZipName = "paper-agent_source_clean.zip"
$ZipPath = Join-Path $OutputDir $ZipName
$TempDir = Join-Path $OutputDir "paper-agent_source_temp"

$ExcludeDirs = @(
    ".git",
    ".venv",
    "venv",
    "env",
    ".vscode",
    ".idea",
    "__pycache__",
    "data",
    "build",
    "dist",
    ".mypy_cache",
    ".pytest_cache"
)

$ExcludeFiles = @(
    ".env",
    ".env.*",
    "*.log",
    "*.pyc",
    "*.pyo",
    "*.tmp",
    "*.bak",
    "*.pdf",
    "*.docx",
    "*.doc",
    "*.xlsx",
    "*.pptx",
    "secrets.json",
    "api_keys.json",
    "config.local.yaml",
    "config.local.yml",
    "config.local.json"
)

if (Test-Path $ZipPath) {
    Remove-Item $ZipPath -Force
}

if (Test-Path $TempDir) {
    Remove-Item $TempDir -Recurse -Force
}

New-Item -ItemType Directory -Path $TempDir | Out-Null

Get-ChildItem -Path $ProjectPath -Force | ForEach-Object {
    $Name = $_.Name
    $FullName = $_.FullName

    if ($_.PSIsContainer -and ($ExcludeDirs -contains $Name)) {
        Write-Host "跳过目录：" $Name
        return
    }

    $ShouldExclude = $false
    foreach ($Pattern in $ExcludeFiles) {
        if ($Name -like $Pattern) {
            $ShouldExclude = $true
            break
        }
    }

    if ($ShouldExclude) {
        Write-Host "跳过文件：" $Name
        return
    }

    Copy-Item -Path $FullName -Destination $TempDir -Recurse -Force
}

Compress-Archive -Path "$TempDir\*" -DestinationPath $ZipPath -Force

Remove-Item $TempDir -Recurse -Force

Write-Host ""
Write-Host "脱敏源码已打包完成：" $ZipPath
Write-Host "请检查压缩包内不要包含 .env、data、真实论文、API Key、输出结果等敏感内容。"
