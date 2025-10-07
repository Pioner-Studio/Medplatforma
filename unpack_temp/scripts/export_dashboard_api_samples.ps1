<#
  export_dashboard_api_samples.ps1
  Собирает реальные примеры ответов для панели кабинетов + отчёт.

  Что делает:
  1) Читает templates/calendar.html, вытягивает все "/api/..." URL и рядом пытается угадать метод.
  2) Пытается определить:
     - GET  /api/rooms/status_now
     - POST/GET /api/free_slots (или похожее)
     - GET  /api/today_details?room=...
     - POST /api/appointments/update_time (для запроса — только шаблон payload)
  3) Дёргает API и кладёт результаты в artifacts/rooms_panel:
     - rooms_status_now.json
     - free_slots_request.json / free_slots_response.json
     - today_details_response.json
     - update_time_request_template.json
     - ROOMS_PANEL_API_REPORT.md
#>

param(
  [string]$BaseUrl   = "http://localhost:5000",
  [string]$Calendar  = ".\templates\calendar.html",
  [string]$OutDir    = ".\artifacts\rooms_panel",
  [string]$RoomHint  = "",
  [int]$TimeoutSec   = 10
)

# ---------- helpers ----------
function Ensure-OutDir([string]$p) {
  if (-not (Test-Path $p -PathType Container)) { New-Item -ItemType Directory -Path $p | Out-Null }
}
function Join-Url([string]$base, [string]$path) {
  if ([string]::IsNullOrWhiteSpace($path)) { return $base }
  if ($path -match '^https?://') { return $path }
  $b = $base.TrimEnd('/')
  $u = $path.TrimStart('/')
  return "$b/$u"
}
function Get-LineNum([string]$text, [int]$index) {
  if ($index -lt 0) { return 1 }
  $slice = $text.Substring(0, [Math]::Min($index, $text.Length))
  return ($slice -split "`n").Count
}
function UrlEncode([string]$s) { [System.Uri]::EscapeDataString([string]$s) }
function DictToQuery([hashtable]$d) {
  if (-not $d -or $d.Keys.Count -eq 0) { return "" }
  $pairs = @()
  foreach ($k in $d.Keys) { $pairs += ("{0}={1}" -f (UrlEncode $k), (UrlEncode ([string]$d[$k]))) }
  return ($pairs -join "&")
}
function Save-Json([string]$path, $obj) {
  $json = $obj | ConvertTo-Json -Depth 12
  Set-Content -Path $path -Value $json -Encoding UTF8
}
function Fetch-Json {
  param(
    [ValidateSet("GET","POST","PUT","PATCH","DELETE","HEAD","OPTIONS")]
    [string]$Method,
    [string]$Url,
    [hashtable]$Headers = $null,
    $Body = $null,
    [int]$TimeoutSec = 10
  )
  try {
    $params = @{
      Method      = $Method
      Uri         = $Url
      ErrorAction = "Stop"
    }
    if ($Headers) { $params["Headers"] = $Headers }
    if ($Body -ne $null -and $Method -in @("POST","PUT","PATCH","DELETE")) {
      if ($Body -is [hashtable] -or $Body -is [pscustomobject]) {
        $params["Body"] = ($Body | ConvertTo-Json -Depth 10)
        $params["ContentType"] = "application/json"
      } else {
        $params["Body"] = [string]$Body
      }
    }
    $resp = Invoke-RestMethod @params
    return @{ ok=$true; status=200; data=$resp; error=$null }
  } catch {
    $msg = $_.Exception.Message
    return @{ ok=$false; status=0; data=$null; error=$msg }
  }
}

# Вытащить все "/api/..." URL из файла и угадать метод по контексту
function Extract-ApiCalls([string]$text) {
  $calls = New-Object System.Collections.Generic.List[object]
  # Важно: строка single-quoted с удвоенными одинарными кавычками внутри.
  $rx = [regex]'(?i)[''"](?<url>/api/[^''""]+)[''"]'
  $matches = $rx.Matches($text)
  foreach ($m in $matches) {
    $url = $m.Groups['url'].Value
    $idx = $m.Index
    $line = Get-LineNum $text $idx
    # Контекст ±200 символов
    $s = [Math]::Max(0, $idx - 200)
    $e = [Math]::Min($text.Length, $idx + 200)
    $ctx = $text.Substring($s, $e - $s)
    $method = "GET"
    if ($ctx -match '(?i)axios\.(post|put|patch|delete)\s*\(') { $method = ($Matches[1].ToUpper()) }
    elseif ($ctx -match '(?i)\bmethod\s*:\s*["''](get|post|put|patch|delete|options|head)["'']') { $method = ($Matches[1].ToUpper()) }
    elseif ($ctx -match '(?i)fetch\s*\(' -and $ctx -match '(?i)\bbody\s*:') { $method = "POST" }
    $calls.Add([pscustomobject]@{ url=$url; line=$line; method=$method; ctx=$ctx }) | Out-Null
  }
  # Уникализируем по url+method (берём первый по файлу)
  $uniq = @{}
  $out = @()
  foreach ($c in $calls) {
    $key = $c.url + "|" + $c.method
    if (-not $uniq.ContainsKey($key)) { $uniq[$key] = $true; $out += $c }
  }
  return $out
}

# Подбор эндпоинтов по семантике
function Pick-Endpoint([array]$calls, [string]$kind) {
  $pred = $null
  switch ($kind) {
    "status_now"   { $pred = { ( <#
  export_dashboard_api_samples.ps1
  Собирает реальные примеры ответов для панели кабинетов + отчёт.

  Что делает:
  1) Читает templates/calendar.html, вытягивает все "/api/..." URL и рядом пытается угадать метод.
  2) Пытается определить:
     - GET  /api/rooms/status_now
     - POST/GET /api/free_slots (или похожее)
     - GET  /api/today_details?room=...
     - POST /api/appointments/update_time (для запроса — только шаблон payload)
  3) Дёргает API и кладёт результаты в artifacts/rooms_panel:
     - rooms_status_now.json
     - free_slots_request.json / free_slots_response.json
     - today_details_response.json
     - update_time_request_template.json
     - ROOMS_PANEL_API_REPORT.md
#>

param(
  [string]$BaseUrl   = "http://localhost:5000",
  [string]$Calendar  = ".\templates\calendar.html",
  [string]$OutDir    = ".\artifacts\rooms_panel",
  [string]$RoomHint  = "",
  [int]$TimeoutSec   = 10
)

# ---------- helpers ----------
function Ensure-OutDir([string]$p) {
  if (-not (Test-Path $p -PathType Container)) { New-Item -ItemType Directory -Path $p | Out-Null }
}
function Join-Url([string]$base, [string]$path) {
  if ([string]::IsNullOrWhiteSpace($path)) { return $base }
  if ($path -match '^https?://') { return $path }
  $b = $base.TrimEnd('/')
  $u = $path.TrimStart('/')
  return "$b/$u"
}
function Get-LineNum([string]$text, [int]$index) {
  if ($index -lt 0) { return 1 }
  $slice = $text.Substring(0, [Math]::Min($index, $text.Length))
  return ($slice -split "`n").Count
}
function UrlEncode([string]$s) { [System.Uri]::EscapeDataString([string]$s) }
function DictToQuery([hashtable]$d) {
  if (-not $d -or $d.Keys.Count -eq 0) { return "" }
  $pairs = @()
  foreach ($k in $d.Keys) { $pairs += ("{0}={1}" -f (UrlEncode $k), (UrlEncode ([string]$d[$k]))) }
  return ($pairs -join "&")
}
function Save-Json([string]$path, $obj) {
  $json = $obj | ConvertTo-Json -Depth 12
  Set-Content -Path $path -Value $json -Encoding UTF8
}
function Fetch-Json {
  param(
    [ValidateSet("GET","POST","PUT","PATCH","DELETE","HEAD","OPTIONS")]
    [string]$Method,
    [string]$Url,
    [hashtable]$Headers = $null,
    $Body = $null,
    [int]$TimeoutSec = 10
  )
  try {
    $params = @{
      Method      = $Method
      Uri         = $Url
      ErrorAction = "Stop"
    }
    if ($Headers) { $params["Headers"] = $Headers }
    if ($Body -ne $null -and $Method -in @("POST","PUT","PATCH","DELETE")) {
      if ($Body -is [hashtable] -or $Body -is [pscustomobject]) {
        $params["Body"] = ($Body | ConvertTo-Json -Depth 10)
        $params["ContentType"] = "application/json"
      } else {
        $params["Body"] = [string]$Body
      }
    }
    $resp = Invoke-RestMethod @params
    return @{ ok=$true; status=200; data=$resp; error=$null }
  } catch {
    $msg = $_.Exception.Message
    return @{ ok=$false; status=0; data=$null; error=$msg }
  }
}

# Вытащить все "/api/..." URL из файла и угадать метод по контексту
function Extract-ApiCalls([string]$text) {
  $calls = New-Object System.Collections.Generic.List[object]
  # Важно: строка single-quoted с удвоенными одинарными кавычками внутри.
  $rx = [regex]'(?i)[''"](?<url>/api/[^''""]+)[''"]'
  $matches = $rx.Matches($text)
  foreach ($m in $matches) {
    $url = $m.Groups['url'].Value
    $idx = $m.Index
    $line = Get-LineNum $text $idx
    # Контекст ±200 символов
    $s = [Math]::Max(0, $idx - 200)
    $e = [Math]::Min($text.Length, $idx + 200)
    $ctx = $text.Substring($s, $e - $s)
    $method = "GET"
    if ($ctx -match '(?i)axios\.(post|put|patch|delete)\s*\(') { $method = ($Matches[1].ToUpper()) }
    elseif ($ctx -match '(?i)\bmethod\s*:\s*["''](get|post|put|patch|delete|options|head)["'']') { $method = ($Matches[1].ToUpper()) }
    elseif ($ctx -match '(?i)fetch\s*\(' -and $ctx -match '(?i)\bbody\s*:') { $method = "POST" }
    $calls.Add([pscustomobject]@{ url=$url; line=$line; method=$method; ctx=$ctx }) | Out-Null
  }
  # Уникализируем по url+method (берём первый по файлу)
  $uniq = @{}
  $out = @()
  foreach ($c in $calls) {
    $key = $c.url + "|" + $c.method
    if (-not $uniq.ContainsKey($key)) { $uniq[$key] = $true; $out += $c }
  }
  return $out
}

# Подбор эндпоинтов по семантике
function Pick-Endpoint([array]$calls, [string]$kind) {
  $pred = $null
  switch ($kind) {
    "status_now"   { $pred = { ( $_.url -match '(?i)status' -and $_.url -match '(?i)room' ) -or $_.url -match '(?i)/rooms/status' } }
    "free_slots"   { $pred = { $_.url -match '(?i)free.*slot|slot.*free|/slots(\b|/)|/free_slots(\b|/)' } }
    "today_details"{ $pred = { $_.url -match '(?i)today.*detail|detail.*today|/today_details(\b|/)' } }
    "update_time"  { $pred = { $_.url -match '(?i)update[_-]?time' } }
    default        { $pred = { $false } }
  }
  $found = $calls | Where-Object $pred
  if ($found.Count -gt 0) {
    $post = $found | Where-Object { $_.method -eq "POST" } | Select-Object -First 1
    if ($post) { return $post }
    return ($found | Select-Object -First 1)
  }
  return $null
}

# Разбор ожидаемого payload для update_time прямо из кода (ищем JSON.stringify({...}))
function Guess-UpdateTime-PayloadKeys([string]$text) {
  $keys = New-Object System.Collections.Generic.HashSet[string]
  $rx = [regex]'(?is)update[_-]?time.*?JSON\.stringify\s*\(\s*\{(?<obj>[^}]*)\}'
  $m = $rx.Match($text)
  if ($m.Success) {
    $obj = $m.Groups['obj'].Value
    $rxk = [regex]'["''](?<k>[A-Za-z0-9_]+)["'']\s*:'
    foreach ($mm in $rxk.Matches($obj)) { [void]$keys.Add($mm.Groups['k'].Value) }
  } else {
    # запасные часто используемые
    [void]$keys.Add("id")
    [void]$keys.Add("start")
    [void]$keys.Add("end")
    [void]$keys.Add("room")
    [void]$keys.Add("doctor_id")
  }
  return ($keys | Sort-Object)
}

# ---------- main ----------
if (-not (Test-Path $Calendar -PathType Leaf)) {
  Write-Error ("calendar not found: " + $Calendar); exit 1
}
$calText = Get-Content -Path $Calendar -Raw
Ensure-OutDir $OutDir

$ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
$dir = $OutDir
$report = Join-Path $dir "ROOMS_PANEL_API_REPORT.md"
"" | Set-Content -Path $report -Encoding UTF8
Add-Content $report "<!-- GENERATED: $ts -->"
Add-Content $report "# Rooms panel API — autodetected endpoints"
Add-Content $report ""
Add-Content $report ("Source calendar: {0}" -f (Resolve-Path -Relative $Calendar))
Add-Content $report ("BaseUrl: {0}" -f $BaseUrl)
if ($RoomHint) { Add-Content $report ("RoomHint: {0}" -f $RoomHint) }
Add-Content $report ""

$calls = Extract-ApiCalls $calText

# A1) /api/rooms/status_now
$epStatus = Pick-Endpoint $calls "status_now"
if ($epStatus) {
  $url1 = Join-Url $BaseUrl $epStatus.url
  $r1 = Fetch-Json -Method "GET" -Url $url1 -TimeoutSec $TimeoutSec
  $file1 = Join-Path $dir "rooms_status_now.json"
  if ($r1.ok) { Save-Json $file1 $r1.data } else { Save-Json $file1 @{ error=$r1.error; endpoint=$url1 } }
  Add-Content $report "## A1) GET /api/rooms/status_now"
  Add-Content $report ("- detected url: {0}" -f $epStatus.url)
  Add-Content $report ("- method guess: {0}" -f $epStatus.method)
  Add-Content $report ("- saved: {0}" -f (Resolve-Path -Relative $file1))
  Add-Content $report ""
} else {
  Add-Content $report "## A1) /api/rooms/status_now"
  Add-Content $report "_not found in calendar_"
  Add-Content $report ""
}

# A2) /api/free_slots (или подобное)
$epSlots = Pick-Endpoint $calls "free_slots"
if ($epSlots) {
  $room = $RoomHint
  if (-not $room) {
    # попробовать вытащить имя комнаты из HTML
    $mroom = [regex]::Match($calText, '(?i)(id|name)\s*=\s*["'']room(_name)?["''][^>]*value\s*=\s*["'']([^"'']+)["'']')
    if ($mroom.Success) { $room = $mroom.Groups[3].Value }
  }
  if (-not $room) { $room = "Ортопедия" }

  $date = (Get-Date).ToString("yyyy-MM-dd")
  $step = 15

  $uSlotsBase = Join-Url $BaseUrl $epSlots.url
  $qs = @{ room = $room; date = $date; step = $step }
  $qsStr = DictToQuery $qs
  if ($uSlotsBase -like "*?*") { $uSlotsGet = "$uSlotsBase&$qsStr" } else { $uSlotsGet = "$uSlotsBase?$qsStr" }

  $reqBody    = @{ room=$room; date=$date; step=$step }
  $reqHeaders = @{ "Content-Type" = "application/json" }

  $r2 = $null
  if ($epSlots.method -eq "POST") {
    $r2 = Fetch-Json -Method "POST" -Url $uSlotsBase -Body $reqBody -Headers $reqHeaders -TimeoutSec $TimeoutSec
    $reqMethod = "POST"
  } else {
    $tryGet = Fetch-Json -Method "GET" -Url $uSlotsGet -TimeoutSec $TimeoutSec
    if ($tryGet.ok) { $r2 = $tryGet; $reqMethod = "GET" }
    else { $r2 = Fetch-Json -Method "POST" -Url $uSlotsBase -Body $reqBody -Headers $reqHeaders -TimeoutSec $TimeoutSec; $reqMethod = "POST" }
  }

  $fileReq  = Join-Path $dir "free_slots_request.json"
  $fileResp = Join-Path $dir "free_slots_response.json"
  Save-Json $fileReq  @{ url=$uSlotsBase; query=$qs; method=$reqMethod; body=$reqBody }
  if ($r2.ok) { Save-Json $fileResp $r2.data } else { Save-Json $fileResp @{ error=$r2.error; endpoint=$uSlotsBase } }

  Add-Content $report "## A2) /api/free_slots (or similar)"
  Add-Content $report ("- detected url: {0}" -f $epSlots.url)
  Add-Content $report ("- method guess: {0}" -f $epSlots.method)
  Add-Content $report ("- request: {0}" -f (Resolve-Path -Relative $fileReq))
  Add-Content $report ("- response: {0}" -f (Resolve-Path -Relative $fileResp))
  Add-Content $report ""
} else {
  Add-Content $report "## A2) /api/free_slots"
  Add-Content $report "_not found in calendar_"
  Add-Content $report ""
}

# A3) /api/today_details?room=...
$epDetails = Pick-Endpoint $calls "today_details"
if ($epDetails) {
  $room = $RoomHint; if (-not $room) { $room = "Ортопедия" }
  $u3   = Join-Url $BaseUrl $epDetails.url
  $qs3  = @{ room = $room }
  $q3   = DictToQuery $qs3
  if ($u3 -like "*?*") { $u3q = "$u3&$q3" } else { $u3q = "$u3?$q3" }
  $r3   = Fetch-Json -Method "GET" -Url $u3q -TimeoutSec $TimeoutSec
  $file3 = Join-Path $dir "today_details_response.json"
  if ($r3.ok) { Save-Json $file3 $r3.data } else { Save-Json $file3 @{ error=$r3.error; endpoint=$u3q } }

  Add-Content $report "## A3) /api/today_details"
  Add-Content $report ("- detected url: {0}" -f $epDetails.url)
  Add-Content $report ("- saved: {0}" -f (Resolve-Path -Relative $file3))
  Add-Content $report ""
} else {
  Add-Content $report "## A3) /api/today_details"
  Add-Content $report "_not found in calendar_"
  Add-Content $report ""
}

# B) update_time — только шаблон payload
$epUpdate    = Pick-Endpoint $calls "update_time"
$payloadKeys = Guess-UpdateTime-PayloadKeys $calText
$fileUpd     = Join-Path $dir "update_time_request_template.json"
$tpl = [ordered]@{}
foreach ($k in $payloadKeys) { $tpl[$k] = "<fill>" }
if ($tpl.Contains("id"))    { $tpl["id"]    = 123 }
if ($tpl.Contains("start")) { $tpl["start"] = (Get-Date).ToString("yyyy-MM-ddT10:30:00Z") }
if ($tpl.Contains("end"))   { $tpl["end"]   = (Get-Date).ToString("yyyy-MM-ddT10:45:00Z") }
Save-Json $fileUpd $tpl

Add-Content $report "## B) update_time"
if ($epUpdate) {
  Add-Content $report ("- detected url: {0}" -f $epUpdate.url)
  Add-Content $report ("- method guess: {0}" -f $epUpdate.method)
} else {
  Add-Content $report "- endpoint not found in calendar"
}
Add-Content $report ("- request template: {0}" -f (Resolve-Path -Relative $fileUpd))
Add-Content $report "- expected keys:"
foreach ($k in $payloadKeys) { Add-Content $report ("  - {0}" -f $k) }
Add-Content $report ""

Write-Host ("OK -> " + (Resolve-Path -Relative $report))
.url -match ''(?i)status'' -and <#
  export_dashboard_api_samples.ps1
  Собирает реальные примеры ответов для панели кабинетов + отчёт.

  Что делает:
  1) Читает templates/calendar.html, вытягивает все "/api/..." URL и рядом пытается угадать метод.
  2) Пытается определить:
     - GET  /api/rooms/status_now
     - POST/GET /api/free_slots (или похожее)
     - GET  /api/today_details?room=...
     - POST /api/appointments/update_time (для запроса — только шаблон payload)
  3) Дёргает API и кладёт результаты в artifacts/rooms_panel:
     - rooms_status_now.json
     - free_slots_request.json / free_slots_response.json
     - today_details_response.json
     - update_time_request_template.json
     - ROOMS_PANEL_API_REPORT.md
#>

param(
  [string]$BaseUrl   = "http://localhost:5000",
  [string]$Calendar  = ".\templates\calendar.html",
  [string]$OutDir    = ".\artifacts\rooms_panel",
  [string]$RoomHint  = "",
  [int]$TimeoutSec   = 10
)

# ---------- helpers ----------
function Ensure-OutDir([string]$p) {
  if (-not (Test-Path $p -PathType Container)) { New-Item -ItemType Directory -Path $p | Out-Null }
}
function Join-Url([string]$base, [string]$path) {
  if ([string]::IsNullOrWhiteSpace($path)) { return $base }
  if ($path -match '^https?://') { return $path }
  $b = $base.TrimEnd('/')
  $u = $path.TrimStart('/')
  return "$b/$u"
}
function Get-LineNum([string]$text, [int]$index) {
  if ($index -lt 0) { return 1 }
  $slice = $text.Substring(0, [Math]::Min($index, $text.Length))
  return ($slice -split "`n").Count
}
function UrlEncode([string]$s) { [System.Uri]::EscapeDataString([string]$s) }
function DictToQuery([hashtable]$d) {
  if (-not $d -or $d.Keys.Count -eq 0) { return "" }
  $pairs = @()
  foreach ($k in $d.Keys) { $pairs += ("{0}={1}" -f (UrlEncode $k), (UrlEncode ([string]$d[$k]))) }
  return ($pairs -join "&")
}
function Save-Json([string]$path, $obj) {
  $json = $obj | ConvertTo-Json -Depth 12
  Set-Content -Path $path -Value $json -Encoding UTF8
}
function Fetch-Json {
  param(
    [ValidateSet("GET","POST","PUT","PATCH","DELETE","HEAD","OPTIONS")]
    [string]$Method,
    [string]$Url,
    [hashtable]$Headers = $null,
    $Body = $null,
    [int]$TimeoutSec = 10
  )
  try {
    $params = @{
      Method      = $Method
      Uri         = $Url
      ErrorAction = "Stop"
    }
    if ($Headers) { $params["Headers"] = $Headers }
    if ($Body -ne $null -and $Method -in @("POST","PUT","PATCH","DELETE")) {
      if ($Body -is [hashtable] -or $Body -is [pscustomobject]) {
        $params["Body"] = ($Body | ConvertTo-Json -Depth 10)
        $params["ContentType"] = "application/json"
      } else {
        $params["Body"] = [string]$Body
      }
    }
    $resp = Invoke-RestMethod @params
    return @{ ok=$true; status=200; data=$resp; error=$null }
  } catch {
    $msg = $_.Exception.Message
    return @{ ok=$false; status=0; data=$null; error=$msg }
  }
}

# Вытащить все "/api/..." URL из файла и угадать метод по контексту
function Extract-ApiCalls([string]$text) {
  $calls = New-Object System.Collections.Generic.List[object]
  # Важно: строка single-quoted с удвоенными одинарными кавычками внутри.
  $rx = [regex]'(?i)[''"](?<url>/api/[^''""]+)[''"]'
  $matches = $rx.Matches($text)
  foreach ($m in $matches) {
    $url = $m.Groups['url'].Value
    $idx = $m.Index
    $line = Get-LineNum $text $idx
    # Контекст ±200 символов
    $s = [Math]::Max(0, $idx - 200)
    $e = [Math]::Min($text.Length, $idx + 200)
    $ctx = $text.Substring($s, $e - $s)
    $method = "GET"
    if ($ctx -match '(?i)axios\.(post|put|patch|delete)\s*\(') { $method = ($Matches[1].ToUpper()) }
    elseif ($ctx -match '(?i)\bmethod\s*:\s*["''](get|post|put|patch|delete|options|head)["'']') { $method = ($Matches[1].ToUpper()) }
    elseif ($ctx -match '(?i)fetch\s*\(' -and $ctx -match '(?i)\bbody\s*:') { $method = "POST" }
    $calls.Add([pscustomobject]@{ url=$url; line=$line; method=$method; ctx=$ctx }) | Out-Null
  }
  # Уникализируем по url+method (берём первый по файлу)
  $uniq = @{}
  $out = @()
  foreach ($c in $calls) {
    $key = $c.url + "|" + $c.method
    if (-not $uniq.ContainsKey($key)) { $uniq[$key] = $true; $out += $c }
  }
  return $out
}

# Подбор эндпоинтов по семантике
function Pick-Endpoint([array]$calls, [string]$kind) {
  $pred = $null
  switch ($kind) {
    "status_now"   { $pred = { ( $_.url -match '(?i)status' -and $_.url -match '(?i)room' ) -or $_.url -match '(?i)/rooms/status' } }
    "free_slots"   { $pred = { $_.url -match '(?i)free.*slot|slot.*free|/slots(\b|/)|/free_slots(\b|/)' } }
    "today_details"{ $pred = { $_.url -match '(?i)today.*detail|detail.*today|/today_details(\b|/)' } }
    "update_time"  { $pred = { $_.url -match '(?i)update[_-]?time' } }
    default        { $pred = { $false } }
  }
  $found = $calls | Where-Object $pred
  if ($found.Count -gt 0) {
    $post = $found | Where-Object { $_.method -eq "POST" } | Select-Object -First 1
    if ($post) { return $post }
    return ($found | Select-Object -First 1)
  }
  return $null
}

# Разбор ожидаемого payload для update_time прямо из кода (ищем JSON.stringify({...}))
function Guess-UpdateTime-PayloadKeys([string]$text) {
  $keys = New-Object System.Collections.Generic.HashSet[string]
  $rx = [regex]'(?is)update[_-]?time.*?JSON\.stringify\s*\(\s*\{(?<obj>[^}]*)\}'
  $m = $rx.Match($text)
  if ($m.Success) {
    $obj = $m.Groups['obj'].Value
    $rxk = [regex]'["''](?<k>[A-Za-z0-9_]+)["'']\s*:'
    foreach ($mm in $rxk.Matches($obj)) { [void]$keys.Add($mm.Groups['k'].Value) }
  } else {
    # запасные часто используемые
    [void]$keys.Add("id")
    [void]$keys.Add("start")
    [void]$keys.Add("end")
    [void]$keys.Add("room")
    [void]$keys.Add("doctor_id")
  }
  return ($keys | Sort-Object)
}

# ---------- main ----------
if (-not (Test-Path $Calendar -PathType Leaf)) {
  Write-Error ("calendar not found: " + $Calendar); exit 1
}
$calText = Get-Content -Path $Calendar -Raw
Ensure-OutDir $OutDir

$ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
$dir = $OutDir
$report = Join-Path $dir "ROOMS_PANEL_API_REPORT.md"
"" | Set-Content -Path $report -Encoding UTF8
Add-Content $report "<!-- GENERATED: $ts -->"
Add-Content $report "# Rooms panel API — autodetected endpoints"
Add-Content $report ""
Add-Content $report ("Source calendar: {0}" -f (Resolve-Path -Relative $Calendar))
Add-Content $report ("BaseUrl: {0}" -f $BaseUrl)
if ($RoomHint) { Add-Content $report ("RoomHint: {0}" -f $RoomHint) }
Add-Content $report ""

$calls = Extract-ApiCalls $calText

# A1) /api/rooms/status_now
$epStatus = Pick-Endpoint $calls "status_now"
if ($epStatus) {
  $url1 = Join-Url $BaseUrl $epStatus.url
  $r1 = Fetch-Json -Method "GET" -Url $url1 -TimeoutSec $TimeoutSec
  $file1 = Join-Path $dir "rooms_status_now.json"
  if ($r1.ok) { Save-Json $file1 $r1.data } else { Save-Json $file1 @{ error=$r1.error; endpoint=$url1 } }
  Add-Content $report "## A1) GET /api/rooms/status_now"
  Add-Content $report ("- detected url: {0}" -f $epStatus.url)
  Add-Content $report ("- method guess: {0}" -f $epStatus.method)
  Add-Content $report ("- saved: {0}" -f (Resolve-Path -Relative $file1))
  Add-Content $report ""
} else {
  Add-Content $report "## A1) /api/rooms/status_now"
  Add-Content $report "_not found in calendar_"
  Add-Content $report ""
}

# A2) /api/free_slots (или подобное)
$epSlots = Pick-Endpoint $calls "free_slots"
if ($epSlots) {
  $room = $RoomHint
  if (-not $room) {
    # попробовать вытащить имя комнаты из HTML
    $mroom = [regex]::Match($calText, '(?i)(id|name)\s*=\s*["'']room(_name)?["''][^>]*value\s*=\s*["'']([^"'']+)["'']')
    if ($mroom.Success) { $room = $mroom.Groups[3].Value }
  }
  if (-not $room) { $room = "Ортопедия" }

  $date = (Get-Date).ToString("yyyy-MM-dd")
  $step = 15

  $uSlotsBase = Join-Url $BaseUrl $epSlots.url
  $qs = @{ room = $room; date = $date; step = $step }
  $qsStr = DictToQuery $qs
  if ($uSlotsBase -like "*?*") { $uSlotsGet = "$uSlotsBase&$qsStr" } else { $uSlotsGet = "$uSlotsBase?$qsStr" }

  $reqBody    = @{ room=$room; date=$date; step=$step }
  $reqHeaders = @{ "Content-Type" = "application/json" }

  $r2 = $null
  if ($epSlots.method -eq "POST") {
    $r2 = Fetch-Json -Method "POST" -Url $uSlotsBase -Body $reqBody -Headers $reqHeaders -TimeoutSec $TimeoutSec
    $reqMethod = "POST"
  } else {
    $tryGet = Fetch-Json -Method "GET" -Url $uSlotsGet -TimeoutSec $TimeoutSec
    if ($tryGet.ok) { $r2 = $tryGet; $reqMethod = "GET" }
    else { $r2 = Fetch-Json -Method "POST" -Url $uSlotsBase -Body $reqBody -Headers $reqHeaders -TimeoutSec $TimeoutSec; $reqMethod = "POST" }
  }

  $fileReq  = Join-Path $dir "free_slots_request.json"
  $fileResp = Join-Path $dir "free_slots_response.json"
  Save-Json $fileReq  @{ url=$uSlotsBase; query=$qs; method=$reqMethod; body=$reqBody }
  if ($r2.ok) { Save-Json $fileResp $r2.data } else { Save-Json $fileResp @{ error=$r2.error; endpoint=$uSlotsBase } }

  Add-Content $report "## A2) /api/free_slots (or similar)"
  Add-Content $report ("- detected url: {0}" -f $epSlots.url)
  Add-Content $report ("- method guess: {0}" -f $epSlots.method)
  Add-Content $report ("- request: {0}" -f (Resolve-Path -Relative $fileReq))
  Add-Content $report ("- response: {0}" -f (Resolve-Path -Relative $fileResp))
  Add-Content $report ""
} else {
  Add-Content $report "## A2) /api/free_slots"
  Add-Content $report "_not found in calendar_"
  Add-Content $report ""
}

# A3) /api/today_details?room=...
$epDetails = Pick-Endpoint $calls "today_details"
if ($epDetails) {
  $room = $RoomHint; if (-not $room) { $room = "Ортопедия" }
  $u3   = Join-Url $BaseUrl $epDetails.url
  $qs3  = @{ room = $room }
  $q3   = DictToQuery $qs3
  if ($u3 -like "*?*") { $u3q = "$u3&$q3" } else { $u3q = "$u3?$q3" }
  $r3   = Fetch-Json -Method "GET" -Url $u3q -TimeoutSec $TimeoutSec
  $file3 = Join-Path $dir "today_details_response.json"
  if ($r3.ok) { Save-Json $file3 $r3.data } else { Save-Json $file3 @{ error=$r3.error; endpoint=$u3q } }

  Add-Content $report "## A3) /api/today_details"
  Add-Content $report ("- detected url: {0}" -f $epDetails.url)
  Add-Content $report ("- saved: {0}" -f (Resolve-Path -Relative $file3))
  Add-Content $report ""
} else {
  Add-Content $report "## A3) /api/today_details"
  Add-Content $report "_not found in calendar_"
  Add-Content $report ""
}

# B) update_time — только шаблон payload
$epUpdate    = Pick-Endpoint $calls "update_time"
$payloadKeys = Guess-UpdateTime-PayloadKeys $calText
$fileUpd     = Join-Path $dir "update_time_request_template.json"
$tpl = [ordered]@{}
foreach ($k in $payloadKeys) { $tpl[$k] = "<fill>" }
if ($tpl.Contains("id"))    { $tpl["id"]    = 123 }
if ($tpl.Contains("start")) { $tpl["start"] = (Get-Date).ToString("yyyy-MM-ddT10:30:00Z") }
if ($tpl.Contains("end"))   { $tpl["end"]   = (Get-Date).ToString("yyyy-MM-ddT10:45:00Z") }
Save-Json $fileUpd $tpl

Add-Content $report "## B) update_time"
if ($epUpdate) {
  Add-Content $report ("- detected url: {0}" -f $epUpdate.url)
  Add-Content $report ("- method guess: {0}" -f $epUpdate.method)
} else {
  Add-Content $report "- endpoint not found in calendar"
}
Add-Content $report ("- request template: {0}" -f (Resolve-Path -Relative $fileUpd))
Add-Content $report "- expected keys:"
foreach ($k in $payloadKeys) { Add-Content $report ("  - {0}" -f $k) }
Add-Content $report ""

Write-Host ("OK -> " + (Resolve-Path -Relative $report))
.url -match ''(?i)room'' ) -or <#
  export_dashboard_api_samples.ps1
  Собирает реальные примеры ответов для панели кабинетов + отчёт.

  Что делает:
  1) Читает templates/calendar.html, вытягивает все "/api/..." URL и рядом пытается угадать метод.
  2) Пытается определить:
     - GET  /api/rooms/status_now
     - POST/GET /api/free_slots (или похожее)
     - GET  /api/today_details?room=...
     - POST /api/appointments/update_time (для запроса — только шаблон payload)
  3) Дёргает API и кладёт результаты в artifacts/rooms_panel:
     - rooms_status_now.json
     - free_slots_request.json / free_slots_response.json
     - today_details_response.json
     - update_time_request_template.json
     - ROOMS_PANEL_API_REPORT.md
#>

param(
  [string]$BaseUrl   = "http://localhost:5000",
  [string]$Calendar  = ".\templates\calendar.html",
  [string]$OutDir    = ".\artifacts\rooms_panel",
  [string]$RoomHint  = "",
  [int]$TimeoutSec   = 10
)

# ---------- helpers ----------
function Ensure-OutDir([string]$p) {
  if (-not (Test-Path $p -PathType Container)) { New-Item -ItemType Directory -Path $p | Out-Null }
}
function Join-Url([string]$base, [string]$path) {
  if ([string]::IsNullOrWhiteSpace($path)) { return $base }
  if ($path -match '^https?://') { return $path }
  $b = $base.TrimEnd('/')
  $u = $path.TrimStart('/')
  return "$b/$u"
}
function Get-LineNum([string]$text, [int]$index) {
  if ($index -lt 0) { return 1 }
  $slice = $text.Substring(0, [Math]::Min($index, $text.Length))
  return ($slice -split "`n").Count
}
function UrlEncode([string]$s) { [System.Uri]::EscapeDataString([string]$s) }
function DictToQuery([hashtable]$d) {
  if (-not $d -or $d.Keys.Count -eq 0) { return "" }
  $pairs = @()
  foreach ($k in $d.Keys) { $pairs += ("{0}={1}" -f (UrlEncode $k), (UrlEncode ([string]$d[$k]))) }
  return ($pairs -join "&")
}
function Save-Json([string]$path, $obj) {
  $json = $obj | ConvertTo-Json -Depth 12
  Set-Content -Path $path -Value $json -Encoding UTF8
}
function Fetch-Json {
  param(
    [ValidateSet("GET","POST","PUT","PATCH","DELETE","HEAD","OPTIONS")]
    [string]$Method,
    [string]$Url,
    [hashtable]$Headers = $null,
    $Body = $null,
    [int]$TimeoutSec = 10
  )
  try {
    $params = @{
      Method      = $Method
      Uri         = $Url
      ErrorAction = "Stop"
    }
    if ($Headers) { $params["Headers"] = $Headers }
    if ($Body -ne $null -and $Method -in @("POST","PUT","PATCH","DELETE")) {
      if ($Body -is [hashtable] -or $Body -is [pscustomobject]) {
        $params["Body"] = ($Body | ConvertTo-Json -Depth 10)
        $params["ContentType"] = "application/json"
      } else {
        $params["Body"] = [string]$Body
      }
    }
    $resp = Invoke-RestMethod @params
    return @{ ok=$true; status=200; data=$resp; error=$null }
  } catch {
    $msg = $_.Exception.Message
    return @{ ok=$false; status=0; data=$null; error=$msg }
  }
}

# Вытащить все "/api/..." URL из файла и угадать метод по контексту
function Extract-ApiCalls([string]$text) {
  $calls = New-Object System.Collections.Generic.List[object]
  # Важно: строка single-quoted с удвоенными одинарными кавычками внутри.
  $rx = [regex]'(?i)[''"](?<url>/api/[^''""]+)[''"]'
  $matches = $rx.Matches($text)
  foreach ($m in $matches) {
    $url = $m.Groups['url'].Value
    $idx = $m.Index
    $line = Get-LineNum $text $idx
    # Контекст ±200 символов
    $s = [Math]::Max(0, $idx - 200)
    $e = [Math]::Min($text.Length, $idx + 200)
    $ctx = $text.Substring($s, $e - $s)
    $method = "GET"
    if ($ctx -match '(?i)axios\.(post|put|patch|delete)\s*\(') { $method = ($Matches[1].ToUpper()) }
    elseif ($ctx -match '(?i)\bmethod\s*:\s*["''](get|post|put|patch|delete|options|head)["'']') { $method = ($Matches[1].ToUpper()) }
    elseif ($ctx -match '(?i)fetch\s*\(' -and $ctx -match '(?i)\bbody\s*:') { $method = "POST" }
    $calls.Add([pscustomobject]@{ url=$url; line=$line; method=$method; ctx=$ctx }) | Out-Null
  }
  # Уникализируем по url+method (берём первый по файлу)
  $uniq = @{}
  $out = @()
  foreach ($c in $calls) {
    $key = $c.url + "|" + $c.method
    if (-not $uniq.ContainsKey($key)) { $uniq[$key] = $true; $out += $c }
  }
  return $out
}

# Подбор эндпоинтов по семантике
function Pick-Endpoint([array]$calls, [string]$kind) {
  $pred = $null
  switch ($kind) {
    "status_now"   { $pred = { ( $_.url -match '(?i)status' -and $_.url -match '(?i)room' ) -or $_.url -match '(?i)/rooms/status' } }
    "free_slots"   { $pred = { $_.url -match '(?i)free.*slot|slot.*free|/slots(\b|/)|/free_slots(\b|/)' } }
    "today_details"{ $pred = { $_.url -match '(?i)today.*detail|detail.*today|/today_details(\b|/)' } }
    "update_time"  { $pred = { $_.url -match '(?i)update[_-]?time' } }
    default        { $pred = { $false } }
  }
  $found = $calls | Where-Object $pred
  if ($found.Count -gt 0) {
    $post = $found | Where-Object { $_.method -eq "POST" } | Select-Object -First 1
    if ($post) { return $post }
    return ($found | Select-Object -First 1)
  }
  return $null
}

# Разбор ожидаемого payload для update_time прямо из кода (ищем JSON.stringify({...}))
function Guess-UpdateTime-PayloadKeys([string]$text) {
  $keys = New-Object System.Collections.Generic.HashSet[string]
  $rx = [regex]'(?is)update[_-]?time.*?JSON\.stringify\s*\(\s*\{(?<obj>[^}]*)\}'
  $m = $rx.Match($text)
  if ($m.Success) {
    $obj = $m.Groups['obj'].Value
    $rxk = [regex]'["''](?<k>[A-Za-z0-9_]+)["'']\s*:'
    foreach ($mm in $rxk.Matches($obj)) { [void]$keys.Add($mm.Groups['k'].Value) }
  } else {
    # запасные часто используемые
    [void]$keys.Add("id")
    [void]$keys.Add("start")
    [void]$keys.Add("end")
    [void]$keys.Add("room")
    [void]$keys.Add("doctor_id")
  }
  return ($keys | Sort-Object)
}

# ---------- main ----------
if (-not (Test-Path $Calendar -PathType Leaf)) {
  Write-Error ("calendar not found: " + $Calendar); exit 1
}
$calText = Get-Content -Path $Calendar -Raw
Ensure-OutDir $OutDir

$ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
$dir = $OutDir
$report = Join-Path $dir "ROOMS_PANEL_API_REPORT.md"
"" | Set-Content -Path $report -Encoding UTF8
Add-Content $report "<!-- GENERATED: $ts -->"
Add-Content $report "# Rooms panel API — autodetected endpoints"
Add-Content $report ""
Add-Content $report ("Source calendar: {0}" -f (Resolve-Path -Relative $Calendar))
Add-Content $report ("BaseUrl: {0}" -f $BaseUrl)
if ($RoomHint) { Add-Content $report ("RoomHint: {0}" -f $RoomHint) }
Add-Content $report ""

$calls = Extract-ApiCalls $calText

# A1) /api/rooms/status_now
$epStatus = Pick-Endpoint $calls "status_now"
if ($epStatus) {
  $url1 = Join-Url $BaseUrl $epStatus.url
  $r1 = Fetch-Json -Method "GET" -Url $url1 -TimeoutSec $TimeoutSec
  $file1 = Join-Path $dir "rooms_status_now.json"
  if ($r1.ok) { Save-Json $file1 $r1.data } else { Save-Json $file1 @{ error=$r1.error; endpoint=$url1 } }
  Add-Content $report "## A1) GET /api/rooms/status_now"
  Add-Content $report ("- detected url: {0}" -f $epStatus.url)
  Add-Content $report ("- method guess: {0}" -f $epStatus.method)
  Add-Content $report ("- saved: {0}" -f (Resolve-Path -Relative $file1))
  Add-Content $report ""
} else {
  Add-Content $report "## A1) /api/rooms/status_now"
  Add-Content $report "_not found in calendar_"
  Add-Content $report ""
}

# A2) /api/free_slots (или подобное)
$epSlots = Pick-Endpoint $calls "free_slots"
if ($epSlots) {
  $room = $RoomHint
  if (-not $room) {
    # попробовать вытащить имя комнаты из HTML
    $mroom = [regex]::Match($calText, '(?i)(id|name)\s*=\s*["'']room(_name)?["''][^>]*value\s*=\s*["'']([^"'']+)["'']')
    if ($mroom.Success) { $room = $mroom.Groups[3].Value }
  }
  if (-not $room) { $room = "Ортопедия" }

  $date = (Get-Date).ToString("yyyy-MM-dd")
  $step = 15

  $uSlotsBase = Join-Url $BaseUrl $epSlots.url
  $qs = @{ room = $room; date = $date; step = $step }
  $qsStr = DictToQuery $qs
  if ($uSlotsBase -like "*?*") { $uSlotsGet = "$uSlotsBase&$qsStr" } else { $uSlotsGet = "$uSlotsBase?$qsStr" }

  $reqBody    = @{ room=$room; date=$date; step=$step }
  $reqHeaders = @{ "Content-Type" = "application/json" }

  $r2 = $null
  if ($epSlots.method -eq "POST") {
    $r2 = Fetch-Json -Method "POST" -Url $uSlotsBase -Body $reqBody -Headers $reqHeaders -TimeoutSec $TimeoutSec
    $reqMethod = "POST"
  } else {
    $tryGet = Fetch-Json -Method "GET" -Url $uSlotsGet -TimeoutSec $TimeoutSec
    if ($tryGet.ok) { $r2 = $tryGet; $reqMethod = "GET" }
    else { $r2 = Fetch-Json -Method "POST" -Url $uSlotsBase -Body $reqBody -Headers $reqHeaders -TimeoutSec $TimeoutSec; $reqMethod = "POST" }
  }

  $fileReq  = Join-Path $dir "free_slots_request.json"
  $fileResp = Join-Path $dir "free_slots_response.json"
  Save-Json $fileReq  @{ url=$uSlotsBase; query=$qs; method=$reqMethod; body=$reqBody }
  if ($r2.ok) { Save-Json $fileResp $r2.data } else { Save-Json $fileResp @{ error=$r2.error; endpoint=$uSlotsBase } }

  Add-Content $report "## A2) /api/free_slots (or similar)"
  Add-Content $report ("- detected url: {0}" -f $epSlots.url)
  Add-Content $report ("- method guess: {0}" -f $epSlots.method)
  Add-Content $report ("- request: {0}" -f (Resolve-Path -Relative $fileReq))
  Add-Content $report ("- response: {0}" -f (Resolve-Path -Relative $fileResp))
  Add-Content $report ""
} else {
  Add-Content $report "## A2) /api/free_slots"
  Add-Content $report "_not found in calendar_"
  Add-Content $report ""
}

# A3) /api/today_details?room=...
$epDetails = Pick-Endpoint $calls "today_details"
if ($epDetails) {
  $room = $RoomHint; if (-not $room) { $room = "Ортопедия" }
  $u3   = Join-Url $BaseUrl $epDetails.url
  $qs3  = @{ room = $room }
  $q3   = DictToQuery $qs3
  if ($u3 -like "*?*") { $u3q = "$u3&$q3" } else { $u3q = "$u3?$q3" }
  $r3   = Fetch-Json -Method "GET" -Url $u3q -TimeoutSec $TimeoutSec
  $file3 = Join-Path $dir "today_details_response.json"
  if ($r3.ok) { Save-Json $file3 $r3.data } else { Save-Json $file3 @{ error=$r3.error; endpoint=$u3q } }

  Add-Content $report "## A3) /api/today_details"
  Add-Content $report ("- detected url: {0}" -f $epDetails.url)
  Add-Content $report ("- saved: {0}" -f (Resolve-Path -Relative $file3))
  Add-Content $report ""
} else {
  Add-Content $report "## A3) /api/today_details"
  Add-Content $report "_not found in calendar_"
  Add-Content $report ""
}

# B) update_time — только шаблон payload
$epUpdate    = Pick-Endpoint $calls "update_time"
$payloadKeys = Guess-UpdateTime-PayloadKeys $calText
$fileUpd     = Join-Path $dir "update_time_request_template.json"
$tpl = [ordered]@{}
foreach ($k in $payloadKeys) { $tpl[$k] = "<fill>" }
if ($tpl.Contains("id"))    { $tpl["id"]    = 123 }
if ($tpl.Contains("start")) { $tpl["start"] = (Get-Date).ToString("yyyy-MM-ddT10:30:00Z") }
if ($tpl.Contains("end"))   { $tpl["end"]   = (Get-Date).ToString("yyyy-MM-ddT10:45:00Z") }
Save-Json $fileUpd $tpl

Add-Content $report "## B) update_time"
if ($epUpdate) {
  Add-Content $report ("- detected url: {0}" -f $epUpdate.url)
  Add-Content $report ("- method guess: {0}" -f $epUpdate.method)
} else {
  Add-Content $report "- endpoint not found in calendar"
}
Add-Content $report ("- request template: {0}" -f (Resolve-Path -Relative $fileUpd))
Add-Content $report "- expected keys:"
foreach ($k in $payloadKeys) { Add-Content $report ("  - {0}" -f $k) }
Add-Content $report ""

Write-Host ("OK -> " + (Resolve-Path -Relative $report))
.url -match ''(?i)/rooms/status'' } }
    "free_slots"   { $pred = { <#
  export_dashboard_api_samples.ps1
  Собирает реальные примеры ответов для панели кабинетов + отчёт.

  Что делает:
  1) Читает templates/calendar.html, вытягивает все "/api/..." URL и рядом пытается угадать метод.
  2) Пытается определить:
     - GET  /api/rooms/status_now
     - POST/GET /api/free_slots (или похожее)
     - GET  /api/today_details?room=...
     - POST /api/appointments/update_time (для запроса — только шаблон payload)
  3) Дёргает API и кладёт результаты в artifacts/rooms_panel:
     - rooms_status_now.json
     - free_slots_request.json / free_slots_response.json
     - today_details_response.json
     - update_time_request_template.json
     - ROOMS_PANEL_API_REPORT.md
#>

param(
  [string]$BaseUrl   = "http://localhost:5000",
  [string]$Calendar  = ".\templates\calendar.html",
  [string]$OutDir    = ".\artifacts\rooms_panel",
  [string]$RoomHint  = "",
  [int]$TimeoutSec   = 10
)

# ---------- helpers ----------
function Ensure-OutDir([string]$p) {
  if (-not (Test-Path $p -PathType Container)) { New-Item -ItemType Directory -Path $p | Out-Null }
}
function Join-Url([string]$base, [string]$path) {
  if ([string]::IsNullOrWhiteSpace($path)) { return $base }
  if ($path -match '^https?://') { return $path }
  $b = $base.TrimEnd('/')
  $u = $path.TrimStart('/')
  return "$b/$u"
}
function Get-LineNum([string]$text, [int]$index) {
  if ($index -lt 0) { return 1 }
  $slice = $text.Substring(0, [Math]::Min($index, $text.Length))
  return ($slice -split "`n").Count
}
function UrlEncode([string]$s) { [System.Uri]::EscapeDataString([string]$s) }
function DictToQuery([hashtable]$d) {
  if (-not $d -or $d.Keys.Count -eq 0) { return "" }
  $pairs = @()
  foreach ($k in $d.Keys) { $pairs += ("{0}={1}" -f (UrlEncode $k), (UrlEncode ([string]$d[$k]))) }
  return ($pairs -join "&")
}
function Save-Json([string]$path, $obj) {
  $json = $obj | ConvertTo-Json -Depth 12
  Set-Content -Path $path -Value $json -Encoding UTF8
}
function Fetch-Json {
  param(
    [ValidateSet("GET","POST","PUT","PATCH","DELETE","HEAD","OPTIONS")]
    [string]$Method,
    [string]$Url,
    [hashtable]$Headers = $null,
    $Body = $null,
    [int]$TimeoutSec = 10
  )
  try {
    $params = @{
      Method      = $Method
      Uri         = $Url
      ErrorAction = "Stop"
    }
    if ($Headers) { $params["Headers"] = $Headers }
    if ($Body -ne $null -and $Method -in @("POST","PUT","PATCH","DELETE")) {
      if ($Body -is [hashtable] -or $Body -is [pscustomobject]) {
        $params["Body"] = ($Body | ConvertTo-Json -Depth 10)
        $params["ContentType"] = "application/json"
      } else {
        $params["Body"] = [string]$Body
      }
    }
    $resp = Invoke-RestMethod @params
    return @{ ok=$true; status=200; data=$resp; error=$null }
  } catch {
    $msg = $_.Exception.Message
    return @{ ok=$false; status=0; data=$null; error=$msg }
  }
}

# Вытащить все "/api/..." URL из файла и угадать метод по контексту
function Extract-ApiCalls([string]$text) {
  $calls = New-Object System.Collections.Generic.List[object]
  # Важно: строка single-quoted с удвоенными одинарными кавычками внутри.
  $rx = [regex]'(?i)[''"](?<url>/api/[^''""]+)[''"]'
  $matches = $rx.Matches($text)
  foreach ($m in $matches) {
    $url = $m.Groups['url'].Value
    $idx = $m.Index
    $line = Get-LineNum $text $idx
    # Контекст ±200 символов
    $s = [Math]::Max(0, $idx - 200)
    $e = [Math]::Min($text.Length, $idx + 200)
    $ctx = $text.Substring($s, $e - $s)
    $method = "GET"
    if ($ctx -match '(?i)axios\.(post|put|patch|delete)\s*\(') { $method = ($Matches[1].ToUpper()) }
    elseif ($ctx -match '(?i)\bmethod\s*:\s*["''](get|post|put|patch|delete|options|head)["'']') { $method = ($Matches[1].ToUpper()) }
    elseif ($ctx -match '(?i)fetch\s*\(' -and $ctx -match '(?i)\bbody\s*:') { $method = "POST" }
    $calls.Add([pscustomobject]@{ url=$url; line=$line; method=$method; ctx=$ctx }) | Out-Null
  }
  # Уникализируем по url+method (берём первый по файлу)
  $uniq = @{}
  $out = @()
  foreach ($c in $calls) {
    $key = $c.url + "|" + $c.method
    if (-not $uniq.ContainsKey($key)) { $uniq[$key] = $true; $out += $c }
  }
  return $out
}

# Подбор эндпоинтов по семантике
function Pick-Endpoint([array]$calls, [string]$kind) {
  $pred = $null
  switch ($kind) {
    "status_now"   { $pred = { ( $_.url -match '(?i)status' -and $_.url -match '(?i)room' ) -or $_.url -match '(?i)/rooms/status' } }
    "free_slots"   { $pred = { $_.url -match '(?i)free.*slot|slot.*free|/slots(\b|/)|/free_slots(\b|/)' } }
    "today_details"{ $pred = { $_.url -match '(?i)today.*detail|detail.*today|/today_details(\b|/)' } }
    "update_time"  { $pred = { $_.url -match '(?i)update[_-]?time' } }
    default        { $pred = { $false } }
  }
  $found = $calls | Where-Object $pred
  if ($found.Count -gt 0) {
    $post = $found | Where-Object { $_.method -eq "POST" } | Select-Object -First 1
    if ($post) { return $post }
    return ($found | Select-Object -First 1)
  }
  return $null
}

# Разбор ожидаемого payload для update_time прямо из кода (ищем JSON.stringify({...}))
function Guess-UpdateTime-PayloadKeys([string]$text) {
  $keys = New-Object System.Collections.Generic.HashSet[string]
  $rx = [regex]'(?is)update[_-]?time.*?JSON\.stringify\s*\(\s*\{(?<obj>[^}]*)\}'
  $m = $rx.Match($text)
  if ($m.Success) {
    $obj = $m.Groups['obj'].Value
    $rxk = [regex]'["''](?<k>[A-Za-z0-9_]+)["'']\s*:'
    foreach ($mm in $rxk.Matches($obj)) { [void]$keys.Add($mm.Groups['k'].Value) }
  } else {
    # запасные часто используемые
    [void]$keys.Add("id")
    [void]$keys.Add("start")
    [void]$keys.Add("end")
    [void]$keys.Add("room")
    [void]$keys.Add("doctor_id")
  }
  return ($keys | Sort-Object)
}

# ---------- main ----------
if (-not (Test-Path $Calendar -PathType Leaf)) {
  Write-Error ("calendar not found: " + $Calendar); exit 1
}
$calText = Get-Content -Path $Calendar -Raw
Ensure-OutDir $OutDir

$ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
$dir = $OutDir
$report = Join-Path $dir "ROOMS_PANEL_API_REPORT.md"
"" | Set-Content -Path $report -Encoding UTF8
Add-Content $report "<!-- GENERATED: $ts -->"
Add-Content $report "# Rooms panel API — autodetected endpoints"
Add-Content $report ""
Add-Content $report ("Source calendar: {0}" -f (Resolve-Path -Relative $Calendar))
Add-Content $report ("BaseUrl: {0}" -f $BaseUrl)
if ($RoomHint) { Add-Content $report ("RoomHint: {0}" -f $RoomHint) }
Add-Content $report ""

$calls = Extract-ApiCalls $calText

# A1) /api/rooms/status_now
$epStatus = Pick-Endpoint $calls "status_now"
if ($epStatus) {
  $url1 = Join-Url $BaseUrl $epStatus.url
  $r1 = Fetch-Json -Method "GET" -Url $url1 -TimeoutSec $TimeoutSec
  $file1 = Join-Path $dir "rooms_status_now.json"
  if ($r1.ok) { Save-Json $file1 $r1.data } else { Save-Json $file1 @{ error=$r1.error; endpoint=$url1 } }
  Add-Content $report "## A1) GET /api/rooms/status_now"
  Add-Content $report ("- detected url: {0}" -f $epStatus.url)
  Add-Content $report ("- method guess: {0}" -f $epStatus.method)
  Add-Content $report ("- saved: {0}" -f (Resolve-Path -Relative $file1))
  Add-Content $report ""
} else {
  Add-Content $report "## A1) /api/rooms/status_now"
  Add-Content $report "_not found in calendar_"
  Add-Content $report ""
}

# A2) /api/free_slots (или подобное)
$epSlots = Pick-Endpoint $calls "free_slots"
if ($epSlots) {
  $room = $RoomHint
  if (-not $room) {
    # попробовать вытащить имя комнаты из HTML
    $mroom = [regex]::Match($calText, '(?i)(id|name)\s*=\s*["'']room(_name)?["''][^>]*value\s*=\s*["'']([^"'']+)["'']')
    if ($mroom.Success) { $room = $mroom.Groups[3].Value }
  }
  if (-not $room) { $room = "Ортопедия" }

  $date = (Get-Date).ToString("yyyy-MM-dd")
  $step = 15

  $uSlotsBase = Join-Url $BaseUrl $epSlots.url
  $qs = @{ room = $room; date = $date; step = $step }
  $qsStr = DictToQuery $qs
  if ($uSlotsBase -like "*?*") { $uSlotsGet = "$uSlotsBase&$qsStr" } else { $uSlotsGet = "$uSlotsBase?$qsStr" }

  $reqBody    = @{ room=$room; date=$date; step=$step }
  $reqHeaders = @{ "Content-Type" = "application/json" }

  $r2 = $null
  if ($epSlots.method -eq "POST") {
    $r2 = Fetch-Json -Method "POST" -Url $uSlotsBase -Body $reqBody -Headers $reqHeaders -TimeoutSec $TimeoutSec
    $reqMethod = "POST"
  } else {
    $tryGet = Fetch-Json -Method "GET" -Url $uSlotsGet -TimeoutSec $TimeoutSec
    if ($tryGet.ok) { $r2 = $tryGet; $reqMethod = "GET" }
    else { $r2 = Fetch-Json -Method "POST" -Url $uSlotsBase -Body $reqBody -Headers $reqHeaders -TimeoutSec $TimeoutSec; $reqMethod = "POST" }
  }

  $fileReq  = Join-Path $dir "free_slots_request.json"
  $fileResp = Join-Path $dir "free_slots_response.json"
  Save-Json $fileReq  @{ url=$uSlotsBase; query=$qs; method=$reqMethod; body=$reqBody }
  if ($r2.ok) { Save-Json $fileResp $r2.data } else { Save-Json $fileResp @{ error=$r2.error; endpoint=$uSlotsBase } }

  Add-Content $report "## A2) /api/free_slots (or similar)"
  Add-Content $report ("- detected url: {0}" -f $epSlots.url)
  Add-Content $report ("- method guess: {0}" -f $epSlots.method)
  Add-Content $report ("- request: {0}" -f (Resolve-Path -Relative $fileReq))
  Add-Content $report ("- response: {0}" -f (Resolve-Path -Relative $fileResp))
  Add-Content $report ""
} else {
  Add-Content $report "## A2) /api/free_slots"
  Add-Content $report "_not found in calendar_"
  Add-Content $report ""
}

# A3) /api/today_details?room=...
$epDetails = Pick-Endpoint $calls "today_details"
if ($epDetails) {
  $room = $RoomHint; if (-not $room) { $room = "Ортопедия" }
  $u3   = Join-Url $BaseUrl $epDetails.url
  $qs3  = @{ room = $room }
  $q3   = DictToQuery $qs3
  if ($u3 -like "*?*") { $u3q = "$u3&$q3" } else { $u3q = "$u3?$q3" }
  $r3   = Fetch-Json -Method "GET" -Url $u3q -TimeoutSec $TimeoutSec
  $file3 = Join-Path $dir "today_details_response.json"
  if ($r3.ok) { Save-Json $file3 $r3.data } else { Save-Json $file3 @{ error=$r3.error; endpoint=$u3q } }

  Add-Content $report "## A3) /api/today_details"
  Add-Content $report ("- detected url: {0}" -f $epDetails.url)
  Add-Content $report ("- saved: {0}" -f (Resolve-Path -Relative $file3))
  Add-Content $report ""
} else {
  Add-Content $report "## A3) /api/today_details"
  Add-Content $report "_not found in calendar_"
  Add-Content $report ""
}

# B) update_time — только шаблон payload
$epUpdate    = Pick-Endpoint $calls "update_time"
$payloadKeys = Guess-UpdateTime-PayloadKeys $calText
$fileUpd     = Join-Path $dir "update_time_request_template.json"
$tpl = [ordered]@{}
foreach ($k in $payloadKeys) { $tpl[$k] = "<fill>" }
if ($tpl.Contains("id"))    { $tpl["id"]    = 123 }
if ($tpl.Contains("start")) { $tpl["start"] = (Get-Date).ToString("yyyy-MM-ddT10:30:00Z") }
if ($tpl.Contains("end"))   { $tpl["end"]   = (Get-Date).ToString("yyyy-MM-ddT10:45:00Z") }
Save-Json $fileUpd $tpl

Add-Content $report "## B) update_time"
if ($epUpdate) {
  Add-Content $report ("- detected url: {0}" -f $epUpdate.url)
  Add-Content $report ("- method guess: {0}" -f $epUpdate.method)
} else {
  Add-Content $report "- endpoint not found in calendar"
}
Add-Content $report ("- request template: {0}" -f (Resolve-Path -Relative $fileUpd))
Add-Content $report "- expected keys:"
foreach ($k in $payloadKeys) { Add-Content $report ("  - {0}" -f $k) }
Add-Content $report ""

Write-Host ("OK -> " + (Resolve-Path -Relative $report))
.url -match ''(?i)free.*slot|slot.*free|/slots(\b|/)|/free_slots(\b|/)'' } }
    "today_details"{ $pred = { <#
  export_dashboard_api_samples.ps1
  Собирает реальные примеры ответов для панели кабинетов + отчёт.

  Что делает:
  1) Читает templates/calendar.html, вытягивает все "/api/..." URL и рядом пытается угадать метод.
  2) Пытается определить:
     - GET  /api/rooms/status_now
     - POST/GET /api/free_slots (или похожее)
     - GET  /api/today_details?room=...
     - POST /api/appointments/update_time (для запроса — только шаблон payload)
  3) Дёргает API и кладёт результаты в artifacts/rooms_panel:
     - rooms_status_now.json
     - free_slots_request.json / free_slots_response.json
     - today_details_response.json
     - update_time_request_template.json
     - ROOMS_PANEL_API_REPORT.md
#>

param(
  [string]$BaseUrl   = "http://localhost:5000",
  [string]$Calendar  = ".\templates\calendar.html",
  [string]$OutDir    = ".\artifacts\rooms_panel",
  [string]$RoomHint  = "",
  [int]$TimeoutSec   = 10
)

# ---------- helpers ----------
function Ensure-OutDir([string]$p) {
  if (-not (Test-Path $p -PathType Container)) { New-Item -ItemType Directory -Path $p | Out-Null }
}
function Join-Url([string]$base, [string]$path) {
  if ([string]::IsNullOrWhiteSpace($path)) { return $base }
  if ($path -match '^https?://') { return $path }
  $b = $base.TrimEnd('/')
  $u = $path.TrimStart('/')
  return "$b/$u"
}
function Get-LineNum([string]$text, [int]$index) {
  if ($index -lt 0) { return 1 }
  $slice = $text.Substring(0, [Math]::Min($index, $text.Length))
  return ($slice -split "`n").Count
}
function UrlEncode([string]$s) { [System.Uri]::EscapeDataString([string]$s) }
function DictToQuery([hashtable]$d) {
  if (-not $d -or $d.Keys.Count -eq 0) { return "" }
  $pairs = @()
  foreach ($k in $d.Keys) { $pairs += ("{0}={1}" -f (UrlEncode $k), (UrlEncode ([string]$d[$k]))) }
  return ($pairs -join "&")
}
function Save-Json([string]$path, $obj) {
  $json = $obj | ConvertTo-Json -Depth 12
  Set-Content -Path $path -Value $json -Encoding UTF8
}
function Fetch-Json {
  param(
    [ValidateSet("GET","POST","PUT","PATCH","DELETE","HEAD","OPTIONS")]
    [string]$Method,
    [string]$Url,
    [hashtable]$Headers = $null,
    $Body = $null,
    [int]$TimeoutSec = 10
  )
  try {
    $params = @{
      Method      = $Method
      Uri         = $Url
      ErrorAction = "Stop"
    }
    if ($Headers) { $params["Headers"] = $Headers }
    if ($Body -ne $null -and $Method -in @("POST","PUT","PATCH","DELETE")) {
      if ($Body -is [hashtable] -or $Body -is [pscustomobject]) {
        $params["Body"] = ($Body | ConvertTo-Json -Depth 10)
        $params["ContentType"] = "application/json"
      } else {
        $params["Body"] = [string]$Body
      }
    }
    $resp = Invoke-RestMethod @params
    return @{ ok=$true; status=200; data=$resp; error=$null }
  } catch {
    $msg = $_.Exception.Message
    return @{ ok=$false; status=0; data=$null; error=$msg }
  }
}

# Вытащить все "/api/..." URL из файла и угадать метод по контексту
function Extract-ApiCalls([string]$text) {
  $calls = New-Object System.Collections.Generic.List[object]
  # Важно: строка single-quoted с удвоенными одинарными кавычками внутри.
  $rx = [regex]'(?i)[''"](?<url>/api/[^''""]+)[''"]'
  $matches = $rx.Matches($text)
  foreach ($m in $matches) {
    $url = $m.Groups['url'].Value
    $idx = $m.Index
    $line = Get-LineNum $text $idx
    # Контекст ±200 символов
    $s = [Math]::Max(0, $idx - 200)
    $e = [Math]::Min($text.Length, $idx + 200)
    $ctx = $text.Substring($s, $e - $s)
    $method = "GET"
    if ($ctx -match '(?i)axios\.(post|put|patch|delete)\s*\(') { $method = ($Matches[1].ToUpper()) }
    elseif ($ctx -match '(?i)\bmethod\s*:\s*["''](get|post|put|patch|delete|options|head)["'']') { $method = ($Matches[1].ToUpper()) }
    elseif ($ctx -match '(?i)fetch\s*\(' -and $ctx -match '(?i)\bbody\s*:') { $method = "POST" }
    $calls.Add([pscustomobject]@{ url=$url; line=$line; method=$method; ctx=$ctx }) | Out-Null
  }
  # Уникализируем по url+method (берём первый по файлу)
  $uniq = @{}
  $out = @()
  foreach ($c in $calls) {
    $key = $c.url + "|" + $c.method
    if (-not $uniq.ContainsKey($key)) { $uniq[$key] = $true; $out += $c }
  }
  return $out
}

# Подбор эндпоинтов по семантике
function Pick-Endpoint([array]$calls, [string]$kind) {
  $pred = $null
  switch ($kind) {
    "status_now"   { $pred = { ( $_.url -match '(?i)status' -and $_.url -match '(?i)room' ) -or $_.url -match '(?i)/rooms/status' } }
    "free_slots"   { $pred = { $_.url -match '(?i)free.*slot|slot.*free|/slots(\b|/)|/free_slots(\b|/)' } }
    "today_details"{ $pred = { $_.url -match '(?i)today.*detail|detail.*today|/today_details(\b|/)' } }
    "update_time"  { $pred = { $_.url -match '(?i)update[_-]?time' } }
    default        { $pred = { $false } }
  }
  $found = $calls | Where-Object $pred
  if ($found.Count -gt 0) {
    $post = $found | Where-Object { $_.method -eq "POST" } | Select-Object -First 1
    if ($post) { return $post }
    return ($found | Select-Object -First 1)
  }
  return $null
}

# Разбор ожидаемого payload для update_time прямо из кода (ищем JSON.stringify({...}))
function Guess-UpdateTime-PayloadKeys([string]$text) {
  $keys = New-Object System.Collections.Generic.HashSet[string]
  $rx = [regex]'(?is)update[_-]?time.*?JSON\.stringify\s*\(\s*\{(?<obj>[^}]*)\}'
  $m = $rx.Match($text)
  if ($m.Success) {
    $obj = $m.Groups['obj'].Value
    $rxk = [regex]'["''](?<k>[A-Za-z0-9_]+)["'']\s*:'
    foreach ($mm in $rxk.Matches($obj)) { [void]$keys.Add($mm.Groups['k'].Value) }
  } else {
    # запасные часто используемые
    [void]$keys.Add("id")
    [void]$keys.Add("start")
    [void]$keys.Add("end")
    [void]$keys.Add("room")
    [void]$keys.Add("doctor_id")
  }
  return ($keys | Sort-Object)
}

# ---------- main ----------
if (-not (Test-Path $Calendar -PathType Leaf)) {
  Write-Error ("calendar not found: " + $Calendar); exit 1
}
$calText = Get-Content -Path $Calendar -Raw
Ensure-OutDir $OutDir

$ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
$dir = $OutDir
$report = Join-Path $dir "ROOMS_PANEL_API_REPORT.md"
"" | Set-Content -Path $report -Encoding UTF8
Add-Content $report "<!-- GENERATED: $ts -->"
Add-Content $report "# Rooms panel API — autodetected endpoints"
Add-Content $report ""
Add-Content $report ("Source calendar: {0}" -f (Resolve-Path -Relative $Calendar))
Add-Content $report ("BaseUrl: {0}" -f $BaseUrl)
if ($RoomHint) { Add-Content $report ("RoomHint: {0}" -f $RoomHint) }
Add-Content $report ""

$calls = Extract-ApiCalls $calText

# A1) /api/rooms/status_now
$epStatus = Pick-Endpoint $calls "status_now"
if ($epStatus) {
  $url1 = Join-Url $BaseUrl $epStatus.url
  $r1 = Fetch-Json -Method "GET" -Url $url1 -TimeoutSec $TimeoutSec
  $file1 = Join-Path $dir "rooms_status_now.json"
  if ($r1.ok) { Save-Json $file1 $r1.data } else { Save-Json $file1 @{ error=$r1.error; endpoint=$url1 } }
  Add-Content $report "## A1) GET /api/rooms/status_now"
  Add-Content $report ("- detected url: {0}" -f $epStatus.url)
  Add-Content $report ("- method guess: {0}" -f $epStatus.method)
  Add-Content $report ("- saved: {0}" -f (Resolve-Path -Relative $file1))
  Add-Content $report ""
} else {
  Add-Content $report "## A1) /api/rooms/status_now"
  Add-Content $report "_not found in calendar_"
  Add-Content $report ""
}

# A2) /api/free_slots (или подобное)
$epSlots = Pick-Endpoint $calls "free_slots"
if ($epSlots) {
  $room = $RoomHint
  if (-not $room) {
    # попробовать вытащить имя комнаты из HTML
    $mroom = [regex]::Match($calText, '(?i)(id|name)\s*=\s*["'']room(_name)?["''][^>]*value\s*=\s*["'']([^"'']+)["'']')
    if ($mroom.Success) { $room = $mroom.Groups[3].Value }
  }
  if (-not $room) { $room = "Ортопедия" }

  $date = (Get-Date).ToString("yyyy-MM-dd")
  $step = 15

  $uSlotsBase = Join-Url $BaseUrl $epSlots.url
  $qs = @{ room = $room; date = $date; step = $step }
  $qsStr = DictToQuery $qs
  if ($uSlotsBase -like "*?*") { $uSlotsGet = "$uSlotsBase&$qsStr" } else { $uSlotsGet = "$uSlotsBase?$qsStr" }

  $reqBody    = @{ room=$room; date=$date; step=$step }
  $reqHeaders = @{ "Content-Type" = "application/json" }

  $r2 = $null
  if ($epSlots.method -eq "POST") {
    $r2 = Fetch-Json -Method "POST" -Url $uSlotsBase -Body $reqBody -Headers $reqHeaders -TimeoutSec $TimeoutSec
    $reqMethod = "POST"
  } else {
    $tryGet = Fetch-Json -Method "GET" -Url $uSlotsGet -TimeoutSec $TimeoutSec
    if ($tryGet.ok) { $r2 = $tryGet; $reqMethod = "GET" }
    else { $r2 = Fetch-Json -Method "POST" -Url $uSlotsBase -Body $reqBody -Headers $reqHeaders -TimeoutSec $TimeoutSec; $reqMethod = "POST" }
  }

  $fileReq  = Join-Path $dir "free_slots_request.json"
  $fileResp = Join-Path $dir "free_slots_response.json"
  Save-Json $fileReq  @{ url=$uSlotsBase; query=$qs; method=$reqMethod; body=$reqBody }
  if ($r2.ok) { Save-Json $fileResp $r2.data } else { Save-Json $fileResp @{ error=$r2.error; endpoint=$uSlotsBase } }

  Add-Content $report "## A2) /api/free_slots (or similar)"
  Add-Content $report ("- detected url: {0}" -f $epSlots.url)
  Add-Content $report ("- method guess: {0}" -f $epSlots.method)
  Add-Content $report ("- request: {0}" -f (Resolve-Path -Relative $fileReq))
  Add-Content $report ("- response: {0}" -f (Resolve-Path -Relative $fileResp))
  Add-Content $report ""
} else {
  Add-Content $report "## A2) /api/free_slots"
  Add-Content $report "_not found in calendar_"
  Add-Content $report ""
}

# A3) /api/today_details?room=...
$epDetails = Pick-Endpoint $calls "today_details"
if ($epDetails) {
  $room = $RoomHint; if (-not $room) { $room = "Ортопедия" }
  $u3   = Join-Url $BaseUrl $epDetails.url
  $qs3  = @{ room = $room }
  $q3   = DictToQuery $qs3
  if ($u3 -like "*?*") { $u3q = "$u3&$q3" } else { $u3q = "$u3?$q3" }
  $r3   = Fetch-Json -Method "GET" -Url $u3q -TimeoutSec $TimeoutSec
  $file3 = Join-Path $dir "today_details_response.json"
  if ($r3.ok) { Save-Json $file3 $r3.data } else { Save-Json $file3 @{ error=$r3.error; endpoint=$u3q } }

  Add-Content $report "## A3) /api/today_details"
  Add-Content $report ("- detected url: {0}" -f $epDetails.url)
  Add-Content $report ("- saved: {0}" -f (Resolve-Path -Relative $file3))
  Add-Content $report ""
} else {
  Add-Content $report "## A3) /api/today_details"
  Add-Content $report "_not found in calendar_"
  Add-Content $report ""
}

# B) update_time — только шаблон payload
$epUpdate    = Pick-Endpoint $calls "update_time"
$payloadKeys = Guess-UpdateTime-PayloadKeys $calText
$fileUpd     = Join-Path $dir "update_time_request_template.json"
$tpl = [ordered]@{}
foreach ($k in $payloadKeys) { $tpl[$k] = "<fill>" }
if ($tpl.Contains("id"))    { $tpl["id"]    = 123 }
if ($tpl.Contains("start")) { $tpl["start"] = (Get-Date).ToString("yyyy-MM-ddT10:30:00Z") }
if ($tpl.Contains("end"))   { $tpl["end"]   = (Get-Date).ToString("yyyy-MM-ddT10:45:00Z") }
Save-Json $fileUpd $tpl

Add-Content $report "## B) update_time"
if ($epUpdate) {
  Add-Content $report ("- detected url: {0}" -f $epUpdate.url)
  Add-Content $report ("- method guess: {0}" -f $epUpdate.method)
} else {
  Add-Content $report "- endpoint not found in calendar"
}
Add-Content $report ("- request template: {0}" -f (Resolve-Path -Relative $fileUpd))
Add-Content $report "- expected keys:"
foreach ($k in $payloadKeys) { Add-Content $report ("  - {0}" -f $k) }
Add-Content $report ""

Write-Host ("OK -> " + (Resolve-Path -Relative $report))
.url -match ''(?i)today.*detail|detail.*today|/today_details(\b|/)'' } }
    "update_time"  { $pred = { <#
  export_dashboard_api_samples.ps1
  Собирает реальные примеры ответов для панели кабинетов + отчёт.

  Что делает:
  1) Читает templates/calendar.html, вытягивает все "/api/..." URL и рядом пытается угадать метод.
  2) Пытается определить:
     - GET  /api/rooms/status_now
     - POST/GET /api/free_slots (или похожее)
     - GET  /api/today_details?room=...
     - POST /api/appointments/update_time (для запроса — только шаблон payload)
  3) Дёргает API и кладёт результаты в artifacts/rooms_panel:
     - rooms_status_now.json
     - free_slots_request.json / free_slots_response.json
     - today_details_response.json
     - update_time_request_template.json
     - ROOMS_PANEL_API_REPORT.md
#>

param(
  [string]$BaseUrl   = "http://localhost:5000",
  [string]$Calendar  = ".\templates\calendar.html",
  [string]$OutDir    = ".\artifacts\rooms_panel",
  [string]$RoomHint  = "",
  [int]$TimeoutSec   = 10
)

# ---------- helpers ----------
function Ensure-OutDir([string]$p) {
  if (-not (Test-Path $p -PathType Container)) { New-Item -ItemType Directory -Path $p | Out-Null }
}
function Join-Url([string]$base, [string]$path) {
  if ([string]::IsNullOrWhiteSpace($path)) { return $base }
  if ($path -match '^https?://') { return $path }
  $b = $base.TrimEnd('/')
  $u = $path.TrimStart('/')
  return "$b/$u"
}
function Get-LineNum([string]$text, [int]$index) {
  if ($index -lt 0) { return 1 }
  $slice = $text.Substring(0, [Math]::Min($index, $text.Length))
  return ($slice -split "`n").Count
}
function UrlEncode([string]$s) { [System.Uri]::EscapeDataString([string]$s) }
function DictToQuery([hashtable]$d) {
  if (-not $d -or $d.Keys.Count -eq 0) { return "" }
  $pairs = @()
  foreach ($k in $d.Keys) { $pairs += ("{0}={1}" -f (UrlEncode $k), (UrlEncode ([string]$d[$k]))) }
  return ($pairs -join "&")
}
function Save-Json([string]$path, $obj) {
  $json = $obj | ConvertTo-Json -Depth 12
  Set-Content -Path $path -Value $json -Encoding UTF8
}
function Fetch-Json {
  param(
    [ValidateSet("GET","POST","PUT","PATCH","DELETE","HEAD","OPTIONS")]
    [string]$Method,
    [string]$Url,
    [hashtable]$Headers = $null,
    $Body = $null,
    [int]$TimeoutSec = 10
  )
  try {
    $params = @{
      Method      = $Method
      Uri         = $Url
      ErrorAction = "Stop"
    }
    if ($Headers) { $params["Headers"] = $Headers }
    if ($Body -ne $null -and $Method -in @("POST","PUT","PATCH","DELETE")) {
      if ($Body -is [hashtable] -or $Body -is [pscustomobject]) {
        $params["Body"] = ($Body | ConvertTo-Json -Depth 10)
        $params["ContentType"] = "application/json"
      } else {
        $params["Body"] = [string]$Body
      }
    }
    $resp = Invoke-RestMethod @params
    return @{ ok=$true; status=200; data=$resp; error=$null }
  } catch {
    $msg = $_.Exception.Message
    return @{ ok=$false; status=0; data=$null; error=$msg }
  }
}

# Вытащить все "/api/..." URL из файла и угадать метод по контексту
function Extract-ApiCalls([string]$text) {
  $calls = New-Object System.Collections.Generic.List[object]
  # Важно: строка single-quoted с удвоенными одинарными кавычками внутри.
  $rx = [regex]'(?i)[''"](?<url>/api/[^''""]+)[''"]'
  $matches = $rx.Matches($text)
  foreach ($m in $matches) {
    $url = $m.Groups['url'].Value
    $idx = $m.Index
    $line = Get-LineNum $text $idx
    # Контекст ±200 символов
    $s = [Math]::Max(0, $idx - 200)
    $e = [Math]::Min($text.Length, $idx + 200)
    $ctx = $text.Substring($s, $e - $s)
    $method = "GET"
    if ($ctx -match '(?i)axios\.(post|put|patch|delete)\s*\(') { $method = ($Matches[1].ToUpper()) }
    elseif ($ctx -match '(?i)\bmethod\s*:\s*["''](get|post|put|patch|delete|options|head)["'']') { $method = ($Matches[1].ToUpper()) }
    elseif ($ctx -match '(?i)fetch\s*\(' -and $ctx -match '(?i)\bbody\s*:') { $method = "POST" }
    $calls.Add([pscustomobject]@{ url=$url; line=$line; method=$method; ctx=$ctx }) | Out-Null
  }
  # Уникализируем по url+method (берём первый по файлу)
  $uniq = @{}
  $out = @()
  foreach ($c in $calls) {
    $key = $c.url + "|" + $c.method
    if (-not $uniq.ContainsKey($key)) { $uniq[$key] = $true; $out += $c }
  }
  return $out
}

# Подбор эндпоинтов по семантике
function Pick-Endpoint([array]$calls, [string]$kind) {
  $pred = $null
  switch ($kind) {
    "status_now"   { $pred = { ( $_.url -match '(?i)status' -and $_.url -match '(?i)room' ) -or $_.url -match '(?i)/rooms/status' } }
    "free_slots"   { $pred = { $_.url -match '(?i)free.*slot|slot.*free|/slots(\b|/)|/free_slots(\b|/)' } }
    "today_details"{ $pred = { $_.url -match '(?i)today.*detail|detail.*today|/today_details(\b|/)' } }
    "update_time"  { $pred = { $_.url -match '(?i)update[_-]?time' } }
    default        { $pred = { $false } }
  }
  $found = $calls | Where-Object $pred
  if ($found.Count -gt 0) {
    $post = $found | Where-Object { $_.method -eq "POST" } | Select-Object -First 1
    if ($post) { return $post }
    return ($found | Select-Object -First 1)
  }
  return $null
}

# Разбор ожидаемого payload для update_time прямо из кода (ищем JSON.stringify({...}))
function Guess-UpdateTime-PayloadKeys([string]$text) {
  $keys = New-Object System.Collections.Generic.HashSet[string]
  $rx = [regex]'(?is)update[_-]?time.*?JSON\.stringify\s*\(\s*\{(?<obj>[^}]*)\}'
  $m = $rx.Match($text)
  if ($m.Success) {
    $obj = $m.Groups['obj'].Value
    $rxk = [regex]'["''](?<k>[A-Za-z0-9_]+)["'']\s*:'
    foreach ($mm in $rxk.Matches($obj)) { [void]$keys.Add($mm.Groups['k'].Value) }
  } else {
    # запасные часто используемые
    [void]$keys.Add("id")
    [void]$keys.Add("start")
    [void]$keys.Add("end")
    [void]$keys.Add("room")
    [void]$keys.Add("doctor_id")
  }
  return ($keys | Sort-Object)
}

# ---------- main ----------
if (-not (Test-Path $Calendar -PathType Leaf)) {
  Write-Error ("calendar not found: " + $Calendar); exit 1
}
$calText = Get-Content -Path $Calendar -Raw
Ensure-OutDir $OutDir

$ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
$dir = $OutDir
$report = Join-Path $dir "ROOMS_PANEL_API_REPORT.md"
"" | Set-Content -Path $report -Encoding UTF8
Add-Content $report "<!-- GENERATED: $ts -->"
Add-Content $report "# Rooms panel API — autodetected endpoints"
Add-Content $report ""
Add-Content $report ("Source calendar: {0}" -f (Resolve-Path -Relative $Calendar))
Add-Content $report ("BaseUrl: {0}" -f $BaseUrl)
if ($RoomHint) { Add-Content $report ("RoomHint: {0}" -f $RoomHint) }
Add-Content $report ""

$calls = Extract-ApiCalls $calText

# A1) /api/rooms/status_now
$epStatus = Pick-Endpoint $calls "status_now"
if ($epStatus) {
  $url1 = Join-Url $BaseUrl $epStatus.url
  $r1 = Fetch-Json -Method "GET" -Url $url1 -TimeoutSec $TimeoutSec
  $file1 = Join-Path $dir "rooms_status_now.json"
  if ($r1.ok) { Save-Json $file1 $r1.data } else { Save-Json $file1 @{ error=$r1.error; endpoint=$url1 } }
  Add-Content $report "## A1) GET /api/rooms/status_now"
  Add-Content $report ("- detected url: {0}" -f $epStatus.url)
  Add-Content $report ("- method guess: {0}" -f $epStatus.method)
  Add-Content $report ("- saved: {0}" -f (Resolve-Path -Relative $file1))
  Add-Content $report ""
} else {
  Add-Content $report "## A1) /api/rooms/status_now"
  Add-Content $report "_not found in calendar_"
  Add-Content $report ""
}

# A2) /api/free_slots (или подобное)
$epSlots = Pick-Endpoint $calls "free_slots"
if ($epSlots) {
  $room = $RoomHint
  if (-not $room) {
    # попробовать вытащить имя комнаты из HTML
    $mroom = [regex]::Match($calText, '(?i)(id|name)\s*=\s*["'']room(_name)?["''][^>]*value\s*=\s*["'']([^"'']+)["'']')
    if ($mroom.Success) { $room = $mroom.Groups[3].Value }
  }
  if (-not $room) { $room = "Ортопедия" }

  $date = (Get-Date).ToString("yyyy-MM-dd")
  $step = 15

  $uSlotsBase = Join-Url $BaseUrl $epSlots.url
  $qs = @{ room = $room; date = $date; step = $step }
  $qsStr = DictToQuery $qs
  if ($uSlotsBase -like "*?*") { $uSlotsGet = "$uSlotsBase&$qsStr" } else { $uSlotsGet = "$uSlotsBase?$qsStr" }

  $reqBody    = @{ room=$room; date=$date; step=$step }
  $reqHeaders = @{ "Content-Type" = "application/json" }

  $r2 = $null
  if ($epSlots.method -eq "POST") {
    $r2 = Fetch-Json -Method "POST" -Url $uSlotsBase -Body $reqBody -Headers $reqHeaders -TimeoutSec $TimeoutSec
    $reqMethod = "POST"
  } else {
    $tryGet = Fetch-Json -Method "GET" -Url $uSlotsGet -TimeoutSec $TimeoutSec
    if ($tryGet.ok) { $r2 = $tryGet; $reqMethod = "GET" }
    else { $r2 = Fetch-Json -Method "POST" -Url $uSlotsBase -Body $reqBody -Headers $reqHeaders -TimeoutSec $TimeoutSec; $reqMethod = "POST" }
  }

  $fileReq  = Join-Path $dir "free_slots_request.json"
  $fileResp = Join-Path $dir "free_slots_response.json"
  Save-Json $fileReq  @{ url=$uSlotsBase; query=$qs; method=$reqMethod; body=$reqBody }
  if ($r2.ok) { Save-Json $fileResp $r2.data } else { Save-Json $fileResp @{ error=$r2.error; endpoint=$uSlotsBase } }

  Add-Content $report "## A2) /api/free_slots (or similar)"
  Add-Content $report ("- detected url: {0}" -f $epSlots.url)
  Add-Content $report ("- method guess: {0}" -f $epSlots.method)
  Add-Content $report ("- request: {0}" -f (Resolve-Path -Relative $fileReq))
  Add-Content $report ("- response: {0}" -f (Resolve-Path -Relative $fileResp))
  Add-Content $report ""
} else {
  Add-Content $report "## A2) /api/free_slots"
  Add-Content $report "_not found in calendar_"
  Add-Content $report ""
}

# A3) /api/today_details?room=...
$epDetails = Pick-Endpoint $calls "today_details"
if ($epDetails) {
  $room = $RoomHint; if (-not $room) { $room = "Ортопедия" }
  $u3   = Join-Url $BaseUrl $epDetails.url
  $qs3  = @{ room = $room }
  $q3   = DictToQuery $qs3
  if ($u3 -like "*?*") { $u3q = "$u3&$q3" } else { $u3q = "$u3?$q3" }
  $r3   = Fetch-Json -Method "GET" -Url $u3q -TimeoutSec $TimeoutSec
  $file3 = Join-Path $dir "today_details_response.json"
  if ($r3.ok) { Save-Json $file3 $r3.data } else { Save-Json $file3 @{ error=$r3.error; endpoint=$u3q } }

  Add-Content $report "## A3) /api/today_details"
  Add-Content $report ("- detected url: {0}" -f $epDetails.url)
  Add-Content $report ("- saved: {0}" -f (Resolve-Path -Relative $file3))
  Add-Content $report ""
} else {
  Add-Content $report "## A3) /api/today_details"
  Add-Content $report "_not found in calendar_"
  Add-Content $report ""
}

# B) update_time — только шаблон payload
$epUpdate    = Pick-Endpoint $calls "update_time"
$payloadKeys = Guess-UpdateTime-PayloadKeys $calText
$fileUpd     = Join-Path $dir "update_time_request_template.json"
$tpl = [ordered]@{}
foreach ($k in $payloadKeys) { $tpl[$k] = "<fill>" }
if ($tpl.Contains("id"))    { $tpl["id"]    = 123 }
if ($tpl.Contains("start")) { $tpl["start"] = (Get-Date).ToString("yyyy-MM-ddT10:30:00Z") }
if ($tpl.Contains("end"))   { $tpl["end"]   = (Get-Date).ToString("yyyy-MM-ddT10:45:00Z") }
Save-Json $fileUpd $tpl

Add-Content $report "## B) update_time"
if ($epUpdate) {
  Add-Content $report ("- detected url: {0}" -f $epUpdate.url)
  Add-Content $report ("- method guess: {0}" -f $epUpdate.method)
} else {
  Add-Content $report "- endpoint not found in calendar"
}
Add-Content $report ("- request template: {0}" -f (Resolve-Path -Relative $fileUpd))
Add-Content $report "- expected keys:"
foreach ($k in $payloadKeys) { Add-Content $report ("  - {0}" -f $k) }
Add-Content $report ""

Write-Host ("OK -> " + (Resolve-Path -Relative $report))
.url -match ''(?i)update[_-]?time'' } }
    default        { $pred = { $false } }
  }
  $found = @()
  if ($calls) { $found = @($calls | Where-Object $pred) }
  if ($found.Count -gt 0) {
    $post = $found | Where-Object { <#
  export_dashboard_api_samples.ps1
  Собирает реальные примеры ответов для панели кабинетов + отчёт.

  Что делает:
  1) Читает templates/calendar.html, вытягивает все "/api/..." URL и рядом пытается угадать метод.
  2) Пытается определить:
     - GET  /api/rooms/status_now
     - POST/GET /api/free_slots (или похожее)
     - GET  /api/today_details?room=...
     - POST /api/appointments/update_time (для запроса — только шаблон payload)
  3) Дёргает API и кладёт результаты в artifacts/rooms_panel:
     - rooms_status_now.json
     - free_slots_request.json / free_slots_response.json
     - today_details_response.json
     - update_time_request_template.json
     - ROOMS_PANEL_API_REPORT.md
#>

param(
  [string]$BaseUrl   = "http://localhost:5000",
  [string]$Calendar  = ".\templates\calendar.html",
  [string]$OutDir    = ".\artifacts\rooms_panel",
  [string]$RoomHint  = "",
  [int]$TimeoutSec   = 10
)

# ---------- helpers ----------
function Ensure-OutDir([string]$p) {
  if (-not (Test-Path $p -PathType Container)) { New-Item -ItemType Directory -Path $p | Out-Null }
}
function Join-Url([string]$base, [string]$path) {
  if ([string]::IsNullOrWhiteSpace($path)) { return $base }
  if ($path -match '^https?://') { return $path }
  $b = $base.TrimEnd('/')
  $u = $path.TrimStart('/')
  return "$b/$u"
}
function Get-LineNum([string]$text, [int]$index) {
  if ($index -lt 0) { return 1 }
  $slice = $text.Substring(0, [Math]::Min($index, $text.Length))
  return ($slice -split "`n").Count
}
function UrlEncode([string]$s) { [System.Uri]::EscapeDataString([string]$s) }
function DictToQuery([hashtable]$d) {
  if (-not $d -or $d.Keys.Count -eq 0) { return "" }
  $pairs = @()
  foreach ($k in $d.Keys) { $pairs += ("{0}={1}" -f (UrlEncode $k), (UrlEncode ([string]$d[$k]))) }
  return ($pairs -join "&")
}
function Save-Json([string]$path, $obj) {
  $json = $obj | ConvertTo-Json -Depth 12
  Set-Content -Path $path -Value $json -Encoding UTF8
}
function Fetch-Json {
  param(
    [ValidateSet("GET","POST","PUT","PATCH","DELETE","HEAD","OPTIONS")]
    [string]$Method,
    [string]$Url,
    [hashtable]$Headers = $null,
    $Body = $null,
    [int]$TimeoutSec = 10
  )
  try {
    $params = @{
      Method      = $Method
      Uri         = $Url
      ErrorAction = "Stop"
    }
    if ($Headers) { $params["Headers"] = $Headers }
    if ($Body -ne $null -and $Method -in @("POST","PUT","PATCH","DELETE")) {
      if ($Body -is [hashtable] -or $Body -is [pscustomobject]) {
        $params["Body"] = ($Body | ConvertTo-Json -Depth 10)
        $params["ContentType"] = "application/json"
      } else {
        $params["Body"] = [string]$Body
      }
    }
    $resp = Invoke-RestMethod @params
    return @{ ok=$true; status=200; data=$resp; error=$null }
  } catch {
    $msg = $_.Exception.Message
    return @{ ok=$false; status=0; data=$null; error=$msg }
  }
}

# Вытащить все "/api/..." URL из файла и угадать метод по контексту
function Extract-ApiCalls([string]$text) {
  $calls = New-Object System.Collections.Generic.List[object]
  # Важно: строка single-quoted с удвоенными одинарными кавычками внутри.
  $rx = [regex]'(?i)[''"](?<url>/api/[^''""]+)[''"]'
  $matches = $rx.Matches($text)
  foreach ($m in $matches) {
    $url = $m.Groups['url'].Value
    $idx = $m.Index
    $line = Get-LineNum $text $idx
    # Контекст ±200 символов
    $s = [Math]::Max(0, $idx - 200)
    $e = [Math]::Min($text.Length, $idx + 200)
    $ctx = $text.Substring($s, $e - $s)
    $method = "GET"
    if ($ctx -match '(?i)axios\.(post|put|patch|delete)\s*\(') { $method = ($Matches[1].ToUpper()) }
    elseif ($ctx -match '(?i)\bmethod\s*:\s*["''](get|post|put|patch|delete|options|head)["'']') { $method = ($Matches[1].ToUpper()) }
    elseif ($ctx -match '(?i)fetch\s*\(' -and $ctx -match '(?i)\bbody\s*:') { $method = "POST" }
    $calls.Add([pscustomobject]@{ url=$url; line=$line; method=$method; ctx=$ctx }) | Out-Null
  }
  # Уникализируем по url+method (берём первый по файлу)
  $uniq = @{}
  $out = @()
  foreach ($c in $calls) {
    $key = $c.url + "|" + $c.method
    if (-not $uniq.ContainsKey($key)) { $uniq[$key] = $true; $out += $c }
  }
  return $out
}

# Подбор эндпоинтов по семантике
function Pick-Endpoint([array]$calls, [string]$kind) {
  $pred = $null
  switch ($kind) {
    "status_now"   { $pred = { ( $_.url -match '(?i)status' -and $_.url -match '(?i)room' ) -or $_.url -match '(?i)/rooms/status' } }
    "free_slots"   { $pred = { $_.url -match '(?i)free.*slot|slot.*free|/slots(\b|/)|/free_slots(\b|/)' } }
    "today_details"{ $pred = { $_.url -match '(?i)today.*detail|detail.*today|/today_details(\b|/)' } }
    "update_time"  { $pred = { $_.url -match '(?i)update[_-]?time' } }
    default        { $pred = { $false } }
  }
  $found = $calls | Where-Object $pred
  if ($found.Count -gt 0) {
    $post = $found | Where-Object { $_.method -eq "POST" } | Select-Object -First 1
    if ($post) { return $post }
    return ($found | Select-Object -First 1)
  }
  return $null
}

# Разбор ожидаемого payload для update_time прямо из кода (ищем JSON.stringify({...}))
function Guess-UpdateTime-PayloadKeys([string]$text) {
  $keys = New-Object System.Collections.Generic.HashSet[string]
  $rx = [regex]'(?is)update[_-]?time.*?JSON\.stringify\s*\(\s*\{(?<obj>[^}]*)\}'
  $m = $rx.Match($text)
  if ($m.Success) {
    $obj = $m.Groups['obj'].Value
    $rxk = [regex]'["''](?<k>[A-Za-z0-9_]+)["'']\s*:'
    foreach ($mm in $rxk.Matches($obj)) { [void]$keys.Add($mm.Groups['k'].Value) }
  } else {
    # запасные часто используемые
    [void]$keys.Add("id")
    [void]$keys.Add("start")
    [void]$keys.Add("end")
    [void]$keys.Add("room")
    [void]$keys.Add("doctor_id")
  }
  return ($keys | Sort-Object)
}

# ---------- main ----------
if (-not (Test-Path $Calendar -PathType Leaf)) {
  Write-Error ("calendar not found: " + $Calendar); exit 1
}
$calText = Get-Content -Path $Calendar -Raw
Ensure-OutDir $OutDir

$ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
$dir = $OutDir
$report = Join-Path $dir "ROOMS_PANEL_API_REPORT.md"
"" | Set-Content -Path $report -Encoding UTF8
Add-Content $report "<!-- GENERATED: $ts -->"
Add-Content $report "# Rooms panel API — autodetected endpoints"
Add-Content $report ""
Add-Content $report ("Source calendar: {0}" -f (Resolve-Path -Relative $Calendar))
Add-Content $report ("BaseUrl: {0}" -f $BaseUrl)
if ($RoomHint) { Add-Content $report ("RoomHint: {0}" -f $RoomHint) }
Add-Content $report ""

$calls = Extract-ApiCalls $calText

# A1) /api/rooms/status_now
$epStatus = Pick-Endpoint $calls "status_now"
if ($epStatus) {
  $url1 = Join-Url $BaseUrl $epStatus.url
  $r1 = Fetch-Json -Method "GET" -Url $url1 -TimeoutSec $TimeoutSec
  $file1 = Join-Path $dir "rooms_status_now.json"
  if ($r1.ok) { Save-Json $file1 $r1.data } else { Save-Json $file1 @{ error=$r1.error; endpoint=$url1 } }
  Add-Content $report "## A1) GET /api/rooms/status_now"
  Add-Content $report ("- detected url: {0}" -f $epStatus.url)
  Add-Content $report ("- method guess: {0}" -f $epStatus.method)
  Add-Content $report ("- saved: {0}" -f (Resolve-Path -Relative $file1))
  Add-Content $report ""
} else {
  Add-Content $report "## A1) /api/rooms/status_now"
  Add-Content $report "_not found in calendar_"
  Add-Content $report ""
}

# A2) /api/free_slots (или подобное)
$epSlots = Pick-Endpoint $calls "free_slots"
if ($epSlots) {
  $room = $RoomHint
  if (-not $room) {
    # попробовать вытащить имя комнаты из HTML
    $mroom = [regex]::Match($calText, '(?i)(id|name)\s*=\s*["'']room(_name)?["''][^>]*value\s*=\s*["'']([^"'']+)["'']')
    if ($mroom.Success) { $room = $mroom.Groups[3].Value }
  }
  if (-not $room) { $room = "Ортопедия" }

  $date = (Get-Date).ToString("yyyy-MM-dd")
  $step = 15

  $uSlotsBase = Join-Url $BaseUrl $epSlots.url
  $qs = @{ room = $room; date = $date; step = $step }
  $qsStr = DictToQuery $qs
  if ($uSlotsBase -like "*?*") { $uSlotsGet = "$uSlotsBase&$qsStr" } else { $uSlotsGet = "$uSlotsBase?$qsStr" }

  $reqBody    = @{ room=$room; date=$date; step=$step }
  $reqHeaders = @{ "Content-Type" = "application/json" }

  $r2 = $null
  if ($epSlots.method -eq "POST") {
    $r2 = Fetch-Json -Method "POST" -Url $uSlotsBase -Body $reqBody -Headers $reqHeaders -TimeoutSec $TimeoutSec
    $reqMethod = "POST"
  } else {
    $tryGet = Fetch-Json -Method "GET" -Url $uSlotsGet -TimeoutSec $TimeoutSec
    if ($tryGet.ok) { $r2 = $tryGet; $reqMethod = "GET" }
    else { $r2 = Fetch-Json -Method "POST" -Url $uSlotsBase -Body $reqBody -Headers $reqHeaders -TimeoutSec $TimeoutSec; $reqMethod = "POST" }
  }

  $fileReq  = Join-Path $dir "free_slots_request.json"
  $fileResp = Join-Path $dir "free_slots_response.json"
  Save-Json $fileReq  @{ url=$uSlotsBase; query=$qs; method=$reqMethod; body=$reqBody }
  if ($r2.ok) { Save-Json $fileResp $r2.data } else { Save-Json $fileResp @{ error=$r2.error; endpoint=$uSlotsBase } }

  Add-Content $report "## A2) /api/free_slots (or similar)"
  Add-Content $report ("- detected url: {0}" -f $epSlots.url)
  Add-Content $report ("- method guess: {0}" -f $epSlots.method)
  Add-Content $report ("- request: {0}" -f (Resolve-Path -Relative $fileReq))
  Add-Content $report ("- response: {0}" -f (Resolve-Path -Relative $fileResp))
  Add-Content $report ""
} else {
  Add-Content $report "## A2) /api/free_slots"
  Add-Content $report "_not found in calendar_"
  Add-Content $report ""
}

# A3) /api/today_details?room=...
$epDetails = Pick-Endpoint $calls "today_details"
if ($epDetails) {
  $room = $RoomHint; if (-not $room) { $room = "Ортопедия" }
  $u3   = Join-Url $BaseUrl $epDetails.url
  $qs3  = @{ room = $room }
  $q3   = DictToQuery $qs3
  if ($u3 -like "*?*") { $u3q = "$u3&$q3" } else { $u3q = "$u3?$q3" }
  $r3   = Fetch-Json -Method "GET" -Url $u3q -TimeoutSec $TimeoutSec
  $file3 = Join-Path $dir "today_details_response.json"
  if ($r3.ok) { Save-Json $file3 $r3.data } else { Save-Json $file3 @{ error=$r3.error; endpoint=$u3q } }

  Add-Content $report "## A3) /api/today_details"
  Add-Content $report ("- detected url: {0}" -f $epDetails.url)
  Add-Content $report ("- saved: {0}" -f (Resolve-Path -Relative $file3))
  Add-Content $report ""
} else {
  Add-Content $report "## A3) /api/today_details"
  Add-Content $report "_not found in calendar_"
  Add-Content $report ""
}

# B) update_time — только шаблон payload
$epUpdate    = Pick-Endpoint $calls "update_time"
$payloadKeys = Guess-UpdateTime-PayloadKeys $calText
$fileUpd     = Join-Path $dir "update_time_request_template.json"
$tpl = [ordered]@{}
foreach ($k in $payloadKeys) { $tpl[$k] = "<fill>" }
if ($tpl.Contains("id"))    { $tpl["id"]    = 123 }
if ($tpl.Contains("start")) { $tpl["start"] = (Get-Date).ToString("yyyy-MM-ddT10:30:00Z") }
if ($tpl.Contains("end"))   { $tpl["end"]   = (Get-Date).ToString("yyyy-MM-ddT10:45:00Z") }
Save-Json $fileUpd $tpl

Add-Content $report "## B) update_time"
if ($epUpdate) {
  Add-Content $report ("- detected url: {0}" -f $epUpdate.url)
  Add-Content $report ("- method guess: {0}" -f $epUpdate.method)
} else {
  Add-Content $report "- endpoint not found in calendar"
}
Add-Content $report ("- request template: {0}" -f (Resolve-Path -Relative $fileUpd))
Add-Content $report "- expected keys:"
foreach ($k in $payloadKeys) { Add-Content $report ("  - {0}" -f $k) }
Add-Content $report ""

Write-Host ("OK -> " + (Resolve-Path -Relative $report))
.method -eq "POST" } | Select-Object -First 1
    if ($post) { return $post }
    return ($found | Select-Object -First 1)
  }
  return $null
}}
    "free_slots"   { $pred = { $_.url -match '(?i)free.*slot|slot.*free|/slots(\b|/)|/free_slots(\b|/)' } }
    "today_details"{ $pred = { $_.url -match '(?i)today.*detail|detail.*today|/today_details(\b|/)' } }
    "update_time"  { $pred = { $_.url -match '(?i)update[_-]?time' } }
    default        { $pred = { $false } }
  }
  $found = $calls | Where-Object $pred
  if ($found.Count -gt 0) {
    $post = $found | Where-Object { $_.method -eq "POST" } | Select-Object -First 1
    if ($post) { return $post }
    return ($found | Select-Object -First 1)
  }
  return $null
}

# Разбор ожидаемого payload для update_time прямо из кода (ищем JSON.stringify({...}))
function Guess-UpdateTime-PayloadKeys([string]$text) {
  $keys = New-Object System.Collections.Generic.HashSet[string]
  $rx = [regex]'(?is)update[_-]?time.*?JSON\.stringify\s*\(\s*\{(?<obj>[^}]*)\}'
  $m = $rx.Match($text)
  if ($m.Success) {
    $obj = $m.Groups['obj'].Value
    $rxk = [regex]'["''](?<k>[A-Za-z0-9_]+)["'']\s*:'
    foreach ($mm in $rxk.Matches($obj)) { [void]$keys.Add($mm.Groups['k'].Value) }
  } else {
    # запасные часто используемые
    [void]$keys.Add("id")
    [void]$keys.Add("start")
    [void]$keys.Add("end")
    [void]$keys.Add("room")
    [void]$keys.Add("doctor_id")
  }
  return ($keys | Sort-Object)
}

# ---------- main ----------
if (-not (Test-Path $Calendar -PathType Leaf)) {
  Write-Error ("calendar not found: " + $Calendar); exit 1
}
$calText = Get-Content -Path $Calendar -Raw
Ensure-OutDir $OutDir

$ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
$dir = $OutDir
$report = Join-Path $dir "ROOMS_PANEL_API_REPORT.md"
"" | Set-Content -Path $report -Encoding UTF8
Add-Content $report "<!-- GENERATED: $ts -->"
Add-Content $report "# Rooms panel API — autodetected endpoints"
Add-Content $report ""
Add-Content $report ("Source calendar: {0}" -f (Resolve-Path -Relative $Calendar))
Add-Content $report ("BaseUrl: {0}" -f $BaseUrl)
if ($RoomHint) { Add-Content $report ("RoomHint: {0}" -f $RoomHint) }
Add-Content $report ""

$calls = Extract-ApiCalls $calText

# A1) /api/rooms/status_now
$epStatus = Pick-Endpoint $calls "status_now"
if ($epStatus) {
  $url1 = Join-Url $BaseUrl $epStatus.url
  $r1 = Fetch-Json -Method "GET" -Url $url1 -TimeoutSec $TimeoutSec
  $file1 = Join-Path $dir "rooms_status_now.json"
  if ($r1.ok) { Save-Json $file1 $r1.data } else { Save-Json $file1 @{ error=$r1.error; endpoint=$url1 } }
  Add-Content $report "## A1) GET /api/rooms/status_now"
  Add-Content $report ("- detected url: {0}" -f $epStatus.url)
  Add-Content $report ("- method guess: {0}" -f $epStatus.method)
  Add-Content $report ("- saved: {0}" -f (Resolve-Path -Relative $file1))
  Add-Content $report ""
} else {
  Add-Content $report "## A1) /api/rooms/status_now"
  Add-Content $report "_not found in calendar_"
  Add-Content $report ""
}

# A2) /api/free_slots (или подобное)
$epSlots = Pick-Endpoint $calls "free_slots"
if ($epSlots) {
  $room = $RoomHint
  if (-not $room) {
    # попробовать вытащить имя комнаты из HTML
    $mroom = [regex]::Match($calText, '(?i)(id|name)\s*=\s*["'']room(_name)?["''][^>]*value\s*=\s*["'']([^"'']+)["'']')
    if ($mroom.Success) { $room = $mroom.Groups[3].Value }
  }
  if (-not $room) { $room = "Ортопедия" }

  $date = (Get-Date).ToString("yyyy-MM-dd")
  $step = 15

  $uSlotsBase = Join-Url $BaseUrl $epSlots.url
  $qs = @{ room = $room; date = $date; step = $step }
  $qsStr = DictToQuery $qs
  if ($uSlotsBase -like "*?*") { $uSlotsGet = "$uSlotsBase&$qsStr" } else { $uSlotsGet = "$uSlotsBase?$qsStr" }

  $reqBody    = @{ room=$room; date=$date; step=$step }
  $reqHeaders = @{ "Content-Type" = "application/json" }

  $r2 = $null
  if ($epSlots.method -eq "POST") {
    $r2 = Fetch-Json -Method "POST" -Url $uSlotsBase -Body $reqBody -Headers $reqHeaders -TimeoutSec $TimeoutSec
    $reqMethod = "POST"
  } else {
    $tryGet = Fetch-Json -Method "GET" -Url $uSlotsGet -TimeoutSec $TimeoutSec
    if ($tryGet.ok) { $r2 = $tryGet; $reqMethod = "GET" }
    else { $r2 = Fetch-Json -Method "POST" -Url $uSlotsBase -Body $reqBody -Headers $reqHeaders -TimeoutSec $TimeoutSec; $reqMethod = "POST" }
  }

  $fileReq  = Join-Path $dir "free_slots_request.json"
  $fileResp = Join-Path $dir "free_slots_response.json"
  Save-Json $fileReq  @{ url=$uSlotsBase; query=$qs; method=$reqMethod; body=$reqBody }
  if ($r2.ok) { Save-Json $fileResp $r2.data } else { Save-Json $fileResp @{ error=$r2.error; endpoint=$uSlotsBase } }

  Add-Content $report "## A2) /api/free_slots (or similar)"
  Add-Content $report ("- detected url: {0}" -f $epSlots.url)
  Add-Content $report ("- method guess: {0}" -f $epSlots.method)
  Add-Content $report ("- request: {0}" -f (Resolve-Path -Relative $fileReq))
  Add-Content $report ("- response: {0}" -f (Resolve-Path -Relative $fileResp))
  Add-Content $report ""
} else {
  Add-Content $report "## A2) /api/free_slots"
  Add-Content $report "_not found in calendar_"
  Add-Content $report ""
}

# A3) /api/today_details?room=...
$epDetails = Pick-Endpoint $calls "today_details"
if ($epDetails) {
  $room = $RoomHint; if (-not $room) { $room = "Ортопедия" }
  $u3   = Join-Url $BaseUrl $epDetails.url
  $qs3  = @{ room = $room }
  $q3   = DictToQuery $qs3
  if ($u3 -like "*?*") { $u3q = "$u3&$q3" } else { $u3q = "$u3?$q3" }
  $r3   = Fetch-Json -Method "GET" -Url $u3q -TimeoutSec $TimeoutSec
  $file3 = Join-Path $dir "today_details_response.json"
  if ($r3.ok) { Save-Json $file3 $r3.data } else { Save-Json $file3 @{ error=$r3.error; endpoint=$u3q } }

  Add-Content $report "## A3) /api/today_details"
  Add-Content $report ("- detected url: {0}" -f $epDetails.url)
  Add-Content $report ("- saved: {0}" -f (Resolve-Path -Relative $file3))
  Add-Content $report ""
} else {
  Add-Content $report "## A3) /api/today_details"
  Add-Content $report "_not found in calendar_"
  Add-Content $report ""
}

# B) update_time — только шаблон payload
$epUpdate    = Pick-Endpoint $calls "update_time"
$payloadKeys = Guess-UpdateTime-PayloadKeys $calText
$fileUpd     = Join-Path $dir "update_time_request_template.json"
$tpl = [ordered]@{}
foreach ($k in $payloadKeys) { $tpl[$k] = "<fill>" }
if ($tpl.Contains("id"))    { $tpl["id"]    = 123 }
if ($tpl.Contains("start")) { $tpl["start"] = (Get-Date).ToString("yyyy-MM-ddT10:30:00Z") }
if ($tpl.Contains("end"))   { $tpl["end"]   = (Get-Date).ToString("yyyy-MM-ddT10:45:00Z") }
Save-Json $fileUpd $tpl

Add-Content $report "## B) update_time"
if ($epUpdate) {
  Add-Content $report ("- detected url: {0}" -f $epUpdate.url)
  Add-Content $report ("- method guess: {0}" -f $epUpdate.method)
} else {
  Add-Content $report "- endpoint not found in calendar"
}
Add-Content $report ("- request template: {0}" -f (Resolve-Path -Relative $fileUpd))
Add-Content $report "- expected keys:"
foreach ($k in $payloadKeys) { Add-Content $report ("  - {0}" -f $k) }
Add-Content $report ""

Write-Host ("OK -> " + (Resolve-Path -Relative $report))


