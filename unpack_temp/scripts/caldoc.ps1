param(
  [string]$Calendar = ".\templates\calendar.html",
  [string]$OutDir   = ".\artifacts",
  [string]$Snapshot = ".\artifacts\ROUTES_METHODS_FRONT_AND_TREE.md",
  [string]$OutName  = "CALENDAR_OVERVIEW.md"
)

if (-not (Test-Path $Calendar -PathType Leaf)) { Write-Error ("Файл не найден: " + $Calendar); exit 1 }
if (-not (Test-Path $OutDir -PathType Container)) { New-Item -ItemType Directory -Path $OutDir | Out-Null }

$rep = Join-Path $OutDir $OutName

# --- читаем HTML календаря
$text  = Get-Content -Path $Calendar -Raw
$lines = $text -split "`n"

# --- детект фронт-вызовов
$rxFetch = [regex]'(?i)fetch\(\s*["''](?<url>[^"'']+)["''](?:\s*,\s*\{[^}]*\bmethod\s*:\s*["''](?<method>GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD)["''])?'
$rxAxios = [regex]'(?i)axios\.(?<verb>get|post|put|patch|delete|options|head)\(\s*["''](?<url>[^"'']+)["'']'
$rxAjaxU = [regex]'(?is)\$\.ajax\(\s*\{[^}]*\burl\s*:\s*["''](?<url>[^"'']+)["'']'
$rxAjaxT = [regex]'(?i)\btype\s*:\s*["''](?<type>GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD)["'']'

$apiCalls = New-Object System.Collections.Generic.List[object]
function Add-ApiCall([string]$meth,[string]$url,[int]$ln) {
  $apiCalls.Add([PSCustomObject]@{ method=$meth; url=$url; line=$ln }) | Out-Null
}
foreach ($m in $rxFetch.Matches($text)) { $ln = ($text.Substring(0,[Math]::Min($m.Index,$text.Length)) -split "`n").Count; $method = if ($m.Groups['method'].Success) { $m.Groups['method'].Value.ToUpper() } else { "GET" }; Add-ApiCall $method $m.Groups['url'].Value $ln }
foreach ($m in $rxAxios.Matches($text)) { $ln = ($text.Substring(0,[Math]::Min($m.Index,$text.Length)) -split "`n").Count; Add-ApiCall ($m.Groups['verb'].Value.ToUpper()) $m.Groups['url'].Value $ln }
foreach ($m in $rxAjaxU.Matches($text)) { $ln = ($text.Substring(0,[Math]::Min($m.Index,$text.Length)) -split "`n").Count; $win = $text.Substring($m.Index, [Math]::Min(500, $text.Length - $m.Index)); $typeMatch = $rxAjaxT.Match($win); $method = if ($typeMatch.Success) { $typeMatch.Groups['type'].Value.ToUpper() } else { "GET" }; Add-ApiCall $method $m.Groups['url'].Value $ln }

# --- inputs/selects с полезными ключами
$rxInpSel = [regex]'(?is)<(input|select)\b[^>]*?(id|name)\s*=\s*["''](?<key>[^"'']+)["''][^>]*>'
$uiKeys = @()
foreach ($mm in $rxInpSel.Matches($text)) {
  $k = $mm.Groups['key'].Value
  if ($k -match '(?i)patient|doctor|service|room|cabinet|search|date|start|end') { $uiKeys += $k }
}
$uiKeys = $uiKeys | Sort-Object -Unique

# --- блок events / eventSources
function Grab-Context([int]$center,[int]$pre,[int]$post) { $s=[Math]::Max(0,$center-$pre); $e=[Math]::Min($lines.Count-1,$center+$post); return $lines[$s..$e] }
$eventsBlock = @(); $hit=$false
for ($i=0; $i -lt $lines.Count; $i++) {
  if ($lines[$i] -match '(?i)\bevents\s*:') { $eventsBlock = Grab-Context $i 2 50; $hit=$true; break }
  if ($lines[$i] -match '(?i)eventSources')  { $eventsBlock = Grab-Context $i 2 50; $hit=$true; break }
}

# --- параметры из URL и из кода
$paramKeys = New-Object System.Collections.Generic.HashSet[string]
foreach ($c in $apiCalls) {
  if ($c.url -match '\?(?<q>[^#]+)$') {
    foreach ($p in (($Matches['q'] -split '&'))) {
      $eq = $p.IndexOf('='); if ($eq -gt 0) { [void]$paramKeys.Add($p.Substring(0,$eq)) } else { [void]$paramKeys.Add($p) }
    }
  }
}
$rxParamLike = [regex]'(?i)\b(patient[_-]?id|doctor[_-]?id|service[_-]?id|room|cabinet|date|start|end)\b'
foreach ($m in $rxParamLike.Matches($text)) { [void]$paramKeys.Add($m.Value.ToLower()) }

# --- подтягиваем бэкенд-совпадения из snapshot (если есть)
$backendMatches = @()
$apiPaths = ($apiCalls | ForEach-Object {
  $u=$_.url; if ($u -match '^(https?://[^/]+)?(?<path>/[^?\s#"]+)') { $Matches['path'] } else { $u }
}) | Sort-Object -Unique
if (Test-Path $Snapshot -PathType Leaf) {
  $snap = Get-Content -Path $Snapshot -Raw
  foreach ($p in $apiPaths) {
    if ([string]::IsNullOrWhiteSpace($p)) { continue }
    $rxLine = [regex]([regex]::Escape(" ")+".*"+[regex]::Escape($p))
    $hitLines = ($snap -split "`n") | Where-Object { $_ -match $rxLine }
    foreach ($hl in $hitLines) { $backendMatches += $hl }
  }
  $backendMatches = $backendMatches | Sort-Object -Unique
}

# --- пишем OVERVIEW
"" | Set-Content -Path $rep -Encoding UTF8
$ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
Add-Content $rep ("# Calendar — Overview")
Add-Content $rep ""
Add-Content $rep ("Generated: {0}" -f $ts)
Add-Content $rep ("Source: {0}" -f (Resolve-Path -Relative $Calendar))
Add-Content $rep ""

Add-Content $rep "## Резюме"
$apiCount = $apiCalls.Count
Add-Content $rep ("- Найдено фронт-вызовов API: {0}" -f $apiCount)
Add-Content $rep ("- Ключевые параметры: {0}" -f (([string[]]$paramKeys | Sort-Object) -join ", "))
Add-Content $rep ("- Полезные input/select: {0}" -f (($uiKeys) -join ", "))
Add-Content $rep ""

Add-Content $rep "## API вызовы (method url @line)"
if ($apiCount -gt 0) {
  foreach ($c in ($apiCalls | Sort-Object url, method, line)) {
    Add-Content $rep ("- {0} {1}  @L{2}" -f $c.method, $c.url, $c.line)
  }
} else { Add-Content $rep "_не обнаружено_" }
Add-Content $rep ""

Add-Content $rep "## Блок формирования событий (FullCalendar)"
if ($hit -and $eventsBlock.Count -gt 0) {
  Add-Content $rep '```js'
  $eventsBlock | Add-Content $rep
  Add-Content $rep '```'
} else { Add-Content $rep "_не обнаружено_" }
Add-Content $rep ""

Add-Content $rep "## Соответствие backend (по снапшоту ROUTES_METHODS_FRONT_AND_TREE.md)"
if ($backendMatches.Count -gt 0) {
  foreach ($l in $backendMatches) { Add-Content $rep ("- {0}" -f $l) }
} else { Add-Content $rep "_совпадений нет или снапшот отсутствует_" }
Add-Content $rep ""

Add-Content $rep "## Поток данных (кратко)"
Add-Content $rep "- Пользователь меняет фильтры/инпуты (`patient_id`, `doctor_id`, `service_id`, `room`, `date/start/end`)."
Add-Content $rep "- JS формирует запрос к API (см. раздел *API вызовы*)."
Add-Content $rep "- Бэкенд возвращает события; календарь перерисовывает слоты."
Add-Content $rep ""

Write-Host ("OK -> " + $rep)
