param(
  [string]$Slug = "",
  [string]$Title = ""
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$postsDir = Join-Path $root "data\posts"
$script = Join-Path $root "scripts\new-post.py"

Set-Location $root

function Is-InRebase {
  try { $gitDir = git rev-parse --git-dir } catch { return $false }
  if (-not $gitDir) { return $false }
  return (Test-Path (Join-Path $gitDir "rebase-merge")) -or
         (Test-Path (Join-Path $gitDir "rebase-apply"))
}

function Abort-Rebase {
  if (Is-InRebase) {
    try { git rebase --abort } catch { }
    Write-Host "  [FIX] Rebase aborted."
  }
}

function Invoke-GitPull {
  $env:GIT_EDITOR = "true"
  try { git pull --rebase } catch { }
  $code = $LASTEXITCODE
  $env:GIT_EDITOR = $null
  return $code
}

function Test-PushRejected {
  # rejected = remote has new commits (exit code non-zero + stderr contains specific hints)
  $output = git push 2>&1
  $exitCode = $LASTEXITCODE
  if ($exitCode -eq 0) { return @{ Success = $true; Rejected = $false } }

  $stderr = ($output | Out-String).ToLower()
  $isRejected = $stderr -match "rejected|fetch first|updates were rejected"
  return @{ Success = $false; Rejected = $isRejected }
}

# --- Step 1: Pull ---
Write-Host "[1/4] Pulling latest from GitHub..."
if ((Invoke-GitPull) -ne 0) {
  Write-Host "  [WARN] Pull failed, aborting rebase..."
  Abort-Rebase
  Write-Host "  Retrying pull..."
  if ((Invoke-GitPull) -ne 0) {
    Write-Host "  [ERROR] Pull failed again. Please resolve manually."
    Abort-Rebase
    exit 1
  }
}

# --- Step 2: Create note ---
Write-Host "[2/4] Creating note template..."
if ($Slug -eq "") {
  python $script
} elseif ($Title -eq "") {
  python $script $Slug
} else {
  python $script $Slug $Title
}

$latest = Get-ChildItem $postsDir -Filter "*.md" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $latest) { Write-Host "  [ERROR] No note file found"; exit 1 }

# --- Step 3: Edit ---
Write-Host "[3/4] Opening $($latest.Name) in Notepad..."
Write-Host "      Close Notepad when done editing."
notepad $latest.FullName

while ($true) {
  $procs = Get-Process -Name "notepad" -ErrorAction SilentlyContinue
  if (-not $procs) { break }
  Start-Sleep -Seconds 1
}

# --- Step 4: Commit & Push ---
$commitMsg = Read-Host "`n[4/4] Commit message (press Enter for 'post-new')"
if ($commitMsg -eq "") { $commitMsg = "post-new" }

Write-Host "`nCommitting and pushing..."
git add -A
git commit --no-edit -m $commitMsg
if ($LASTEXITCODE -ne 0) {
  Write-Host "`n[DONE] Nothing to commit."
  return
}

# Push with auto-retry on rejection
$maxRetries = 3
for ($i = 1; $i -le $maxRetries; $i++) {
  $result = Test-PushRejected
  if ($result.Success) {
    Write-Host "`n[DONE] Pushed successfully. Deploying via Vercel (1-2 min)"
    return
  }

  if (-not $result.Rejected) {
    # Not a rejection (network error, permission denied, etc.) - no point retrying
    Write-Host "[ERROR] Push failed (not a rejection). Check network and permissions."
    Write-Host "  Run 'git push' manually to see the full error."
    exit 1
  }

  if ($i -ge $maxRetries) { break }

  Write-Host "[WARN] Push rejected (remote has new commits). Retry $i/$maxRetries..."

  # Save uncommitted changes if any
  $stashed = $false
  $porcelain = git status --porcelain
  if ($porcelain) {
    git stash push -m "auto-stash before pull-retry"
    $stashed = $LASTEXITCODE -eq 0
  }

  # Pull with rebase
  if ((Invoke-GitPull) -ne 0) {
    Write-Host "[ERROR] Rebase failed during retry."
    Abort-Rebase
    if ($stashed) {
      Write-Host "  Attempting to restore stashed changes..."
      try { git stash pop } catch { }
      if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Stash pop also failed. Your changes are in stash."
        Write-Host "  Run 'git stash list' then 'git stash pop' after resolving."
      }
    }
    exit 1
  }

  # Restore stashed changes
  if ($stashed) {
    try { git stash pop } catch { }
    if ($LASTEXITCODE -ne 0) {
      Write-Host "[WARN] Stash pop has conflicts. Your commit is still local."
      Write-Host "  Conflicts are in working tree. Resolve them, then run 'git push'."
      Write-Host "  Stash entry preserved: run 'git stash list' to check."
    }
  }
}

Write-Host "[ERROR] Push rejected $maxRetries times. Remote may be updating rapidly."
Write-Host "  Try: git pull --rebase && git push"
Abort-Rebase
exit 1
