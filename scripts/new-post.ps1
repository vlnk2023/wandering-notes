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

function Invoke-GitCommand {
  param(
    [Parameter(Mandatory = $true)]
    [string[]]$Arguments,
    [switch]$PrintOutput,
    [hashtable]$EnvironmentOverrides
  )

  $previousErrorActionPreference = $ErrorActionPreference
  $previousEnv = @{}

  try {
    if ($EnvironmentOverrides) {
      foreach ($key in $EnvironmentOverrides.Keys) {
        $previousEnv[$key] = [Environment]::GetEnvironmentVariable($key)
        [Environment]::SetEnvironmentVariable($key, $EnvironmentOverrides[$key])
      }
    }

    # Windows PowerShell 5.1 can turn native stderr into a terminating error
    # when ErrorActionPreference is Stop. Capture it without changing arguments.
    $ErrorActionPreference = "Continue"
    $output = & git @Arguments 2>&1
    $exitCode = $LASTEXITCODE
    $combined = (($output | ForEach-Object { $_.ToString() }) | Out-String).Trim()

    if ($PrintOutput -and $combined) {
      Write-Host $combined
    }

    return @{
      Success = ($exitCode -eq 0)
      ExitCode = $exitCode
      Output = $combined
    }
  }
  finally {
    $ErrorActionPreference = $previousErrorActionPreference
    if ($EnvironmentOverrides) {
      foreach ($key in $EnvironmentOverrides.Keys) {
        [Environment]::SetEnvironmentVariable($key, $previousEnv[$key])
      }
    }

  }
}

function Invoke-GitPull {
  return Invoke-GitCommand -Arguments @("pull", "--rebase", "--autostash") -EnvironmentOverrides @{ GIT_EDITOR = "true" }
}

function Test-PushRejected {
  $pushResult = Invoke-GitCommand -Arguments @("push") -PrintOutput
  if ($pushResult.Success) {
    return @{ Success = $true; Rejected = $false; Output = $pushResult.Output }
  }

  $lowerOutput = $pushResult.Output.ToLower()
  $isRejected = $lowerOutput -match "rejected|fetch first|updates were rejected"
  return @{ Success = $false; Rejected = $isRejected; Output = $pushResult.Output; ExitCode = $pushResult.ExitCode }
}

# --- Step 1: Pull ---
Write-Host "[1/4] Pulling latest from GitHub..."
$pullResult = Invoke-GitPull
if (-not $pullResult.Success) {
  if (Is-InRebase) {
    Write-Host "  [WARN] Pull failed during an in-progress rebase. Aborting and retrying once..."
    Abort-Rebase
    $pullResult = Invoke-GitPull
  }

  if (-not $pullResult.Success) {
    Write-Host "  [ERROR] git pull --rebase failed."
    if ($pullResult.Output) {
      Write-Host $pullResult.Output
    }
    Write-Host "  Please resolve manually, then rerun the script."
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
git commit -m $commitMsg
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
    Write-Host "[ERROR] Push failed (not a rejection). Check network and permissions."
    if ($result.Output) {
      Write-Host $result.Output
    }
    Write-Host "  Run 'git push' manually to see the full error."
    exit 1
  }

  if ($i -ge $maxRetries) { break }

  Write-Host "[WARN] Push rejected (remote has new commits). Retry $i/$maxRetries..."

  $pullResult = Invoke-GitPull
  if (-not $pullResult.Success) {
    Write-Host "[ERROR] Rebase failed during retry."
    if ($pullResult.Output) {
      Write-Host $pullResult.Output
    }
    Abort-Rebase
    exit 1
  }
}

Write-Host "[ERROR] Push rejected $maxRetries times. Remote may be updating rapidly."
Write-Host "  Try: git pull --rebase && git push"
Abort-Rebase
exit 1
