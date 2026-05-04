param(
  [string]$Slug = "",
  [string]$Title = ""
)

$root = Split-Path -Parent $PSScriptRoot
$postsDir = Join-Path $root "data\posts"
$script = Join-Path $root "scripts\new-post.py"

# 1) 新建笔记模板
if ($Slug -eq "") {
  python $script
} elseif ($Title -eq "") {
  python $script $Slug
} else {
  python $script $Slug $Title
}

# 获取刚创建的文件
$latest = Get-ChildItem $postsDir -Filter "*.md" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $latest) { Write-Host "❌ 没找到新建的笔记"; exit 1 }

Write-Host "`n📝 打开编辑: $($latest.Name)"
notepad $latest.FullName

# 等待用户关掉记事本
Write-Host "`n⏳ 关掉记事本后继续..." -NoNewline
while ($true) {
  $procs = Get-Process -Name "notepad" -ErrorAction SilentlyContinue | Where-Object { $_.MainModule.FileName -eq "notepad.exe" }
  if (-not $procs) { break }
  Start-Sleep -Seconds 1
}
Write-Host " 继续"

# 2) 提示输入 commit 信息
$commitMsg = Read-Host "`nCommit 信息 (默认: post-new)"
if ($commitMsg -eq "") { $commitMsg = "post-new" }

# 3) git 操作
Write-Host "`n📦 Git 提交并推送..."
Set-Location $root
git pull --rebase
if (-not $?) { Write-Host "⚠️  pull 有冲突，尝试 --force 前请确认"; exit 1 }
git add -A
git commit -m $commitMsg
git push

Write-Host "`n✅ 完成！等待 Vercel 自动部署 (~1-2分钟)"
