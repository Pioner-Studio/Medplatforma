param(
  [string]$BaseUrl   = "http://localhost:5000",
  [string]$Calendar  = ".\templates\calendar.html",
  [string]$OutDir    = ".\docs\evidence\rooms_panel",
  [string]$RoomHint  = "Ортопедия",
  [int]$StepMinutes  = 15
)

# --- helpers ---
function Ensure-OutDir([string]$p){
  if(-not(Test-Path $p -PathType Container)){ New-Item -ItemType Directory -Path $p | Out-Null }
}
function Join-Url([string]$base,[string]$path){
  if([string]::IsNullOrWhiteSpace($path)){ return $base }
  if($path -match '^https?://'){ return $path }
  $b=$base.TrimEnd('/'); $u=$path.TrimStart('/'); return "$b/$u"
}
function Save-Json([string]$path,$obj){
  $json=$obj | ConvertTo-Json -Depth 30
  Set-Content -Path $path -Value $json -Encoding UTF8
}
function UrlEncode([string]$s){ [System.Uri]::EscapeDataString([string]$s) }
function DictToQuery([hashtable]$d){
  if(-not $d){return ""}
  ($d.Keys | ForEach-Object { (UrlEncode $_) + "=" + (UrlEncode ([string]$d[$_])) }) -join "&"
}
function Fetch-Json {
  param([string]$Method,[string]$Url,[hashtable]$Headers=$null,$Body=$null)
  try{
    $params=@{ Method=$Method; Uri=$Url; ErrorAction="Stop" }
    if($Headers){ $params.Headers=$Headers }
    if($Body -ne $null -and $Method -in @("POST","PUT","PATCH","DELETE")){
      if($Body -is [hashtable] -or $Body -is [pscustomobject]){
        $params.Body = ($Body | ConvertTo-Json -Depth 30)
        $params.ContentType = "application/json"
      } else { $params.Body = [string]$Body }
    }
    $resp = Invoke-RestMethod @params
    return @{ ok=$true; data=$resp; err=$null; method=$Method; url=$Url; body=$Body }
  } catch {
    return @{ ok=$false; data=$null; err=$_.Exception.Message; method=$Method; url=$Url; body=$Body }
  }
}
function Try-Requests([array]$reqs){
  foreach($r in $reqs){
    if(-not $r){ continue }
    $url     = $r.url
    $method  = $r.method
    $headers = $null
    $body    = $null
    $query   = $null
    if($r -is [hashtable]){
      if($r.ContainsKey('headers')){ $headers = $r.headers }
      if($r.ContainsKey('body'))   { $body    = $r.body }
      if($r.ContainsKey('query'))  { $query   = $r.query }
    }
    if($query){
      $q = DictToQuery $query
      if($q){
        if($url -like "*?*"){ $url = $url + "&" + $q } else { $url = $url + "?" + $q }
      }
    }
    $res = Fetch-Json -Method $method -Url $url -Headers $headers -Body $body
    if($res.ok){ return $res }
  }
  return $null
}

# --- /api/* из calendar.html (не обязательно, но помогает угадать пути) ---
$apiCandidates = @()
if(Test-Path $Calendar -PathType Leaf){
  $text = Get-Content -Path $Calendar -Raw
  $rx = [regex]'(?i)/api/[^\s"''<>)]+'  # простой матчер
  $urls = @(); foreach($m in $rx.Matches($text)){ $u=$m.Value; if($urls -notcontains $u){ $urls+=$u } }
  $apiCandidates = $urls
}

# --- подобрать URL’ы (детект -> дефолты) ---
function PickUrl([string]$kind){
  if($apiCandidates.Count -gt 0){
    switch($kind){
      'free_slots'    { $c = $apiCandidates | Where-Object { $_ -match '(?i)free.*slot|slot.*free|/slots(\b|/)|/free_slots(\b|/)' } | Select-Object -First 1; if($c){ return $c } }
      'today_details' { $c = $apiCandidates | Where-Object { $_ -match '(?i)today.*detail|detail.*today|/today_details(\b|/)|/rooms/today' } | Select-Object -First 1; if($c){ return $c } }
      'events'        { $c = $apiCandidates | Where-Object { $_ -match '(?i)/api/events(\b|/|\?)' } | Select-Object -First 1; if($c){ return $c } }
    }
  }
  switch($kind){
    'free_slots'    { return '/api/free_slots' }
    'today_details' { return '/api/rooms/today_details' }
    'events'        { return '/api/events' }
  }
}

$URL_FREE   = PickUrl 'free_slots'
$URL_TODAY  = PickUrl 'today_details'
$URL_EVENTS = PickUrl 'events'

# --- папка вывода ---
Ensure-OutDir $OutDir
$hints = Join-Path $OutDir 'ROUTES_HINTS.txt'
"" | Set-Content $hints -Encoding UTF8

# =========================
# A) /api/free_slots — УСПЕШНЫЙ ответ
# =========================
$room  = $RoomHint
$today = (Get-Date).ToString('yyyy-MM-dd')
$uFree = Join-Url $BaseUrl $URL_FREE

$reqs_free = @()
$roomKeys = @('room','room_name')
$dateKeys = @('date','day','date_str')
$stepKeys = @('step','interval','granularity')

foreach($rk in $roomKeys){
  foreach($dk in $dateKeys){
    foreach($sk in $stepKeys){
      $reqs_free += @{ method='GET';  url=$uFree; query=@{ $rk=$room; $dk=$today; $sk=$StepMinutes } }
      $reqs_free += @{ method='POST'; url=$uFree; body =@{ $rk=$room; $dk=$today; $sk=$StepMinutes } }
    }
    $reqs_free += @{ method='GET';  url=$uFree; query=@{ $rk=$room; $dk=$today } }
    $reqs_free += @{ method='POST'; url=$uFree; body =@{ $rk=$room; $dk=$today } }
  }
}
$altFreeUrls = @('/api/rooms/free_slots','/api/slots/free','/api/slots')
foreach($alt in $altFreeUrls){
  $full = Join-Url $BaseUrl $alt
  $reqs_free += @{ method='GET';  url=$full; query=@{ room=$room; date=$today; step=$StepMinutes } }
  $reqs_free += @{ method='POST'; url=$full; body =@{ room=$room; date=$today; step=$StepMinutes } }
}

$res_free = Try-Requests $reqs_free
if($res_free){
  $freePath = Join-Path $OutDir 'free_slots_success.json'
  Save-Json $freePath $res_free.data
  Add-Content $hints ("ROUTES.freeSlots={0}" -f $res_free.url)
  Write-Host ("OK free_slots -> " + $freePath)
}else{
  Write-Host "WARN: free_slots не удалось получить 200 OK" -ForegroundColor Yellow
}

# =========================
# B) /api/rooms/today_details — УСПЕШНЫЙ ответ
# =========================
$uToday = Join-Url $BaseUrl $URL_TODAY
$reqs_today = @()
$reqs_today += @{ method='GET';  url=$uToday; query=@{ room=$room } }
$reqs_today += @{ method='GET';  url=$uToday; query=@{ room_name=$room } }
$reqs_today += @{ method='POST'; url=$uToday; body =@{ room=$room } }
$reqs_today += @{ method='POST'; url=$uToday; body =@{ room_name=$room } }
$reqs_today += @{ method='GET';  url=$uToday }
$reqs_today += @{ method='POST'; url=$uToday }
$altToday = @('/api/today_details','/api/rooms/today','/api/schedule/today')
foreach($alt in $altToday){
  $full = Join-Url $BaseUrl $alt
  $reqs_today += @{ method='GET';  url=$full; query=@{ room=$room } }
  $reqs_today += @{ method='GET';  url=$full }
}
$res_today = Try-Requests $reqs_today

$todayObj = $null
if($res_today){
  $todayPath = Join-Path $OutDir 'today_details_success.json'
  Save-Json $todayPath $res_today.data
  $todayObj = $res_today.data
  Add-Content $hints ("ROUTES.todayDetails={0}" -f $res_today.url)
  Write-Host ("OK today_details -> " + $todayPath)
}else{
  Write-Host "WARN: today_details не удалось получить 200 OK" -ForegroundColor Yellow
}

# из today_details подхватим doctor_id/patient_id/room_name для фильтров событий
$doctorId = $null; $patientId = $null; $roomNameForEvents = $room
if($todayObj){
  $items = @()
  if($todayObj -is [System.Object[]]){ $items = $todayObj }
  elseif($todayObj -is [pscustomobject]){
    foreach($prop in $todayObj.PSObject.Properties){
      if($prop.Value -is [System.Object[]]){ $items += $prop.Value }
    }
  }
  foreach($it in $items){
    if(-not $doctorId  -and $it.PSObject.Properties['doctor_id']) { $doctorId = $it.doctor_id }
    if(-not $patientId -and $it.PSObject.Properties['patient_id']){ $patientId = $it.patient_id }
    if(-not $roomNameForEvents -and $it.PSObject.Properties['room_name']){ $roomNameForEvents = $it.room_name }
  }
}

# =========================
# C) /api/events — УСПЕШНЫЙ ответ с фильтрами
# =========================
$uEvents = Join-Url $BaseUrl $URL_EVENTS
$start = (Get-Date).Date.ToString("yyyy-MM-ddT00:00:00")
$end   = (Get-Date).Date.AddDays(1).AddSeconds(-1).ToString("yyyy-MM-ddT23:59:59")

$reqs_events = @()
$reqs_events += @{ method='GET'; url=$uEvents; query=@{
  start=$start; end=$end;
  doctor_id=$doctorId; patient_id=$patientId;
  room_name=$roomNameForEvents; room=$roomNameForEvents
} }
$reqs_events += @{ method='GET'; url=$uEvents; query=@{ start=$start; end=$end; room_name=$roomNameForEvents } }
$reqs_events += @{ method='GET'; url=$uEvents; query=@{ room_name=$roomNameForEvents } }
$reqs_events += @{ method='POST'; url=$uEvents; body=@{
  start=$start; end=$end; doctor_id=$doctorId; patient_id=$patientId; room_name=$roomNameForEvents
} }

$res_events = Try-Requests $reqs_events
if($res_events){
  $evPath = Join-Path $OutDir 'events_filtered_success.json'
  Save-Json $evPath $res_events.data
  Add-Content $hints ("ROUTES.events={0}" -f $res_events.url)
  Write-Host ("OK events (filtered) -> " + $evPath)
}else{
  Write-Host "WARN: events не удалось получить 200 OK" -ForegroundColor Yellow
}

Write-Host ("DONE. Hints -> " + (Resolve-Path -Relative $hints))
