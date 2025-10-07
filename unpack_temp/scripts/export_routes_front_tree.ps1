param(
  [string]$OutDir  = ".\artifacts",
  [string]$OutName = "ROUTES_METHODS_FRONT_AND_TREE.md"
)

# Исключаем только шум
$ExcludeDirs  = @(".\.git",".\.venv",".\artifacts",".\node_modules",
                  ".\__pycache__", ".\dist",".\build",".\logs",".\WAN",
                  ".\.pytest_cache",".\.mypy_cache",".\.idea",".\.vscode")
$ExcludeGlobs = @("*\__pycache__\*","*\site-packages\*","*.map","*.min.*","*.log")

# Подготовка выхода
if (-not (Test-Path $OutDir -PathType Container)) { New-Item -ItemType Directory -Path $OutDir | Out-Null }
$outFile = Join-Path $OutDir $OutName
"" | Set-Content -Path $outFile -Encoding utf8
$ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
"<!-- GENERATED: $ts -->" | Add-Content $outFile -Encoding utf8
"# Routes + Front calls + Directory tree" | Add-Content $outFile -Encoding utf8
"" | Add-Content $outFile -Encoding utf8

function Add-Section([string]$title) { "# $title" | Add-Content $outFile -Encoding utf8; "~~~text" | Add-Content $outFile -Encoding utf8 }
function End-Section() { "~~~" | Add-Content $outFile -Encoding utf8; Add-Content $outFile "`n---`n" -Encoding utf8 }

# Собираем все файлы проекта (минус исключения)
$rootFull = (Resolve-Path ".").Path
$allFiles = Get-ChildItem -Path $rootFull -Recurse -Force -File -ErrorAction SilentlyContinue
$ExcFull = @(); foreach ($d in $ExcludeDirs) { if (Test-Path $d -PathType Container) { $ExcFull += (Resolve-Path $d).Path } }
$allFiles = $allFiles | Where-Object {
  $p=$_.FullName; -not ($ExcFull | Where-Object { $p.StartsWith($_,[System.StringComparison]::OrdinalIgnoreCase) })
}
foreach ($g in $ExcludeGlobs) { $allFiles = $allFiles | Where-Object { $_.FullName -notlike $g } }
$allFiles = $allFiles | Sort-Object FullName -Unique

# ========== 0) DIRECTORY TREE (filtered) ==========
Add-Section "Directory tree (filtered)"
$dirs = $allFiles | ForEach-Object { $_.DirectoryName } | Sort-Object -Unique
foreach ($dir in $dirs) {
  try { $relDir = Resolve-Path -Relative $dir } catch { $relDir = $dir }
  ("{0}" -f $relDir) | Add-Content $outFile -Encoding utf8
  $filesIn = $allFiles | Where-Object { $_.DirectoryName -eq $dir } | Sort-Object Name
  foreach ($f in $filesIn) {
    ("  - {0}  ({1} KB)" -f $f.Name, [math]::Round($f.Length/1kb,2)) | Add-Content $outFile -Encoding utf8
  }
  "" | Add-Content $outFile -Encoding utf8
}
End-Section

# ========== 1) ROUTES WITH METHODS ==========
Add-Section "Flask routes with methods"
$pyFiles = $allFiles | Where-Object { $_.Extension -eq ".py" } | Sort-Object FullName

$rxVerb  = [regex]'(?m)@(?<obj>[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)\.(?<verb>get|post|put|patch|delete|options|head)\(\s*["''](?<path>[^"'']+)["'']'
$rxRoute = [regex]'(?s)@(?<obj>[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)\.route\(\s*["''](?<path>[^"'']+)["'']\s*(?:,\s*methods\s*=\s*(?<methods>\[[^\]]+\]|\([^)]+\)|\{[^}]+\}))?'
$rxAdd   = [regex]'(?s)\.add_url_rule\(\s*["''](?<path>[^"'']+)["'']\s*(?:,\s*methods\s*=\s*(?<methods>\[[^\]]+\]|\([^)]+\)|\{[^}]+\}))?'

function Get-LineNumber([string]$text, [int]$index) { if ($index -lt 0) { return 1 }; (($text.Substring(0,[Math]::Min($index,$text.Length))) -split "`n").Count }
function Parse-Methods([string]$raw) {
  if (-not $raw) { return @("GET") }
  $vals = @([regex]::Matches($raw,'(?i)GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD') | ForEach-Object { $_.Value.ToUpper() } | Sort-Object -Unique)
  if ($vals.Count -eq 0) { return @("GET") } else { return $vals }
}

$routes = New-Object System.Collections.Generic.List[string]
$summary = [ordered]@{ GET=0; POST=0; PUT=0; PATCH=0; DELETE=0; OPTIONS=0; HEAD=0 }

foreach ($f in $pyFiles) {
  $txt = Get-Content $f.FullName -Raw -ErrorAction SilentlyContinue
  if (-not $txt) { continue }
  $rel = (Resolve-Path -Relative $f.FullName)

  foreach ($m in $rxVerb.Matches($txt)) {
    $ln   = Get-LineNumber $txt $m.Index
    $verb = $m.Groups['verb'].Value.ToUpper()
    $path = $m.Groups['path'].Value
    ("{0}:L{1}: {2} {3}" -f $rel,$ln,$verb,$path) | Add-Content $outFile -Encoding utf8
    if ($summary.Contains($verb)) { $summary[$verb]++ } else { $summary[$verb]=1 }
  }
  foreach ($m in $rxRoute.Matches($txt)) {
    $ln   = Get-LineNumber $txt $m.Index
    $path = $m.Groups['path'].Value
    foreach ($method in (Parse-Methods $m.Groups['methods'].Value)) {
      ("{0}:L{1}: {2} {3}" -f $rel,$ln,$method,$path) | Add-Content $outFile -Encoding utf8
      if ($summary.Contains($method)) { $summary[$method]++ } else { $summary[$method]=1 }
    }
  }
  foreach ($m in $rxAdd.Matches($txt)) {
    $ln   = Get-LineNumber $txt $m.Index
    $path = $m.Groups['path'].Value
    foreach ($method in (Parse-Methods $m.Groups['methods'].Value)) {
      ("{0}:L{1}: {2} {3}" -f $rel,$ln,$method,$path) | Add-Content $outFile -Encoding utf8
      if ($summary.Contains($method)) { $summary[$method]++ } else { $summary[$method]=1 }
    }
  }
}
End-Section

# Сводка по методам
Add-Section "Routes summary by method"
foreach ($k in $summary.Keys) { ("{0}: {1}" -f $k, $summary[$k]) | Add-Content $outFile -Encoding utf8 }
End-Section

# ========== 2) TEMPLATES ==========
Add-Section "Templates grouped by folder"
$tplFiles = $allFiles | Where-Object { $_.Extension -eq ".html" -and $_.FullName -like "*\templates\*" } | Sort-Object DirectoryName, Name
if ($tplFiles) {
  $curr = ""
  foreach ($t in $tplFiles) {
    $rel = (Resolve-Path -Relative $t.FullName)
    $dir = Split-Path $rel -Parent
    if ($dir -ne $curr) { "" | Add-Content $outFile; ">>> $dir" | Add-Content $outFile; $curr = $dir }
    ("  - {0}  ({1} KB)" -f (Split-Path $rel -Leaf), [math]::Round($t.Length/1kb,2)) | Add-Content $outFile
  }
} else { "No templates found." | Add-Content $outFile }
End-Section

# ========== 3) FRONTEND API CALLS ==========
Add-Section "Frontend API calls (fetch/axios/jQuery)"
$webFiles = @()
if (Test-Path .\templates) { $webFiles += Get-ChildItem .\templates -Recurse -Filter *.html -File -ErrorAction SilentlyContinue }
if (Test-Path .\static\js) { $webFiles += Get-ChildItem .\static\js -Recurse -Filter *.js   -File -ErrorAction SilentlyContinue }

$rxFetch = [regex]'(?i)fetch\(\s*["''](?<url>[^"'']+)["''](?:\s*,\s*\{[^}]*\bmethod\s*:\s*["''](?<method>GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD)["''])?'
$rxAxios = [regex]'(?i)axios\.(?<verb>get|post|put|patch|delete|options|head)\(\s*["''](?<url>[^"'']+)["'']'
$rxAjaxU = [regex]'(?is)\$\.ajax\(\s*\{[^}]*\burl\s*:\s*["''](?<url>[^"'']+)["'']'
$rxAjaxT = [regex]'(?i)\btype\s*:\s*["''](?<type>GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD)["'']'

foreach ($f in ($webFiles | Sort-Object FullName)) {
  $text = Get-Content $f.FullName -Raw -ErrorAction SilentlyContinue
  if (-not $text) { continue }
  $rel = (Resolve-Path -Relative $f.FullName)

  foreach ($m in $rxFetch.Matches($text)) {
    $ln = ($text.Substring(0,[Math]::Min($m.Index,$text.Length)) -split "`n").Count
    $method = if ($m.Groups['method'].Success) { $m.Groups['method'].Value.ToUpper() } else { "GET" }
    ("{0}:L{1}: {2} {3}" -f $rel,$ln,$method,$m.Groups['url'].Value) | Add-Content $outFile -Encoding utf8
  }
  foreach ($m in $rxAxios.Matches($text)) {
    $ln = ($text.Substring(0,[Math]::Min($m.Index,$text.Length)) -split "`n").Count
    $method = $m.Groups['verb'].Value.ToUpper()
    ("{0}:L{1}: {2} {3}" -f $rel,$ln,$method,$m.Groups['url'].Value) | Add-Content $outFile -Encoding utf8
  }
  foreach ($m in $rxAjaxU.Matches($text)) {
    $ln = ($text.Substring(0,[Math]::Min($m.Index,$text.Length)) -split "`n").Count
    $win = $text.Substring($m.Index, [Math]::Min(500, $text.Length - $m.Index))
    $typeMatch = $rxAjaxT.Match($win)
    $method = if ($typeMatch.Success) { $typeMatch.Groups['type'].Value.ToUpper() } else { "GET" }
    ("{0}:L{1}: {2} {3}" -f $rel,$ln,$method,$m.Groups['url'].Value) | Add-Content $outFile -Encoding utf8
  }
}
End-Section

Write-Host ("DONE -> " + $outFile)
