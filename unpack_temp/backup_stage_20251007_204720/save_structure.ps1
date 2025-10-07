param(
  [string]$ProjectRoot = '.',
  [string]$OutRoot = 'D:\Projects'
)

$ErrorActionPreference = 'Stop'

function Ensure-Folder([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path)) {
    New-Item -ItemType Directory -Path $Path | Out-Null
  }
}

function Write-Section([string]$Dest, [string]$Title) {
  "`n=== $Title ===" | Out-File -FilePath $Dest -Append -Encoding utf8
}

function Dump-Tree([string]$Root, [string]$Header, [string]$Dest) {
  Write-Section -Dest $Dest -Title $Header

  if (-not (Test-Path -LiteralPath $Root)) {
    "$Root (missing)" | Out-File $Dest -Append -Encoding utf8
    return
  }

  $base = (Resolve-Path -LiteralPath $Root).Path

  Get-ChildItem -LiteralPath $Root -Recurse | Sort-Object FullName | ForEach-Object {
    $rel = $_.FullName.Substring($base.Length).TrimStart('\','/')
    if ([string]::IsNullOrWhiteSpace($rel)) { $rel = '.' }
    if ($_.PSIsContainer) {
      "[DIR] $rel" | Out-File $Dest -Append -Encoding utf8
    } else {
      "  - $rel" | Out-File $Dest -Append -Encoding utf8
    }
  }
}

function Dump-FilesByPattern([string]$Root, [string]$Header, [string]$Dest, [string[]]$Patterns) {
  Write-Section -Dest $Dest -Title $Header

  if (-not (Test-Path -LiteralPath $Root)) {
    "$Root (missing)" | Out-File $Dest -Append -Encoding utf8
    return
  }

  $base = (Resolve-Path -LiteralPath $Root).Path
  $found = @()

  foreach ($pat in $Patterns) {
    $found += Get-ChildItem -LiteralPath $Root -Recurse -File -Filter $pat -ErrorAction SilentlyContinue
  }

  if (-not $found -or $found.Count -eq 0) {
    'none' | Out-File $Dest -Append -Encoding utf8
    return
  }

  $found | Sort-Object FullName -Unique | ForEach-Object {
    $rel = $_.FullName.Substring($base.Length).TrimStart('\','/')
    "  - $rel" | Out-File $Dest -Append -Encoding utf8
  }
}

# ---- entry point ----
$stamp = Get-Date -Format 'yyyy-MM-dd_HH-mm'
Ensure-Folder $OutRoot
$dest = Join-Path $OutRoot "structure_$stamp.txt"

# 0) Entire project tree
Dump-Tree -Root $ProjectRoot -Header 'PROJECT TREE (all)' -Dest $dest

# 1) templates/
Dump-Tree -Root (Join-Path $ProjectRoot 'templates') -Header 'templates' -Dest $dest

# 2) routes/ (folder)
Dump-Tree -Root (Join-Path $ProjectRoot 'routes') -Header 'routes (folder)' -Dest $dest

# 3) All Python files in project
Dump-FilesByPattern -Root $ProjectRoot -Header 'PYTHON (*.py) - project' -Dest $dest -Patterns @('*.py')

# 4) Root-level route files only
Write-Section -Dest $dest -Title 'routes (project root only)'
$rootResolved = (Resolve-Path -LiteralPath $ProjectRoot).Path
$patterns = @('main.py','app.py','wsgi.py','routes_*.py')
$foundRoot = @()
foreach ($pat in $patterns) {
  $foundRoot += Get-ChildItem -LiteralPath $ProjectRoot -File -Filter $pat -ErrorAction SilentlyContinue
}
if (-not $foundRoot -or $foundRoot.Count -eq 0) {
  'none' | Out-File $dest -Append -Encoding utf8
} else {
  $foundRoot | Sort-Object FullName -Unique | ForEach-Object {
    $rel = $_.FullName.Substring($rootResolved.Length).TrimStart('\','/')
    "  - $rel" | Out-File $dest -Append -Encoding utf8
  }
}

Write-Host "Saved to $dest"
