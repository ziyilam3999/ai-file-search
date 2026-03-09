<#
.SYNOPSIS
    Initialize a repository with AI protocol files.
.DESCRIPTION
    Copies protocol files from ai-protocol to a target repository.
.PARAMETER TargetRepo
    Path to the target repository. Defaults to current directory.
.PARAMETER ProtocolRepo
    Path to the ai-protocol repository. Auto-detected if not specified.
.PARAMETER Force
    Overwrite existing files.
.PARAMETER SkipSync
    Don't add repo to sync_config.yaml.
.PARAMETER AutoInit
    (Deprecated) Git init now runs automatically. This flag is kept for backwards compatibility.
.PARAMETER IncludeTests
    Also copy tools/tests/ folder.
.PARAMETER WhatIf
    Preview mode - show what would be done without making changes.
.EXAMPLE
    .\init_protocol.ps1
    # Runs in current directory, auto-initializes git if needed
.EXAMPLE
    .\init_protocol.ps1 -TargetRepo "C:\path\to\new-project"
    # Initializes a new project folder with protocol files
#>
param(
    [Parameter(Position = 0)]
    [string]$TargetRepo = ".",

    [Parameter()]
    [string]$ProtocolRepo,

    [Parameter()]
    [switch]$Force,

    [Parameter()]
    [switch]$SkipSync,

    [Parameter()]
    [switch]$AutoInit,

    [Parameter()]
    [switch]$IncludeTests,

    [Parameter()]
    [switch]$WhatIf
)

# ═══════════════════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════════════════

$SCRIPT_VERSION = "1.0.0"
$DEFAULT_PROTOCOL_REPO = Split-Path $PSScriptRoot -Parent

$EXCLUDE_PATTERNS = @(
    "# AI Protocol files (managed by init_protocol.ps1)",
    ".github/copilot-instructions*.md",
    ".github/rules/",
    ".github/protocol-*.md",
    "tools/sync_copilot_instructions.ps1",
    "tools/extract_docs.ps1",
    "tools/tests/",
    "docs/",
    "tmp/",
    "CLAUDE.md",
    ".claude/"
)

# ═══════════════════════════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════════════════════════

function Test-GitRepository {
    param([Parameter(Mandatory)][string]$Path)
    $gitPath = Join-Path $Path ".git"
    return (Test-Path $gitPath -PathType Container)
}

function Copy-SingleFile {
    param(
        [string]$SourcePath,
        [string]$DestPath,
        [switch]$ForceOverwrite,
        [switch]$PreviewOnly
    )

    if (-not (Test-Path $SourcePath)) {
        Write-Warning "Source file not found: $SourcePath"
        return $false
    }

    $destDir = Split-Path $DestPath -Parent
    if (-not (Test-Path $destDir)) {
        if ($PreviewOnly) {
            Write-Host "  WhatIf: Would create directory: $destDir" -ForegroundColor Cyan
        } else {
            New-Item -ItemType Directory -Path $destDir -Force | Out-Null
        }
    }

    if ((Test-Path $DestPath) -and -not $ForceOverwrite) {
        Write-Verbose "Skipping existing file: $DestPath"
        return $false
    }

    if ($PreviewOnly) {
        Write-Host "  WhatIf: Would copy: $SourcePath -> $DestPath" -ForegroundColor Cyan
        return $true
    }

    Copy-Item -Path $SourcePath -Destination $DestPath -Force
    return $true
}

function Copy-FolderContents {
    param(
        [string]$SourceDir,
        [string]$DestDir,
        [switch]$ForceOverwrite,
        [switch]$PreviewOnly
    )

    if (-not (Test-Path $SourceDir)) {
        Write-Warning "Source folder not found: $SourceDir"
        return 0
    }

    $copied = 0
    $files = Get-ChildItem -Path $SourceDir -File -Recurse

    foreach ($file in $files) {
        $relativePath = $file.FullName.Substring($SourceDir.Length).TrimStart('\', '/')
        $destPath = Join-Path $DestDir $relativePath

        if (Copy-SingleFile -SourcePath $file.FullName -DestPath $destPath -ForceOverwrite:$ForceOverwrite -PreviewOnly:$PreviewOnly) {
            $copied++
        }
    }

    return $copied
}

function Setup-GitExclusions {
    param(
        [string]$RepoPath,
        [switch]$PreviewOnly
    )

    $excludeFile = Join-Path $RepoPath ".git\info\exclude"
    $infoDir = Split-Path $excludeFile -Parent

    if (-not (Test-Path $infoDir)) {
        if ($PreviewOnly) {
            Write-Host "  WhatIf: Would create directory: $infoDir" -ForegroundColor Cyan
            return
        }
        New-Item -ItemType Directory -Path $infoDir -Force | Out-Null
    }

    $existingContent = @()
    if (Test-Path $excludeFile) {
        $existingContent = Get-Content $excludeFile -ErrorAction SilentlyContinue
    }

    $newPatterns = @()
    foreach ($pattern in $EXCLUDE_PATTERNS) {
        $escapedPattern = [regex]::Escape($pattern)
        $exists = $existingContent | Where-Object { $_ -match "^$escapedPattern$" }
        if (-not $exists) {
            $newPatterns += $pattern
        }
    }

    if ($newPatterns.Count -gt 0) {
        if ($PreviewOnly) {
            Write-Host "  WhatIf: Would add exclusions to $excludeFile" -ForegroundColor Cyan
        } else {
            if ($existingContent.Count -gt 0) {
                Add-Content -Path $excludeFile -Value ""
            }
            Add-Content -Path $excludeFile -Value $newPatterns
        }
    }
}

function Generate-ClaudeMd {
    param(
        [string]$RepoPath,
        [switch]$PreviewOnly
    )

    $sourceFile = Join-Path $RepoPath ".github\copilot-instructions.md"
    $destFile = Join-Path $RepoPath "CLAUDE.md"

    if (-not (Test-Path $sourceFile)) {
        Write-Warning "Cannot generate CLAUDE.md: copilot-instructions.md not found"
        return
    }

    $content = Get-Content $sourceFile -Raw
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

    $version = "unknown"
    if ($content -match "copilot-instructions v([\d.]+)") {
        $version = $matches[1]
    }

    $header = "# CLAUDE.md`r`n"
    $header += "# AUTO-GENERATED - DO NOT EDIT DIRECTLY`r`n"
    $header += "# Source: .github/copilot-instructions.md`r`n"
    $header += "# Version: v$version`r`n"
    $header += "# Generated: $timestamp`r`n"
    $header += "`r`n"

    if ($PreviewOnly) {
        Write-Host "  WhatIf: Would generate: $destFile" -ForegroundColor Cyan
    } else {
        ($header + $content) | Set-Content $destFile -Encoding UTF8
    }
}

function Add-ToSyncConfig {
    param(
        [string]$ProtocolRepoPath,
        [string]$TargetRepoPath,
        [switch]$PreviewOnly
    )

    # Skip updating real sync_config.yaml during Pester tests
    # Tests should only modify the mock config in temp directory
    if ($env:PESTER_TESTING -eq '1') {
        # Only proceed if the protocol repo is in a temp directory (test isolation)
        $tempPath = [System.IO.Path]::GetTempPath()
        if (-not $ProtocolRepoPath.StartsWith($tempPath)) {
            Write-Verbose "Skipping sync_config update during tests (not in temp dir)"
            return
        }
    }

    $configFile = Join-Path $ProtocolRepoPath "sync_config.yaml"

    if (-not (Test-Path $configFile)) {
        Write-Warning "sync_config.yaml not found: $configFile"
        return
    }

    $repoName = Split-Path $TargetRepoPath -Leaf
    $config = Get-Content $configFile -Raw

    if ($config -match [regex]::Escape($repoName)) {
        Write-Verbose "Repository already in sync config: $repoName"
        return
    }

    if ($PreviewOnly) {
        Write-Host "  WhatIf: Would add to sync_config.yaml: $repoName" -ForegroundColor Cyan
        return
    }

    $lines = Get-Content $configFile
    $newLines = @()
    $inAllRepos = $false
    $lastRepoIndex = -1

    for ($i = 0; $i -lt $lines.Count; $i++) {
        $line = $lines[$i]
        $newLines += $line

        if ($line -match "^all_repos:") {
            $inAllRepos = $true
        } elseif ($inAllRepos -and $line -match "^\s+-\s+") {
            $lastRepoIndex = $newLines.Count - 1
        } elseif ($inAllRepos -and $line -notmatch "^\s+-" -and $line.Trim() -ne "" -and $line -notmatch "^\s*#") {
            $inAllRepos = $false
        }
    }

    if ($lastRepoIndex -gt 0) {
        $newEntry = "  - `"$repoName`""
        $result = @()
        for ($i = 0; $i -lt $newLines.Count; $i++) {
            $result += $newLines[$i]
            if ($i -eq $lastRepoIndex) {
                $result += $newEntry
            }
        }
        $result | Set-Content $configFile
        Write-Host "  Added to sync_config.yaml: $repoName" -ForegroundColor Green
    }
}

# ═══════════════════════════════════════════════════════════════════════════
# Main Function (for testability)
# ═══════════════════════════════════════════════════════════════════════════

function Initialize-Protocol {
    [CmdletBinding()]
    param(
        [Parameter(Position = 0)]
        [string]$TargetRepo = ".",

        [Parameter()]
        [string]$ProtocolRepo,

        [Parameter()]
        [switch]$Force,

        [Parameter()]
        [switch]$SkipSync,

        [Parameter()]
        [switch]$AutoInit,

        [Parameter()]
        [switch]$IncludeTests,

        [Parameter()]
        [switch]$WhatIf
    )

    # Resolve target path
    $resolvedPath = Resolve-Path $TargetRepo -ErrorAction SilentlyContinue
    if ($resolvedPath) {
        $TargetRepo = $resolvedPath.Path
    } else {
        throw "Target path does not exist: $TargetRepo"
    }

    # Set protocol repo
    if (-not $ProtocolRepo) {
        $ProtocolRepo = $DEFAULT_PROTOCOL_REPO
    }

    if (-not (Test-Path $ProtocolRepo)) {
        throw "Protocol repository not found: $ProtocolRepo"
    }

    # Display header
Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "       AI Protocol Initialization v$SCRIPT_VERSION" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Target:   $TargetRepo" -ForegroundColor White
Write-Host "Protocol: $ProtocolRepo" -ForegroundColor White
Write-Host ""

# Check for .git folder - auto-initialize if missing
if (-not (Test-GitRepository -Path $TargetRepo)) {
    if ($WhatIf) {
        Write-Host "  WhatIf: Would run 'git init' in $TargetRepo" -ForegroundColor Cyan
    } else {
        Write-Host "Initializing git repository..." -ForegroundColor Yellow
        Push-Location $TargetRepo
        git init 2>&1 | Out-Null
        Pop-Location
    }
}

$totalCopied = 0

# 1. Copy .github/copilot-instructions.md
Write-Host "[1/7] Copying copilot-instructions.md..." -ForegroundColor Cyan
$srcFile = Join-Path $ProtocolRepo ".github\copilot-instructions.md"
$dstFile = Join-Path $TargetRepo ".github\copilot-instructions.md"
if (Copy-SingleFile -SourcePath $srcFile -DestPath $dstFile -ForceOverwrite:$Force -PreviewOnly:$WhatIf) {
    $totalCopied++
}

# 2. Copy .github/rules/
Write-Host "[2/7] Copying .github/rules/..." -ForegroundColor Cyan
$srcDir = Join-Path $ProtocolRepo ".github\rules"
$dstDir = Join-Path $TargetRepo ".github\rules"
$totalCopied += Copy-FolderContents -SourceDir $srcDir -DestDir $dstDir -ForceOverwrite:$Force -PreviewOnly:$WhatIf

# 3. Copy .claude/commands/
Write-Host "[3/7] Copying .claude/commands/..." -ForegroundColor Cyan
$srcDir = Join-Path $ProtocolRepo ".claude\commands"
$dstDir = Join-Path $TargetRepo ".claude\commands"
$totalCopied += Copy-FolderContents -SourceDir $srcDir -DestDir $dstDir -ForceOverwrite:$Force -PreviewOnly:$WhatIf

# 4. Copy .claude/settings.local.json
Write-Host "[4/7] Copying .claude/settings.local.json..." -ForegroundColor Cyan
$srcFile = Join-Path $ProtocolRepo ".claude\settings.local.json"
$dstFile = Join-Path $TargetRepo ".claude\settings.local.json"
if (Copy-SingleFile -SourcePath $srcFile -DestPath $dstFile -ForceOverwrite:$Force -PreviewOnly:$WhatIf) {
    $totalCopied++
}

# 5. Copy tools/
Write-Host "[5/7] Copying tools/..." -ForegroundColor Cyan
$srcFile = Join-Path $ProtocolRepo "tools\sync_copilot_instructions.ps1"
$dstFile = Join-Path $TargetRepo "tools\sync_copilot_instructions.ps1"
if (Copy-SingleFile -SourcePath $srcFile -DestPath $dstFile -ForceOverwrite:$Force -PreviewOnly:$WhatIf) {
    $totalCopied++
}

$srcFile = Join-Path $ProtocolRepo "tools\extract_docs.ps1"
$dstFile = Join-Path $TargetRepo "tools\extract_docs.ps1"
if (Copy-SingleFile -SourcePath $srcFile -DestPath $dstFile -ForceOverwrite:$Force -PreviewOnly:$WhatIf) {
    $totalCopied++
}

if ($IncludeTests) {
    $srcDir = Join-Path $ProtocolRepo "tools\tests"
    $dstDir = Join-Path $TargetRepo "tools\tests"
    $totalCopied += Copy-FolderContents -SourceDir $srcDir -DestDir $dstDir -ForceOverwrite:$Force -PreviewOnly:$WhatIf
}

# 6. Initialize docs/
Write-Host "[6/7] Initializing docs/..." -ForegroundColor Cyan
$templatesDir = Join-Path $ProtocolRepo "docs\_templates"
$docsDir = Join-Path $TargetRepo "docs"
$totalCopied += Copy-FolderContents -SourceDir $templatesDir -DestDir $docsDir -ForceOverwrite:$Force -PreviewOnly:$WhatIf

# Create tmp folder
$tmpDir = Join-Path $TargetRepo "tmp"
if (-not (Test-Path $tmpDir)) {
    if ($WhatIf) {
        Write-Host "  WhatIf: Would create directory: $tmpDir" -ForegroundColor Cyan
    } else {
        New-Item -ItemType Directory -Path $tmpDir -Force | Out-Null
        "# Keep this folder in git" | Set-Content (Join-Path $tmpDir ".gitkeep")
    }
}

# 7. Setup git exclusions
Write-Host "[7/7] Setting up git exclusions..." -ForegroundColor Cyan
Setup-GitExclusions -RepoPath $TargetRepo -PreviewOnly:$WhatIf

# Generate CLAUDE.md
Write-Host ""
Write-Host "Generating CLAUDE.md..." -ForegroundColor Cyan
Generate-ClaudeMd -RepoPath $TargetRepo -PreviewOnly:$WhatIf

# Update sync config
if (-not $SkipSync) {
    Write-Host "Updating sync_config.yaml..." -ForegroundColor Cyan
    Add-ToSyncConfig -ProtocolRepoPath $ProtocolRepo -TargetRepoPath $TargetRepo -PreviewOnly:$WhatIf
}

# Summary
Write-Host ""
Write-Host "================================================================" -ForegroundColor Green
Write-Host "              Initialization Complete" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Green

if ($WhatIf) {
    Write-Host ""
    Write-Host "  WhatIf mode - no changes were made" -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "  Files copied: $totalCopied" -ForegroundColor White
    Write-Host "  Git exclusions: configured" -ForegroundColor White
    Write-Host "  CLAUDE.md: generated" -ForegroundColor White
    if (-not $SkipSync) {
        Write-Host "  sync_config.yaml: updated" -ForegroundColor White
    }
}

Write-Host ""
Write-Host "  Next steps:" -ForegroundColor Yellow
Write-Host "  1. Review generated files" -ForegroundColor White
Write-Host "  2. Edit docs/ai-manifest.json with project info" -ForegroundColor White
Write-Host "  3. Run .\tools\sync_copilot_instructions.ps1 to sync" -ForegroundColor White
Write-Host ""
}

# ═══════════════════════════════════════════════════════════════════════════
# Script Entry Point (runs when invoked directly, not when dot-sourced)
# ═══════════════════════════════════════════════════════════════════════════

# Guard: Skip entry point when testing (set $env:PESTER_TESTING = '1' in test setup)
# or when explicitly imported as module
if ($env:PESTER_TESTING -ne '1') {
    Initialize-Protocol `
        -TargetRepo $TargetRepo `
        -ProtocolRepo $ProtocolRepo `
        -Force:$Force `
        -SkipSync:$SkipSync `
        -AutoInit:$AutoInit `
        -IncludeTests:$IncludeTests `
        -WhatIf:$WhatIf
}