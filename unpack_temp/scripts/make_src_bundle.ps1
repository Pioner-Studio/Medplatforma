<#
  make_bundle.ps1 — build a Markdown bundle for a specific module/topic.
  Usage examples:
    .\scripts\make_bundle.ps1 -Profile calendar
    .\scripts\make_bundle.ps1 -Profile finance -IncludeDocs
    .\scripts\make_bundle.ps1 -Profile patients -DocsProfile docs_common
#>

param(
  [Parameter(Mandatory=$true)]
  [string]$Profile,                  # name like: calendar | finance | patients | tooth | all
  [string]$ProfilesDir = ".\.profiles",
  [string]$OutDir      = ".\artifacts",
  [string]$OutputName  = "",         # if empty -> auto bundle_<profile>_<timestamp>.md
  [switch]$IncludeDocs,              # include docs_common.txt if present
  [string]$DocsProfile = "docs_common"
)

# Extension -> Markdown language for fenced code
$extMap = @{
  ".html" = "html"
  ".htm"  = "html"
  ".js"   = "javascript"
  ".css"  = "css"
  ".py"   = "python"
  ".json" = "json"
  ".md"   = "markdown"
}

function Resolve-ListFromProfile([string]$name) {
  $file = Join-Path $ProfilesDir ($name + ".txt")
  if (-not (Test-Path $file -PathType Leaf)) {
    throw "Profile file not found: $file"
  }
  $lines = Get-Content $file -Encoding UTF8 | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" -and -not $_.StartsWith("#") }
  return $lines
}

# Collect include/exclude patterns from main profile
$includes = @()
$excludes = @()
$lines = Resolve-ListFromProfile -name $Profile
foreach ($l in $lines) {
  if ($l.StartsWith("!")) { $excludes += $l.Substring(1) } else { $includes += $l }
}

# Optionally include docs from a docs profile (e.g., docs_common.txt)
if ($IncludeDocs -or ($DocsProfile -ne "" -and $DocsProfile -ne $Profile)) {
  try {
    $docLines = Resolve-ListFromProfile -name $DocsProfile
    foreach ($l in $docLines) {
      if ($l.StartsWith("!")) { $excludes += $l.Substring(1) } else { $includes += $l }
    }
  } catch { # ignore if docs profile not present
  }
}

# Helper: expand a single pattern into files
function Expand-Pattern([string]$pattern) {
  $results = @()
  # Normalize slashes
  $pat = $pattern -replace "/", "\"
  # If it's an existing file
  if (Test-Path $pat -PathType Leaf) {
    $results += (Get-Item $pat)
    return $results
  }
  # If it's an existing directory -> take all known types inside (recursive)
  if (Test-Path $pat -PathType Container) {
    $results += Get-ChildItem -Path $pat -Recurse -Force | Where-Object { -not $_.PSIsContainer -and $extMap.ContainsKey($_.Extension.ToLower()) }
    return $results
  }
  # Else treat as wildcard (with possible folders)
  $dir  = Split-Path $pat -Parent
  $mask = Split-Path $pat -Leaf
  if ($dir -eq "" -or -not (Test-Path $dir -PathType Container)) { $dir = "." }
  $results += Get-ChildItem -Path $dir -Filter $mask -Recurse -Force -ErrorAction SilentlyContinue |
              Where-Object { -not $_.PSIsContainer -and $extMap.ContainsKey($_.Extension.ToLower()) }
  return $results
}

# Expand includes
$all = @()
foreach ($p in $includes) { $all += Expand-Pattern $p }
# Apply excludes
if ($excludes.Count -gt 0) {
  $toExclude = @()
  foreach ($x in $excludes) { $toExclude += Expand-Pattern $x }
  $excludeSet = @{}
  foreach ($e in $toExclude) { $excludeSet[$e.FullName.ToLower()] = $true }
  $all = $all | Where-Object { -not $excludeSet.ContainsKey($_.FullName.ToLower()) }
}

# Unique + sort
$files = $all | Sort-Object FullName -Unique

# Prepare output
if (-not (Test-Path $OutDir -PathType Container)) { New-Item -ItemType Directory -Path $OutDir | Out-Null }
if ([string]::IsNullOrWhiteSpace($OutputName)) {
  $stamp = Get-Date -Format 'yyyyMMdd_HHmm'
  $OutputName = "bundle_$($Profile)_$stamp.md"
}
$outFile = Join-Path $OutDir $OutputName

$ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
'<!-- GENERATED: ' + $ts + ' -->'            | Set-Content -Path $outFile -Encoding utf8
'# MedPlatforma Bundle'                       | Add-Content -Path $outFile -Encoding utf8
'Topic: ' + $Profile                          | Add-Content -Path $outFile -Encoding utf8
'Generated: ' + $ts                           | Add-Content -Path $outFile -Encoding utf8
'Files: ' + $files.Count                      | Add-Content -Path $outFile -Encoding utf8
''                                            | Add-Content -Path $outFile -Encoding utf8
'## Included files'                           | Add-Content -Path $outFile -Encoding utf8
foreach ($f in $files) {
  $rel = Resolve-Path -Relative $f.FullName
  '- ' + $rel + '  (' + [math]::Round($f.Length/1kb,2) + ' KB)' | Add-Content -Path $outFile -Encoding utf8
}
'' | Add-Content -Path $outFile -Encoding utf8
'---' | Add-Content -Path $outFile -Encoding utf8

# Emit with ~~~ fenced blocks
foreach ($f in $files) {
  $ext  = $f.Extension.ToLower()
  $lang = if ($extMap.ContainsKey($ext)) { $extMap[$ext] } else { "" }
  $rel  = Resolve-Path -Relative $f.FullName

  '' | Add-Content -Path $outFile -Encoding utf8
  '=== BEGIN FILE: ' + $rel + ' ===' | Add-Content -Path $outFile -Encoding utf8
  '' | Add-Content -Path $outFile -Encoding utf8
  '~~~' + $lang | Add-Content -Path $outFile -Encoding utf8
  Get-Content -Path $f.FullName -Encoding utf8 | Add-Content -Path $outFile -Encoding utf8
  '~~~' | Add-Content -Path $outFile -Encoding utf8
  '' | Add-Content -Path $outFile -Encoding utf8
  '=== END FILE: ' + $rel + ' ===' | Add-Content -Path $outFile -Encoding utf8
}

Write-Host ('DONE -> ' + $outFile)
