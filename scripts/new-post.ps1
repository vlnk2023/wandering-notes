param(
  [string]$Slug = "",
  [string]$Title = ""
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$postsDir = Join-Path $root "data\posts"
$script = Join-Path $root "scripts\new-post.py"

Set-Location $root

Write-Host "[1/4] Pulling latest from GitHub..."
git pull --rebase
if ($LASTEXITCODE -ne 0) {
  Write-Host "  [WARN] git pull failed, continuing anyway..."
}

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

Write-Host "[3/4] Opening $($latest.Name) in Notepad..."
Write-Host "      Close Notepad when done editing."
notepad $latest.FullName

while ($true) {
  $procs = Get-Process -Name "notepad" -ErrorAction SilentlyContinue
  if (-not $procs) { break }
  Start-Sleep -Seconds 1
}

$commitMsg = Read-Host "`n[4/4] Commit message (press Enter for 'post-new')"
if ($commitMsg -eq "") { $commitMsg = "post-new" }

Write-Host "`nCommitting and pushing..."
git add -A
git commit -m $commitMsg
if ($LASTEXITCODE -eq 0) {
  git push
  Write-Host "`n[DONE] Deploying via Vercel (1-2 min)"
} else {
  Write-Host "`n[DONE] Nothing to commit. Vercel auto-deploys on push."
}
