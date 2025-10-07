param(
  [string]$Root      = ".",
  [string]$OutDir    = ".\artifacts",
  [string]$OutName   = "PROJECT_SNAPSHOT.md"
)

function Ensure-OutFile {
  param([string]$OutDir, [string]$OutName)
  if (-not (Test-Path $OutDir -PathType Container)) { New-Item -ItemType Directory -Path $OutDir | Out-Null }
  $outFile = Join-Path $OutDir $OutName
  "" | Set-Content -Path $outFile -Encoding utf8
  return $outFile
}

function Add-SectionText {
  param([string]$OutFile,[string]$Title,[string[]]$Lines)
  "# $Title" | Add-Content -Path $OutFile -Encoding utf8
  "~~~text"  | Add-Content -Path $OutFile -Encoding utf8
  if ($Lines) { $Lines | Add-Content -Path $OutFile -Encoding utf8 }
  "~~~"      | Add-Content -Path $OutFile -Encoding utf8
  Add-Content -Path $OutFile "`n---`n" -Encoding utf8
}

$OUT = Ensure-OutFile -OutDir $OutDir -OutName $OutName
$ts  = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
"<!-- GENERATED: $ts -->" | Add-Content -Path $OUT -Encoding utf8
Add-Content -Path $OUT "# Project snapshot" -Encoding utf8
Add-Content -Path $OUT "Root: $Root" -Encoding utf8
Add-Content -Path $OUT "" -Encoding utf8

# 1) Tree (ASCII)
$tree = cmd /c "chcp 65001>nul & tree /F /A $Root"
Add-SectionText -OutFile $OUT -Title "Directory tree" -Lines $tree

# 2) Files list (path, size KB, last write)
$files = Get-ChildItem -Path $Root -Recurse -Force | Where-Object { -not $_.PSIsContainer } | Sort-Object FullName
$lines = @()
foreach ($f in $files) {
  try {
    $rel = Resolve-Path -Relative $f.FullName
  } catch {
    $rel = $f.FullName
  }
  $kb = [math]::Round($f.Length/1kb,2)
  $lines += "{0}    {1} KB    {2}" -f $rel, $kb, $f.LastWriteTime.ToString("yyyy-MM-dd HH:mm")
}
Add-SectionText -OutFile $OUT -Title "Files list" -Lines $lines

# 3) Flask routes (app/blueprint/add_url_rule)
$patterns = @('^\s*@app\.route\(','^\s*@[\w_]+\.route\(','\.add_url_rule\(')
$routesRaw = Select-String -Path (Join-Path $Root "**\*.py") -Pattern $patterns -AllMatches -ErrorAction SilentlyContinue |
  Sort-Object Path, LineNumber
$routesLines = @()
foreach ($m in $routesRaw) {
  try { $rel = Resolve-Path -Relative $m.Path } catch { $rel = $m.Path }
  $routesLines += "{0}:{1}: {2}" -f $rel, $m.LineNumber, $m.Line.Trim()
}
Add-SectionText -OutFile $OUT -Title "Flask routes (flat list)" -Lines $routesLines

# 3b) Flask routes grouped by file
$group = $routesRaw | Group-Object -Property Path
$grpLines = @()
foreach ($g in $group) {
  try { $rel = Resolve-Path -Relative $g.Name } catch { $rel = $g.Name }
  $grpLines += ">>> " + $rel
  foreach ($m in ($g.Group | Sort-Object LineNumber)) {
    $grpLines += ("  L{0}: {1}" -f $m.LineNumber, $m.Line.Trim())
  }
  $grpLines += ""
}
Add-SectionText -OutFile $OUT -Title "Flask routes (grouped by file)" -Lines $grpLines

# 4) Templates by folder (templates/*.html)
$tpls = Get-ChildItem -Path (Join-Path $Root "templates") -Recurse -Filter *.html -ErrorAction SilentlyContinue |
  Sort-Object DirectoryName, Name
$tplLines = @()
$curr = ""
foreach ($t in $tpls) {
  try { $rel = Resolve-Path -Relative $t.FullName } catch { $rel = $t.FullName }
  $dir = Split-Path $rel -Parent
  if ($dir -ne $curr) { $tplLines += ""; $tplLines += ">>> " + $dir; $curr = $dir }
  $tplLines += ("  - {0}  ({1} KB)" -f (Split-Path $rel -Leaf), [math]::Round($t.Length/1kb,2))
}
if ($tplLines.Count -eq 0) { $tplLines = @("No templates found.") }
Add-SectionText -OutFile $OUT -Title "Templates (*.html) grouped by folder" -Lines $tplLines

# 5) render_template usage (which templates are referenced in .py)
$rtRaw = Select-String -Path (Join-Path $Root "**\*.py") -Pattern 'render_template\(\s*["'']([^"'']+)["'']' -AllMatches -ErrorAction SilentlyContinue |
  Sort-Object Path, LineNumber
$rtLines = @()
foreach ($m in $rtRaw) {
  try { $rel = Resolve-Path -Relative $m.Path } catch { $rel = $m.Path }
  $tpl = $m.Matches.Groups[1].Value
  $rtLines += "{0}:{1}: render_template('{2}')" -f $rel, $m.LineNumber, $tpl
}
if ($rtLines.Count -eq 0) { $rtLines = @("No render_template() calls found.") }
Add-SectionText -OutFile $OUT -Title "render_template() references in Python" -Lines $rtLines

# 6) Seed/fixtures folders overview
$seedDirs = Get-ChildItem -Path $Root -Recurse -Directory -Force -ErrorAction SilentlyContinue |
  Where-Object { $_.Name -match '(?i)seed|fixture' } | Sort-Object FullName
$seedLines = @()
foreach ($d in $seedDirs) {
  try { $relDir = Resolve-Path -Relative $d.FullName } catch { $relDir = $d.FullName }
  $seedLines += ">>> " + $relDir
  $seedFiles = Get-ChildItem -Path $d.FullName -Recurse -Force -ErrorAction SilentlyContinue | Where-Object { -not $_.PSIsContainer }
  foreach ($sf in $seedFiles) {
    try { $rel = Resolve-Path -Relative $sf.FullName } catch { $rel = $sf.FullName }
    $seedLines += ("  - {0}  ({1} KB)" -f $rel, [math]::Round($sf.Length/1kb,2))
  }
  $seedLines += ""
}
if ($seedLines.Count -eq 0) { $seedLines = @("No seed/fixture directories found.") }
Add-SectionText -OutFile $OUT -Title "Seeds / Fixtures overview" -Lines $seedLines

Write-Host ("DONE -> " + $OUT)
