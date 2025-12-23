<#
.SYNOPSIS
    Sync copilot-instructions.md from current repo to target repos with auto-exclusion.

.DESCRIPTION
    This script detects copilot-instructions.md in the current repo and syncs it to
    specified target repositories. It automatically configures .git/info/exclude to
    prevent the file from being committed and verifies the exclusion.
    
    The script also syncs itself to target repos, ensuring all repos have the latest
    version of the sync tool.

.EXAMPLE
    .\sync_copilot_instructions.ps1
    
.NOTES
    Author: AI File Search Project
    Version: 1.0.0
    Date: 2025-12-23
#>

[CmdletBinding()]
param()

# Script version (update this when making changes)
$SCRIPT_VERSION = [version]"1.0.0"
$SCRIPT_NAME = "sync_copilot_instructions.ps1"

# Constants
$COPILOT_FILE_NAME = "copilot-instructions.md"
$GITHUB_DIR = ".github"
$TOOLS_DIR = "tools"
$GIT_EXCLUDE_PATH = ".git\info\exclude"
$VERSION_REGEX = 'copilot-instructions v([\d.]+)'
$SCRIPT_VERSION_REGEX = 'Version:\s*([\d.]+)'

# ═══════════════════════════════════════════════════════════════════════════
# TARGET REPOSITORIES CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════
# Add repository paths here. Script will:
# 1. Create .github folder if missing
# 2. Sync copilot-instructions.md if target version is older (or missing)
# 3. Auto-untrack if file is tracked in git
# 4. Add to .git/info/exclude
# 5. Verify file is ignored
#
# To add a new repository:
# - Add absolute path to the array below
# - Ensure path exists and is a git repository
# ═══════════════════════════════════════════════════════════════════════════

$TARGET_REPOS = @(
    "C:\Users\ziyil\pillar_snapper",
    "C:\Users\ziyil\ai-file-search",
    "C:\Users\ziyil\GetSpace"
)

# Output formatting functions
function Write-Success { 
    [CmdletBinding()]
    param([Parameter(Mandatory)][string]$Message) 
    Write-Host "✓ $Message" -ForegroundColor Green 
}

function Write-Info { 
    [CmdletBinding()]
    param([Parameter(Mandatory)][string]$Message) 
    Write-Host "→ $Message" -ForegroundColor Cyan 
}

function Write-Warning { 
    [CmdletBinding()]
    param([Parameter(Mandatory)][string]$Message) 
    Write-Host "⚠ $Message" -ForegroundColor Yellow 
}

function Write-Error { 
    [CmdletBinding()]
    param([Parameter(Mandatory)][string]$Message) 
    Write-Host "✗ $Message" -ForegroundColor Red 
}

function Write-SectionDivider {
    [CmdletBinding()]
    param([Parameter(Mandatory)][string]$Title)
    Write-Host ""
    Write-Host ("═" * 55) -ForegroundColor Cyan
    Write-Host $Title -ForegroundColor Cyan
    Write-Host ("═" * 55) -ForegroundColor Cyan
}

# Parse version from copilot-instructions.md first line
function Get-CopilotVersion {
    [CmdletBinding()]
    [OutputType([version])]
    param(
        [Parameter(Mandatory)]
        [string]$FilePath
    )
    
    if (-not (Test-Path $FilePath)) {
        return $null
    }
    
    try {
        $firstLine = Get-Content $FilePath -First 1 -ErrorAction Stop
        if ($firstLine -match $VERSION_REGEX) {
            return [version]$matches[1]
        }
    } catch {
        Write-Warning -Message "Could not read version from: $FilePath"
    }
    
    return $null
}

# Parse version from script .NOTES section
function Get-ScriptVersion {
    [CmdletBinding()]
    [OutputType([version])]
    param(
        [Parameter(Mandatory)]
        [string]$FilePath
    )
    
    if (-not (Test-Path $FilePath)) {
        return $null
    }
    
    try {
        $content = Get-Content $FilePath -First 30 -ErrorAction Stop
        foreach ($line in $content) {
            if ($line -match $SCRIPT_VERSION_REGEX) {
                return [version]$matches[1]
            }
        }
    } catch {
        Write-Warning -Message "Could not read script version from: $FilePath"
    }
    
    return $null
}

# Compare two versions
function Compare-CopilotVersion {
    [CmdletBinding()]
    [OutputType([bool])]
    param(
        [Parameter(Mandatory)]
        [AllowNull()]
        [version]$SourceVersion,
        
        [Parameter(Mandatory)]
        [AllowNull()]
        [version]$TargetVersion
    )
    
    # If target has no version, treat as v0.0 (always update)
    if ($null -eq $TargetVersion) {
        return $true
    }
    
    # If source has no version but target does, don't update
    if ($null -eq $SourceVersion) {
        return $false
    }
    
    # Compare versions
    return $SourceVersion -gt $TargetVersion
}

# Check if two paths are the same
function Test-SamePath {
    [CmdletBinding()]
    [OutputType([bool])]
    param(
        [Parameter(Mandatory)]
        [string]$Path1,
        
        [Parameter(Mandatory)]
        [string]$Path2
    )
    
    try {
        $resolved1 = [System.IO.Path]::GetFullPath($Path1).TrimEnd('\', '/')
        $resolved2 = [System.IO.Path]::GetFullPath($Path2).TrimEnd('\', '/')
        return $resolved1 -eq $resolved2
    } catch {
        Write-Verbose "Path comparison failed: $_"
        return $false
    }
}

# Detect source file in current repo
function Find-SourceFile {
    [CmdletBinding()]
    [OutputType([string])]
    param()
    
    $currentDir = Get-Location
    $possiblePaths = @(
        Join-Path $currentDir "$GITHUB_DIR\$COPILOT_FILE_NAME"
        Join-Path $currentDir $COPILOT_FILE_NAME
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
    [CmdletBinding()]
    [OutputType([bool])]
    param(
        [Parameter(Mandatory)]
        [string]$RepoPath,
        
        [Parameter()]
        [string]$Pattern = "$GITHUB_DIR/$COPILOT_FILE_NAME"
    )
    
    $excludeFile = Join-Path $RepoPath $GIT_EXCLUDE_PATH
    
    # Check if .git exists
    if (-not (Test-Path (Join-Path $RepoPath ".git"))) {
        Write-Warning -Message "Not a git repository: $RepoPath"
        return $false
    }
    
    # Create exclude file if doesn't exist
    if (-not (Test-Path $excludeFile)) {
        New-Item -ItemType File -Path $excludeFile -Force | Out-Null
    }
    
    # Check if pattern already exists
    $content = Get-Content $excludeFile -ErrorAction SilentlyContinue
    if ($content -contains $Pattern) {
        Write-Info -Message "Exclusion already exists in: $RepoPath"
        return $true
    }
    
    # Add pattern
    Add-Content -Path $excludeFile -Value $Pattern
    Write-Success -Message "Added exclusion to: $RepoPath"
    return $true
}

# Verify file is ignored by git
function Test-GitIgnored {
    [CmdletBinding()]
    [OutputType([bool])]
    param(
        [Parameter(Mandatory)]
        [string]$RepoPath,
        
        [Parameter()]
        [string]$File = "$GITHUB_DIR\$COPILOT_FILE_NAME"
    )
    
    Push-Location $RepoPath
    try {
        $status = git status --porcelain $File 2>$null
        if ([string]::IsNullOrWhiteSpace($status)) {
            Write-Success -Message "Verified ignored in: $RepoPath"
            return $true
        } else {
            Write-Warning -Message "File still tracked in: $RepoPath (Status: $status)"
            return $false
        }
    } catch {
        Write-Verbose "Git status check failed: $_"
        return $false
    } finally {
        Pop-Location
    }
}

# Check if file is tracked in git index
function Test-GitTracked {
    [CmdletBinding()]
    [OutputType([bool])]
    param(
        [Parameter(Mandatory)]
        [string]$RepoPath,
        
        [Parameter()]
        [string]$File = "$GITHUB_DIR/$COPILOT_FILE_NAME"
    )
    
    Push-Location $RepoPath
    try {
        # git ls-files returns non-empty if file is tracked
        $tracked = git ls-files $File 2>$null
        return -not [string]::IsNullOrWhiteSpace($tracked)
    } catch {
        Write-Verbose "Git ls-files check failed: $_"
        return $false
    } finally {
        Pop-Location
    }
}

# Remove file from git index (stop tracking)
function Remove-FromGitIndex {
    [CmdletBinding()]
    [OutputType([bool])]
    param(
        [Parameter(Mandatory)]
        [string]$RepoPath,
        
        [Parameter()]
        [string]$File = "$GITHUB_DIR/$COPILOT_FILE_NAME"
    )
    
    Push-Location $RepoPath
    try {
        # Remove from index but keep working copy
        $result = git rm --cached $File 2>&1
        if ($LASTEXITCODE -eq 0) {
            # Commit the removal
            git commit -m "chore: stop tracking $COPILOT_FILE_NAME" 2>&1 | Out-Null
            if ($LASTEXITCODE -eq 0) {
                Write-Success -Message "Removed from git tracking: $File"
                return $true
            } else {
                Write-Warning -Message "Failed to commit removal of $File"
                return $false
            }
        } else {
            Write-Warning -Message "Failed to remove from index: $result"
            return $false
        }
    } catch {
        Write-Warning -Message "Error removing from git index: $_"
        return $false
    } finally {
        Pop-Location
    }
}

# Sync result object for better structure
function New-SyncResult {
    [CmdletBinding()]
    param(
        [int]$Synced = 0,
        [int]$Skipped = 0,
        [int]$Excluded = 0,
        [int]$Untracked = 0,
        [int]$Verified = 0,
        [int]$ScriptsSynced = 0
    )
    
    return [PSCustomObject]@{
        Synced = $Synced
        Skipped = $Skipped
        Excluded = $Excluded
        Untracked = $Untracked
        Verified = $Verified
        ScriptsSynced = $ScriptsSynced
    }
}

# Main execution
Write-Info -Message "Starting Copilot Instructions Sync..."
Write-Host ""

# Step 1: Find source file
Write-Info -Message "Step 1: Detecting source file and script..."
$sourceFile = Find-SourceFile

if (-not $sourceFile) {
    Write-Error -Message "Could not find $COPILOT_FILE_NAME in current directory"
    Write-Info -Message "Searched in:"
    Write-Host "  - $GITHUB_DIR\$COPILOT_FILE_NAME"
    Write-Host "  - $COPILOT_FILE_NAME"
    exit 1
}

Write-Success -Message "Found source: $sourceFile"
$sourceVersion = Get-CopilotVersion -FilePath $sourceFile
if ($sourceVersion) {
    Write-Info -Message "Source version: v$sourceVersion"
} else {
    Write-Warning -Message "No version found in source (will be treated as v0.0)"
}
$sourceHash = (Get-FileHash $sourceFile -Algorithm MD5).Hash
Write-Info -Message "Source MD5: $sourceHash"

# Get source directory for path comparison
$sourceDir = Split-Path (Resolve-Path $sourceFile).Path -Parent
$sourceRepoRoot = Split-Path $sourceDir -Parent

# Locate this script
$scriptPath = $PSCommandPath
Write-Info -Message "Script version: v$SCRIPT_VERSION"
Write-Info -Message "Script path: $scriptPath"
$scriptHash = (Get-FileHash $scriptPath -Algorithm MD5).Hash

# Check if source file is tracked in source repo and untrack if needed
Write-Host ""
Write-Info -Message "Checking source repository..."
if (Test-GitTracked -RepoPath $sourceRepoRoot -File "$GITHUB_DIR/$COPILOT_FILE_NAME") {
    Write-Info -Message "Source file is tracked in git, removing from index..."
    if (Remove-FromGitIndex -RepoPath $sourceRepoRoot -File "$GITHUB_DIR/$COPILOT_FILE_NAME") {
        Write-Success -Message "Source repo: File untracked successfully"
    }
} else {
    Write-Info -Message "Source file is not tracked (good)"
}

# Check if source script is tracked and untrack if needed
if (Test-GitTracked -RepoPath $sourceRepoRoot -File "$TOOLS_DIR/$SCRIPT_NAME") {
    Write-Info -Message "Source script is tracked in git, removing from index..."
    if (Remove-FromGitIndex -RepoPath $sourceRepoRoot -File "$TOOLS_DIR/$SCRIPT_NAME") {
        Write-Success -Message "Source repo: Script untracked successfully"
    }
} else {
    Write-Info -Message "Source script is not tracked (good)"
}

# Ensure source has exclusions configured
if (-not (Test-Path (Join-Path $sourceRepoRoot ".git"))) {
    Write-Warning -Message "Source is not a git repository"
} else {
    Add-GitExclusion -RepoPath $sourceRepoRoot -Pattern "$GITHUB_DIR/$COPILOT_FILE_NAME" | Out-Null
    Add-GitExclusion -RepoPath $sourceRepoRoot -Pattern "$TOOLS_DIR/$SCRIPT_NAME" | Out-Null
}

Write-Host ""

# Step 2: Sync to targets
Write-Info -Message "Step 2: Syncing to target repositories..."
$results = New-SyncResult

foreach ($targetRepo in $TARGET_REPOS) {
    Write-Host ""
    Write-Info -Message "Processing: $targetRepo"
    
    # Check if target repo exists
    if (-not (Test-Path $targetRepo)) {
        Write-Warning -Message "Repository not found, skipping: $targetRepo"
        $results.Skipped++
        continue
    }
    
    # Check if source and target are the same
    if (Test-SamePath -Path1 $sourceRepoRoot -Path2 $targetRepo) {
        Write-Warning -Message "Source and target are the same, skipping self-sync"
        $results.Skipped++
        continue
    }
    
    # Create .github directory if needed
    $targetGithubDir = Join-Path $targetRepo $GITHUB_DIR
    if (-not (Test-Path $targetGithubDir)) {
        New-Item -ItemType Directory -Path $targetGithubDir -Force | Out-Null
        Write-Success -Message "Created $GITHUB_DIR directory"
    }
    
    # Check target version
    $targetFile = Join-Path $targetGithubDir $COPILOT_FILE_NAME
    $targetVersion = Get-CopilotVersion -FilePath $targetFile
    
    if ($targetVersion) {
        Write-Info -Message "Target version: v$targetVersion"
    } else {
        Write-Info -Message "Target version: None (will be treated as v0.0 - will sync)"
    }
    
    # Compare versions (null target version = always sync)
    $shouldUpdate = Compare-CopilotVersion -SourceVersion $sourceVersion -TargetVersion $targetVersion
    
    if ($shouldUpdate) {
        # Copy file only if version check passes
        try {
            Copy-Item -Path $sourceFile -Destination $targetFile -Force
            $targetHash = (Get-FileHash $targetFile -Algorithm MD5).Hash
            
            if ($targetHash -eq $sourceHash) {
                Write-Success -Message "Synced successfully (MD5 verified)"
                $results.Synced++
            } else {
                Write-Warning -Message "Synced but hash mismatch"
            }
        } catch {
            Write-Error -Message "Failed to copy: $_"
            continue
        }
    } else {
        Write-Warning -Message "Target version is same or newer, skipping sync"
        $results.Skipped++
    }
    
    # Always check and configure git (even if sync was skipped)
    # Check if file is tracked in git and remove if needed
    if (Test-GitTracked -RepoPath $targetRepo -File "$GITHUB_DIR/$COPILOT_FILE_NAME") {
        Write-Info -Message "File is tracked in git, removing from index..."
        if (Remove-FromGitIndex -RepoPath $targetRepo -File "$GITHUB_DIR/$COPILOT_FILE_NAME") {
            $results.Untracked++
        }
    }
    
    # Add exclusion for copilot instructions
    if (Add-GitExclusion -RepoPath $targetRepo -Pattern "$GITHUB_DIR/$COPILOT_FILE_NAME") {
        $results.Excluded++
    }
    
    # Verify ignored
    if (Test-GitIgnored -RepoPath $targetRepo -File "$GITHUB_DIR\$COPILOT_FILE_NAME") {
        $results.Verified++
    }
    
    # Sync the script itself
    Write-Host ""
    Write-Info -Message "Syncing script to target..."
    
    # Create tools directory if needed
    $targetToolsDir = Join-Path $targetRepo $TOOLS_DIR
    if (-not (Test-Path $targetToolsDir)) {
        New-Item -ItemType Directory -Path $targetToolsDir -Force | Out-Null
        Write-Success -Message "Created $TOOLS_DIR directory"
    }
    
    # Check target script version
    $targetScriptFile = Join-Path $targetToolsDir $SCRIPT_NAME
    $targetScriptVersion = Get-ScriptVersion -FilePath $targetScriptFile
    
    if ($targetScriptVersion) {
        Write-Info -Message "Target script version: v$targetScriptVersion"
    } else {
        Write-Info -Message "Target script version: None (will sync)"
    }
    
    # Compare script versions
    $shouldUpdateScript = Compare-CopilotVersion -SourceVersion $SCRIPT_VERSION -TargetVersion $targetScriptVersion
    
    if ($shouldUpdateScript) {
        try {
            Copy-Item -Path $scriptPath -Destination $targetScriptFile -Force
            $targetScriptHash = (Get-FileHash $targetScriptFile -Algorithm MD5).Hash
            
            if ($targetScriptHash -eq $scriptHash) {
                Write-Success -Message "Script synced successfully (MD5 verified)"
                $results.ScriptsSynced++
            } else {
                Write-Warning -Message "Script synced but hash mismatch"
            }
        } catch {
            Write-Error -Message "Failed to copy script: $_"
        }
    } else {
        Write-Info -Message "Target script version is same or newer, skipping"
    }
    
    # Check if script is tracked in git and remove if needed
    if (Test-GitTracked -RepoPath $targetRepo -File "$TOOLS_DIR/$SCRIPT_NAME") {
        Write-Info -Message "Script is tracked in git, removing from index..."
        Remove-FromGitIndex -RepoPath $targetRepo -File "$TOOLS_DIR/$SCRIPT_NAME" | Out-Null
    }
    
    # Add exclusion for script
    Add-GitExclusion -RepoPath $targetRepo -Pattern "$TOOLS_DIR/$SCRIPT_NAME" | Out-Null
}

# Summary
Write-SectionDivider -Title "Sync Summary:"
Write-Host "  Source File:        $sourceFile"
if ($sourceVersion) {
    Write-Host "  Source Version:     v$sourceVersion"
} else {
    Write-Host "  Source Version:     None"
}
Write-Host "  Script Version:     v$SCRIPT_VERSION"
Write-Host "  Target Repos:       $($TARGET_REPOS.Count)"
Write-Host "  Files Synced:       $($results.Synced)"
Write-Host "  Scripts Synced:     $($results.ScriptsSynced)"
Write-Host "  Files Skipped:      $($results.Skipped)"
Write-Host "  Files Untracked:    $($results.Untracked)"
Write-Host "  Exclusions Added:   $($results.Excluded)"
Write-Host "  Verified Ignored:   $($results.Verified)"
Write-Host ("═" * 55) -ForegroundColor Cyan

if ($results.Synced -gt 0) {
    Write-Host ""
    Write-Success -Message "Sync completed successfully!"
    exit 0
} elseif ($results.Skipped -eq $TARGET_REPOS.Count) {
    Write-Host ""
    Write-Info -Message "All targets are up-to-date or skipped."
    exit 0
} else {
    Write-Host ""
    Write-Warning -Message "Some operations failed. Review output above."
    exit 1
}
