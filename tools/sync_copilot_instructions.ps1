<#
.SYNOPSIS
    Sync copilot-instructions.md from current repo to target repos with auto-exclusion.

.DESCRIPTION
    This script detects copilot-instructions.md in the current repo and syncs it to
    specified target repositories. It automatically configures .git/info/exclude to
    prevent the file from being committed and verifies the exclusion.

.EXAMPLE
    .\sync_copilot_instructions.ps1
    
.NOTES
    Author: AI File Search Project
    Date: 2025-12-23
#>

# Target repositories
$targetRepos = @(
    "C:\Users\ziyil\pillar_snapper",
    "C:\Users\ziyil\ai-file-search"
)

# Colors for output
function Write-Success { param($msg) Write-Host "✓ $msg" -ForegroundColor Green }
function Write-Info { param($msg) Write-Host "→ $msg" -ForegroundColor Cyan }
function Write-Warning { param($msg) Write-Host "⚠ $msg" -ForegroundColor Yellow }
function Write-Error { param($msg) Write-Host "✗ $msg" -ForegroundColor Red }

# Detect source file in current repo
function Find-SourceFile {
    $currentDir = Get-Location
    $possiblePaths = @(
        Join-Path $currentDir ".github\copilot-instructions.md"
        Join-Path $currentDir "copilot-instructions.md"
    )
    
    foreach ($path in $possiblePaths) {
        if (Test-Path $path) {
            return $path
        }
    }
    
    return $null
}

# Add exclusion to .git/info/exclude
function Add-GitExclusion {
    param(
        [string]$repoPath,
        [string]$pattern = ".github/copilot-instructions.md"
    )
    
    $excludeFile = Join-Path $repoPath ".git\info\exclude"
    
    # Check if .git exists
    if (-not (Test-Path (Join-Path $repoPath ".git"))) {
        Write-Warning "Not a git repository: $repoPath"
        return $false
    }
    
    # Create exclude file if doesn't exist
    if (-not (Test-Path $excludeFile)) {
        New-Item -ItemType File -Path $excludeFile -Force | Out-Null
    }
    
    # Check if pattern already exists
    $content = Get-Content $excludeFile -ErrorAction SilentlyContinue
    if ($content -contains $pattern) {
        Write-Info "Exclusion already exists in: $repoPath"
        return $true
    }
    
    # Add pattern
    Add-Content -Path $excludeFile -Value $pattern
    Write-Success "Added exclusion to: $repoPath"
    return $true
}

# Verify file is ignored by git
function Test-GitIgnored {
    param(
        [string]$repoPath,
        [string]$file = ".github\copilot-instructions.md"
    )
    
    Push-Location $repoPath
    try {
        $status = git status --porcelain $file 2>$null
        if ([string]::IsNullOrWhiteSpace($status)) {
            Write-Success "Verified ignored in: $repoPath"
            return $true
        } else {
            Write-Warning "File still tracked in: $repoPath (Status: $status)"
            return $false
        }
    } finally {
        Pop-Location
    }
}

# Main execution
Write-Info "Starting Copilot Instructions Sync..."
Write-Host ""

# Step 1: Find source file
Write-Info "Step 1: Detecting source file..."
$sourceFile = Find-SourceFile

if (-not $sourceFile) {
    Write-Error "Could not find copilot-instructions.md in current directory"
    Write-Info "Searched in:"
    Write-Host "  - .github\copilot-instructions.md"
    Write-Host "  - copilot-instructions.md"
    exit 1
}

Write-Success "Found source: $sourceFile"
$sourceHash = (Get-FileHash $sourceFile -Algorithm MD5).Hash
Write-Info "Source MD5: $sourceHash"
Write-Host ""

# Step 2: Sync to targets
Write-Info "Step 2: Syncing to target repositories..."
$syncCount = 0
$excludeCount = 0
$verifyCount = 0

foreach ($targetRepo in $targetRepos) {
    Write-Host ""
    Write-Info "Processing: $targetRepo"
    
    # Check if target repo exists
    if (-not (Test-Path $targetRepo)) {
        Write-Warning "Repository not found, skipping: $targetRepo"
        continue
    }
    
    # Create .github directory if needed
    $targetGithubDir = Join-Path $targetRepo ".github"
    if (-not (Test-Path $targetGithubDir)) {
        New-Item -ItemType Directory -Path $targetGithubDir -Force | Out-Null
        Write-Success "Created .github directory"
    }
    
    # Copy file
    $targetFile = Join-Path $targetGithubDir "copilot-instructions.md"
    try {
        Copy-Item -Path $sourceFile -Destination $targetFile -Force
        $targetHash = (Get-FileHash $targetFile -Algorithm MD5).Hash
        
        if ($targetHash -eq $sourceHash) {
            Write-Success "Synced successfully (MD5 verified)"
            $syncCount++
        } else {
            Write-Warning "Synced but hash mismatch"
        }
    } catch {
        Write-Error "Failed to copy: $_"
        continue
    }
    
    # Add exclusion
    if (Add-GitExclusion -repoPath $targetRepo) {
        $excludeCount++
    }
    
    # Verify ignored
    if (Test-GitIgnored -repoPath $targetRepo) {
        $verifyCount++
    }
}

# Summary
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "Sync Summary:" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Source File:        $sourceFile"
Write-Host "  Target Repos:       $($targetRepos.Count)"
Write-Host "  Files Synced:       $syncCount"
Write-Host "  Exclusions Added:   $excludeCount"
Write-Host "  Verified Ignored:   $verifyCount"
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan

if ($syncCount -eq $targetRepos.Count) {
    Write-Host ""
    Write-Success "All operations completed successfully!"
    exit 0
} else {
    Write-Host ""
    Write-Warning "Some operations failed. Review output above."
    exit 1
}
