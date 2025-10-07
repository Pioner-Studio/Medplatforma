param(
  [string]$Calendar = ".\templates\calendar.html",
  [string]$OutDir   = ".\artifacts",
  [string]$Snapshot = ".\artifacts\ROUTES_METHODS_FRONT_AND_TREE.md",
  [int]$Pre = 6,
  [int]$Post = 40,
  [string]$ReportName = "CALENDAR_ALL.md"
)

if (-not (Test-Path $Calendar -PathType Leaf)) { Write-Error ("Calendar not found: " + $Calendar); exit 1 }
if (-not (Test-Path $OutDir -PathType Container)) { New-Item -ItemType Directory -Path $OutDir | Out-Null }

# --- outputs
$txt = Join-Path $OutDir "calendar.html.txt"
$rep = Join-Path $OutDir $ReportName

# --- 1) Plain TXT export
Get-Content -Path $Calendar -Raw | Set-Content -Path $txt -Encoding UTF8

# --- helpers (без бэктиков, используем ~~~)
function W-Sub([string]$title){ "## $title" | Add-Content $rep -Encoding UTF8; "" | Add-Content $rep -Encoding UTF8 }
function W-Code([string[]]$arr,[string]$lang="js"){
  "~~~$lang" | Add-Content $rep -Encoding UTF8
  if ($arr) { $arr | Add-Content $rep -Encoding UTF8 }
  "~~~" | Add-Content $rep -Encoding UTF8
  "" | Add-Content $rep -Encoding UTF8
}
function Grab-Context([string[]]$lines,[int]$center,[int]$pre,[int]$post){
  $s=[Math]::Max(0,$center-$pre); $e=[Math]::Min($lines.Count-1,$center+$post); return $lines[$s..$e]
}
function LineNum([string]$text,[int]$idx){
  $slice = $text.Substring(0,[Math]::Min($idx,$text.Length))
  return ([System.Text.RegularExpressions.Regex]::Split($slice, "\r?\n")).Count
}

# --- read source
$text  = Get-Content -Path $Calendar -Raw
$lines = [System.Text.RegularExpressions.Regex]::Split($text, "\r?\n")

# --- 2) ALL UPPER_CASE constants (const/let/var + object keys)
$constSet = New-Object System.Collections.Generic.HashSet[string]
$rxVar  = [regex]'(?m)^\s*(?:const|let|var)\s+([A-Z][A-Z0-9_]+)\s*='
foreach($m in $rxVar.Matches($text)){ [void]$constSet.Add($m.Groups[1].Value) }
$rxObj  = [regex]'(?m)^\s*([A-Z][A-Z0-9_]+)\s*:\s*'
foreach($m in $rxObj.Matches($text)){ [void]$constSet.Add($m.Groups[1].Value) }
$consts = @($constSet | Sort-Object)

# --- 3) Key blocks (events / eventSources / FullCalendar init)
$keyBlocks = @()
$rxEvents = [regex]'(?i)\bevents\s*:'
$rxSources= [regex]'(?i)\beventSources\b'
$rxInit   = [regex]'(?i)new\s+FullCalendar\.Calendar|FullCalendar\.initialize|FullCalendar\('

for($i=0;$i -lt $lines.Count;$i++){ if($lines[$i] -match $rxEvents ){ $keyBlocks += [PSCustomObject]@{title="events:";          line=$i; ctx=(Grab-Context $lines $i $Pre $Post)}; break } }
for($i=0;$i -lt $lines.Count;$i++){ if($lines[$i] -match $rxSources){ $keyBlocks += [PSCustomObject]@{title="eventSources";     line=$i; ctx=(Grab-Context $lines $i $Pre $Post)}; break } }
for($i=0;$i -lt $lines.Count;$i++){ if($lines[$i] -match $rxInit   ){ $keyBlocks += [PSCustomObject]@{title="FullCalendar init"; line=$i; ctx=(Grab-Context $lines $i $Pre $Post)}; break } }

# --- 4) Frontend API calls (fetch/axios/jQuery) — кавычки как \u0027
$rxFetch = [regex]'(?i)fetch\(\s*["\u0027](?<url>[^"\u0027]+)["\u0027](?:\s*,\s*\{[^}]*\bmethod\s*:\s*["\u0027](?<method>GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD)["\u0027])?'
$rxAxios = [regex]'(?i)axios\.(?<verb>get|post|put|patch|delete|options|head)\(\s*["\u0027](?<url>[^"\u0027]+)["\u0027]'
$rxAjaxU = [regex]'(?is)\$\.ajax\(\s*\{[^}]*\burl\s*:\s*["\u0027](?<url>[^"\u0027]+)["\u0027]'
$rxAjaxT = [regex]'(?i)\btype\s*:\s*["\u0027](?<type>GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD)["\u0027]'
$apiCalls = New-Object System.Collections.Generic.List[object]

foreach($m in $rxFetch.Matches($text)){
  $ln = LineNum $text $m.Index
  $method = if($m.Groups['method'].Success){ $m.Groups['method'].Value.ToUpper() } else { "GET" }
  $apiCalls.Add([PSCustomObject]@{method=$method; url=$m.Groups['url'].Value; line=$ln}) | Out-Null
}
foreach($m in $rxAxios.Matches($text)){
  $ln = LineNum $text $m.Index
  $apiCalls.Add([PSCustomObject]@{method=$m.Groups['verb'].Value.ToUpper(); url=$m.Groups['url'].Value; line=$ln}) | Out-Null
}
foreach($m in $rxAjaxU.Matches($text)){
  $ln = LineNum $text $m.Index
  $win = $text.Substring($m.Index, [Math]::Min(600, $text.Length - $m.Index))
  $t = $rxAjaxT.Match($win)
  $method = if($t.Success){ $t.Groups['type'].Value.ToUpper() } else { "GET" }
  $apiCalls.Add([PSCustomObject]@{method=$method; url=$m.Groups['url'].Value; line=$ln}) | Out-Null
}

# --- 5) Query params + эвристики
$paramSet = New-Object System.Collections.Generic.HashSet[string]
foreach($c in $apiCalls){
  if($c.url -match '\?(?<q>[^#]+)$'){
    $pairs = $Matches['q'] -split '&'
    foreach($p in $pairs){
      $eq = $p.IndexOf('=')
      if($eq -gt 0){ [void]$paramSet.Add($p.Substring(0,$eq)) } else { [void]$paramSet.Add($p) }
    }
  }
}
$rxParamLike = [regex]'(?i)\b(patient[_-]?id|doctor[_-]?id|service[_-]?id|room|cabinet|date|start|end)\b'
foreach($m in $rxParamLike.Matches($text)){ [void]$paramSet.Add($m.Value.ToLower()) }
$paramKeys = @($paramSet | Sort-Object)

# --- 6) UI inputs/selects (id/name)
$rxInpSel = [regex]'(?is)<(input|select)\b[^>]*?(id|name)\s*=\s*["\u0027](?<key>[^"\u0027]+)["\u0027][^>]*>'
$uiKeys = @()
foreach($mm in $rxInpSel.Matches($text)){
  $k=$mm.Groups['key'].Value
  if($k -match '(?i)patient|doctor|service|room|cabinet|search|date|start|end'){ $uiKeys += $k }
}
$uiKeys = @($uiKeys | Sort-Object -Unique)

# --- 7) Backend matches (по снапшоту, если есть)
$backendMatches = @()
$apiPaths = @(
  $apiCalls | ForEach-Object {
    $u=$_.url; if($u -match '^(https?://[^/]+)?(?<path>/[^?\s#"]+)'){ $Matches['path'] } else { $u }
  }
) | Sort-Object -Unique
if(Test-Path $Snapshot -PathType Leaf){
  $snap = Get-Content -Path $Snapshot -Raw
  foreach($p in $apiPaths){
    if([string]::IsNullOrWhiteSpace($p)){ continue }
    $rxLine = [regex]([regex]::Escape(" ")+".*"+[regex]::Escape($p))
    $hitLines = ($snap -split "\r?\n") | Where-Object { $_ -match $rxLine }
    foreach($hl in $hitLines){ $backendMatches += $hl }
  }
  $backendMatches = @($backendMatches | Sort-Object -Unique)
}

# --- 8) Write report
"" | Set-Content $rep -Encoding UTF8
$ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content $rep "<!-- GENERATED: $ts -->"
Add-Content $rep "# Calendar — ALL-IN-ONE report"
Add-Content $rep ""
Add-Content $rep ("Source: {0}" -f (Resolve-Path -Relative $Calendar))
Add-Content $rep ""

W-Sub "Summary"
Add-Content $rep ("- API calls detected: {0}" -f ($apiCalls.Count))
Add-Content $rep ("- UPPER_CASE constants: {0}" -f ( ($consts    | Measure-Object).Count ))
Add-Content $rep ("- Key inputs/selects: {0}" -f ( ($uiKeys     | Measure-Object).Count ))
Add-Content $rep ""

W-Sub "ALL constants (UPPER_CASE)"
if( ( ($consts | Measure-Object).Count ) -gt 0 ){ $consts | ForEach-Object { "- $_" } | Add-Content $rep -Encoding UTF8 } else { Add-Content $rep "_none_" }
Add-Content $rep ""

W-Sub "Key blocks"
if( @($keyBlocks).Count -gt 0 ){
  foreach($b in $keyBlocks){
    Add-Content $rep ("### {0}  (@L{1})" -f $b.title, ($b.line+1))
    W-Code $b.ctx "js"
  }
} else { Add-Content $rep "_not detected_" }

W-Sub "Frontend API calls (method url @line)"
if($apiCalls.Count -gt 0){
  foreach($c in ($apiCalls | Sort-Object url, method, line)){
    Add-Content $rep ("- {0} {1}  @L{2}" -f $c.method, $c.url, $c.line)
  }
}else{ Add-Content $rep "_none_" }
Add-Content $rep ""

W-Sub "Likely query parameters"
if( ( ($paramKeys | Measure-Object).Count ) -gt 0 ){ foreach($k in $paramKeys){ Add-Content $rep ("- {0}" -f $k) } } else { Add-Content $rep "_none_" }
Add-Content $rep ""

W-Sub "UI inputs/selects (id/name hints)"
if( ( ($uiKeys | Measure-Object).Count ) -gt 0 ){ foreach($k in $uiKeys){ Add-Content $rep ("- {0}" -f $k) } } else { Add-Content $rep "_none_" }
Add-Content $rep ""

W-Sub "Backend matches (by snapshot)"
if( ( (@($backendMatches) | Measure-Object).Count ) -gt 0 ){ foreach($l in $backendMatches){ Add-Content $rep ("- {0}" -f $l) } } else { Add-Content $rep "_no matches or snapshot missing_" }

Write-Host ("OK -> " + $txt)
Write-Host ("OK -> " + $rep)
