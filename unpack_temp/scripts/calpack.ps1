param(
  [string]$Calendar = ".\templates\calendar.html",
  [string]$OutDir   = ".\artifacts",
  [string]$Snapshot = ".\artifacts\ROUTES_METHODS_FRONT_AND_TREE.md"
)

if (-not (Test-Path $Calendar -PathType Leaf)) { Write-Error ("Файл не найден: " + $Calendar); exit 1 }
if (-not (Test-Path $OutDir -PathType Container)) { New-Item -ItemType Directory -Path $OutDir | Out-Null }

# --- 0) Подготовка путей
$txt = Join-Path $OutDir "calendar.html.txt"
$md  = Join-Path $OutDir "calendar_full.md"
$copy= Join-Path $OutDir "calendar.html"
$rep = Join-Path $OutDir "CALENDAR_REPORT.md"

# --- 1) Экспорт исходника (TXT/MD + копия)
Get-Content -Path $Calendar -Raw | Set-Content -Path $txt -Encoding UTF8
'```html' | Set-Content -Path $md -Encoding UTF8
Get-Content -Path $Calendar -Raw | Add-Content -Path $md -Encoding UTF8
'```' | Add-Content -Path $md -Encoding UTF8
Copy-Item -Path $Calendar -Destination $copy -Force -ErrorAction SilentlyContinue

# --- 2) Чтение исходника для анализа
$text = Get-Content -Path $Calendar -Raw
$lines = $text -split "`n"

# --- 3) Поиск фронтовых вызовов API
$rxFetch = [regex]'(?i)fetch\(\s*["''](?<url>[^"'']+)["''](?:\s*,\s*\{[^}]*\bmethod\s*:\s*["''](?<method>GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD)["''])?'
$rxAxios = [regex]'(?i)axios\.(?<verb>get|post|put|patch|delete|options|head)\(\s*["''](?<url>[^"'']+)["'']'
$rxAjaxU = [regex]'(?is)\$\.ajax\(\s*\{[^}]*\burl\s*:\s*["''](?<url>[^"'']+)["'']'
$rxAjaxT = [regex]'(?i)\btype\s*:\s*["''](?<type>GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD)["'']'

$apiCalls = New-Object System.Collections.Generic.List[object]
function Add-ApiCall([string]$meth,[string]$url,[int]$ln) {
  $obj = [PSCustomObject]@{ method=$meth; url=$url; line=$ln }
  $script:apiCalls.Add($obj) | Out-Null
}
# fetch
foreach ($m in $rxFetch.Matches($text)) {
  $ln = ($text.Substring(0,[Math]::Min($m.Index,$text.Length)) -split "`n").Count
  $method = if ($m.Groups['method'].Success) { $m.Groups['method'].Value.ToUpper() } else { "GET" }
  Add-ApiCall $method $m.Groups['url'].Value $ln
}
# axios
foreach ($m in $rxAxios.Matches($text)) {
  $ln = ($text.Substring(0,[Math]::Min($m.Index,$text.Length)) -split "`n").Count
  Add-ApiCall ($m.Groups['verb'].Value.ToUpper()) $m.Groups['url'].Value $ln
}
# $.ajax
foreach ($m in $rxAjaxU.Matches($text)) {
  $ln = ($text.Substring(0,[Math]::Min($m.Index,$text.Length)) -split "`n").Count
  $win = $text.Substring($m.Index, [Math]::Min(500, $text.Length - $m.Index))
  $typeMatch = $rxAjaxT.Match($win)
  $method = if ($typeMatch.Success) { $typeMatch.Groups['type'].Value.ToUpper() } else { "GET" }
  Add-ApiCall $method $m.Groups['url'].Value $ln
}

# --- 4) Ключевые элементы UI (inputs/selects с ключевыми словами)
$rxInpSel = [regex]'(?is)<(input|select)\b[^>]*?(id|name)\s*=\s*["''](?<key>[^"'']+)["''][^>]*>'
$uiKeys = @()
foreach ($mm in $rxInpSel.Matches($text)) {
  $k = $mm.Groups['key'].Value
  if ($k -match '(?i)patient|doctor|service|room|cabinet|search') { $uiKeys += $k }
}
$uiKeys = $uiKeys | Sort-Object -Unique

# --- 5) Блок событий FullCalendar (events: ... / eventSources)
function Grab-Context([int]$center,[int]$pre,[int]$post) {
  $s = [Math]::Max(0, $center-$pre)
  $e = [Math]::Min($lines.Count-1, $center+$post)
  return $lines[$s..$e]
}
$eventsBlock = @()
$hit = $false
for ($i=0; $i -lt $lines.Count; $i++) {
  if ($lines[$i] -match '(?i)\bevents\s*:') { $eventsBlock = Grab-Context $i 2 40; $hit=$true; break }
  if ($lines[$i] -match '(?i)eventSources')  { $eventsBlock = Grab-Context $i 2 40; $hit=$true; break }
}

# --- 6) Извлечение параметров из URL (?a=1&b=2) и подсказок из JS (params:)
$paramKeys = New-Object System.Collections.Generic.HashSet[string]
foreach ($c in $apiCalls) {
  if ($c.url -match '\?(?<q>[^#]+)$') {
    $pairs = $Matches['q'] -split '&'
    foreach ($p in $pairs) {
      $eq = $p.IndexOf('=')
      if ($eq -gt 0) { [void]$paramKeys.Add($p.Substring(0,$eq)) } else { [void]$paramKeys.Add($p) }
    }
  }
}
# простая эвристика по коду (patientId / patient_id и т.п.)
$rxParamLike = [regex]'(?i)\b(patient[_-]?id|doctor[_-]?id|service[_-]?id|room|cabinet|date|start|end)\b'
foreach ($m in $rxParamLike.Matches($text)) { [void]$paramKeys.Add($m.Value.ToLower()) }

# --- 7) Сопоставление с backend snapshot (если есть)
$backendMatches = @()
if (Test-Path $Snapshot -PathType Leaf) {
  $snap = Get-Content -Path $Snapshot -Raw
  $paths = ($apiCalls | ForEach-Object {
    $u=$_.url
    if ($u -match '^(https?://[^/]+)?(?<path>/[^?\s#"]+)') { $Matches['path'] } else { $u }
  }) | Sort-Object -Unique
  foreach ($p in $paths) {
    if ([string]::IsNullOrWhiteSpace($p)) { continue }
    # строки вида: some.py:L123: METHOD /path
    $rxLine = [regex]([regex]::Escape(" ")+".*"+[regex]::Escape($p))
    $hitLines = ($snap -split "`n") | Where-Object { $_ -match $rxLine }
    foreach ($hl in $hitLines) { $backendMatches += $hl }
  }
  $backendMatches = $backendMatches | Sort-Object -Unique
}

# --- 8) Пишем отчёт
"" | Set-Content -Path $rep -Encoding UTF8
$ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
Add-Content $rep ("# Calendar report")
Add-Content $rep ""
Add-Content $rep ("Generated: {0}" -f $ts)
Add-Content $rep ("Source: {0}" -f (Resolve-Path -Relative $Calendar))
Add-Content $rep ""
Add-Content $rep "## Frontend API calls (method url @line)"
if ($apiCalls.Count -gt 0) {
  foreach ($c in ($apiCalls | Sort-Object url, method, line)) {
    Add-Content $rep ("- {0} {1}  @L{2}" -f $c.method, $c.url, $c.line)
  }
} else { Add-Content $rep "_not detected_" }
Add-Content $rep ""

Add-Content $rep "## Likely query parameters"
if ($paramKeys.Count -gt 0) {
  foreach ($k in ($paramKeys | Sort-Object)) { Add-Content $rep ("- {0}" -f $k) }
} else { Add-Content $rep "_not detected_" }
Add-Content $rep ""

Add-Content $rep "## UI inputs/selects (key hints)"
if ($uiKeys.Count -gt 0) {
  foreach ($k in $uiKeys) { Add-Content $rep ("- {0}" -f $k) }
} else { Add-Content $rep "_not detected_" }
Add-Content $rep ""

Add-Content $rep "## FullCalendar events block (context)"
if ($hit -and $eventsBlock.Count -gt 0) {
  Add-Content $rep '```js'
  $eventsBlock | Add-Content $rep
  Add-Content $rep '```'
} else { Add-Content $rep "_not detected_" }
Add-Content $rep ""

Add-Content $rep "## Backend matches (from ROUTES_METHODS_FRONT_AND_TREE.md)"
if ($backendMatches.Count -gt 0) {
  foreach ($l in $backendMatches) { Add-Content $rep ("- {0}" -f $l) }
} else { Add-Content $rep "_no matches or snapshot missing_" }

Write-Host ("OK -> " + $txt)
Write-Host ("OK -> " + $md)
Write-Host ("OK -> " + $copy)
Write-Host ("OK -> " + $rep)
