param(
  [string]$BaseUrl    = "http://localhost:5000",
  [string]$OutDir     = ".\docs\evidence\rooms_panel",
  [string]$RoomHint   = "Ортопедия",
  [int]   $StepMinutes= 15,
  [switch]$VerboseLog
)

function Ensure-OutDir([string]$p){ if(-not(Test-Path $p -PathType Container)){ New-Item -ItemType Directory -Path $p | Out-Null } }
function Join-Url([string]$base,[string]$path){
  if([string]::IsNullOrWhiteSpace($path)){ return $base }
  if($path -match '^https?://'){ return $path }
  $b=$base.TrimEnd('/'); $u=$path.TrimStart('/'); return "$b/$u"
}
function Save-Json([string]$path,$obj){ $json=$obj | ConvertTo-Json -Depth 32; Set-Content -Path $path -Value $json -Encoding UTF8 }
function UrlEncode([string]$s){ [System.Uri]::EscapeDataString([string]$s) }
function DictToQuery([hashtable]$d){ if(-not $d){return ""}; ($d.Keys | ForEach-Object { (UrlEncode $_) + "=" + (UrlEncode ([string]$d[$_])) }) -join "&" }

function Fetch-Json {
  param(
    [ValidateSet("GET","POST","PUT","PATCH","DELETE","HEAD","OPTIONS")]
    [string]$Method,
    [string]$Url,
    [hashtable]$Headers = $null,
    $Body = $null,
    [string]$ContentType = $null,
    [int]$TimeoutSec = 15
  )
  try{
    $params=@{ Method=$Method; Uri=$Url; TimeoutSec=$TimeoutSec; ErrorAction="Stop" }
    if($Headers){ $params.Headers=$Headers }
    if($Body -ne $null -and $Method -in @("POST","PUT","PATCH","DELETE")){
      if($Body -is [hashtable] -or $Body -is [pscustomobject]){
        $params.Body = ($Body | ConvertTo-Json -Depth 32)
        if(-not $ContentType){ $ContentType = "application/json" }
      } else { $params.Body = [string]$Body }
    }
    if($ContentType){ $params.ContentType = $ContentType }
    if($VerboseLog){ Write-Host "→ $Method $Url" -ForegroundColor DarkGray }
    $resp = Invoke-RestMethod @params
    return @{ ok=$true; data=$resp; err=$null; method=$Method; url=$Url; body=$Body; ctype=$ContentType }
  } catch {
    return @{ ok=$false; data=$null; err=$_.Exception.Message; method=$Method; url=$Url; body=$Body; ctype=$ContentType }
  }
}

function Try-Requests([array]$reqs){
  $last=$null
  foreach($r in $reqs){
    $url = $r.url
    if($r.ContainsKey('query') -and $r.query){
      $q=DictToQuery $r.query
      if($q){ $url = $url + ($(if($url -like "*?*"){"&$q"}else{"?$q"})) }
    }
    $headers = $(if($r.ContainsKey('headers')){ $r.headers } else { $null })
    $body    = $(if($r.ContainsKey('body'))   { $r.body    } else { $null })
    $ctype   = $(if($r.ContainsKey('ctype'))  { $r.ctype   } else { $null })
    $res = Fetch-Json -Method $r.method -Url $url -Headers $headers -Body $body -ContentType $ctype
    $last = $res
    if($res.ok){ return $res }
  }
  return $last
}

# ---------- подготовка ----------
Ensure-OutDir $OutDir
$hints = Join-Path $OutDir 'ROUTES_HINTS.txt'
"" | Set-Content $hints -Encoding UTF8

# вытягиваем удобное имя/id кабинета из /api/dicts (если доступно)
$roomName = $RoomHint
$roomId = $null
$dicts  = Fetch-Json -Method GET -Url (Join-Url $BaseUrl "/api/dicts")
if($dicts.ok -and $dicts.data -and $dicts.data.rooms){
  $rooms = $dicts.data.rooms
  if($rooms -is [System.Object[]]){
    $pick = $null
    if($roomName){ $pick = $rooms | Where-Object { $_.name -eq $roomName } | Select-Object -First 1 }
    if(-not $pick){ $pick = $rooms | Select-Object -First 1 }
    if($pick){
      $roomName = $pick.name
      if($pick.PSObject.Properties['id']) { $roomId = $pick.id }
      elseif($pick.PSObject.Properties['_id']) { $roomId = $pick._id }
    }
  }
}
if($VerboseLog){ Write-Host "Room selected: name='$roomName' id='$roomId'" -ForegroundColor DarkGray }

# ---------- A) free_slots ----------
$today = (Get-Date).ToString('yyyy-MM-dd')
$URLS_FREE = @("/api/free_slots","/api/rooms/free_slots","/api/slots/free","/api/slots")
$reqs_free = @()
foreach($u in $URLS_FREE){
  $full = Join-Url $BaseUrl $u
  foreach($rk in @('room','room_name','cabinet','cabinet_name','room_id')){
    foreach($dk in @('date','day','date_str')){
      foreach($sk in @('step','interval','minute_step')){
        $valRoom = $(if($rk -eq 'room_id' -and $roomId){ $roomId } else { $roomName })
        $reqs_free += @{ method='POST'; url=$full; body=@{ $rk=$valRoom; $dk=$today; $sk=$StepMinutes } }
        $reqs_free += @{ method='POST'; url=$full; body=(DictToQuery @{ $rk=$valRoom; $dk=$today; $sk=$StepMinutes }); ctype='application/x-www-form-urlencoded' }
        $reqs_free += @{ method='GET';  url=$full; query=@{ $rk=$valRoom; $dk=$today; $sk=$StepMinutes } }
      }
      $valRoom2 = $(if($rk -eq 'room_id' -and $roomId){ $roomId } else { $roomName })
      $reqs_free += @{ method='POST'; url=$full; body=@{ $rk=$valRoom2; $dk=$today } }
      $reqs_free += @{ method='GET';  url=$full; query=@{ $rk=$valRoom2; $dk=$today } }
    }
  }
}
$res_free = Try-Requests $reqs_free

# Fallback: строим слоты из /api/rooms/busy
if(-not $res_free -or -not $res_free.ok){
  $uBusy = Join-Url $BaseUrl "/api/rooms/busy"
  $busyQs = @{ date=$today }
  if($roomId){ $busyQs.room_id = $roomId } elseif($roomName){ $busyQs.room_name = $roomName; $busyQs.room = $roomName }
  $res_busy = Try-Requests @(
    @{ method='GET';  url=$uBusy; query=$busyQs },
    @{ method='POST'; url=$uBusy; body=$busyQs }
  )
  $busy = @()
  if($res_busy -and $res_busy.ok -and $res_busy.data -and $res_busy.data.items){ $busy = $res_busy.data.items }

  function To-Min($hhmm){ $t=$hhmm -split ':'; return [int]$t[0]*60 + [int]$t[1] }
  function From-Min($m){ '{0:00}:{1:00}' -f [math]::Floor($m/60), ($m%60) }

  $open = To-Min "09:00"; $close = To-Min "21:00"
  $grid = @()
  for($m=$open; $m -le $close - $StepMinutes; $m+=$StepMinutes){ $grid += $m }
  foreach($b in $busy){ $bs=To-Min $b.start; $be=To-Min $b.end; $grid = $grid | Where-Object { $_ -lt $bs -or $_ -ge $be } }
  $slots = $grid | ForEach-Object { From-Min $_ }

  $res_free = @{ ok = $true; data = @{ ok = $true; slots = $slots; source = "computed_from_/api/rooms/busy" }; url = $uBusy }
}
$freePath = Join-Path $OutDir 'free_slots_success.json'
Save-Json $freePath $res_free.data
Add-Content $hints ("ROUTES.freeSlots={0}" -f ($(if($res_free.url){$res_free.url}else{ Join-Url $BaseUrl "/api/free_slots"})))
Write-Host ("OK free_slots -> " + (Resolve-Path -Relative $freePath))

# ---------- B) today_details ----------
$URLS_TODAY = @("/api/rooms/today_details","/api/today_details","/api/rooms/today","/api/schedule/today")
$reqs_today = @()
foreach($u in $URLS_TODAY){
  $full = Join-Url $BaseUrl $u
  foreach($rk in @('room','room_name','cabinet','cabinet_name','room_id')){
    $valRoom = $(if($rk -eq 'room_id' -and $roomId){ $roomId } else { $roomName })
    $reqs_today += @{ method='GET';  url=$full; query=@{ $rk=$valRoom } }
    $reqs_today += @{ method='POST'; url=$full; body =@{ $rk=$valRoom } }
  }
  $reqs_today += @{ method='GET'; url=$full }
}
$res_today = Try-Requests $reqs_today

# Fallback: собираем "сегодня" из /api/events
if(-not $res_today -or -not $res_today.ok){
  $dayStart = (Get-Date).Date.ToString("yyyy-MM-ddT00:00:00")
  $dayEnd   = (Get-Date).Date.ToString("yyyy-MM-ddT23:59:59")
  $uEvents  = Join-Url $BaseUrl "/api/events"
  $res_ev   = Try-Requests @(
    @{ method='GET'; url=$uEvents; query=@{ start=$dayStart; end=$dayEnd; room_name=$roomName } },
    @{ method='GET'; url=$uEvents; query=@{ room_name=$roomName } }
  )
  $items = @()
  if($res_ev -and $res_ev.ok -and $res_ev.data){
    foreach($ev in $res_ev.data){
      $items += [pscustomobject]@{
        id = $(if($ev.PSObject.Properties['id']){$ev.id}else{$null})
        start = $ev.start
        end   = $ev.end
        patient   = $(if($ev.PSObject.Properties['patient']){$ev.patient}else{$null})
        patient_id= $(if($ev.PSObject.Properties['patient_id']){$ev.patient_id}else{$null})
        service   = $(if($ev.PSObject.Properties['service']){$ev.service}else{$null})
        doctor_id = $(if($ev.PSObject.Properties['doctor_id']){$ev.doctor_id}else{$null})
        room_name = $(if($ev.PSObject.Properties['room_name']){$ev.room_name}else{$roomName})
        status    = $(if($ev.PSObject.Properties['status']){$ev.status}else{$null})
      }
    }
  }
  $res_today = @{ ok=$true; data = @{ ok=$true; items=$items; source="derived_from_/api/events" }; url = $uEvents }
}
$todayPath = Join-Path $OutDir 'today_details_success.json'
Save-Json $todayPath $res_today.data
Add-Content $hints ("ROUTES.todayDetails={0}" -f ($(if($res_today.url){$res_today.url}else{ Join-Url $BaseUrl "/api/rooms/today_details"})))
Write-Host ("OK today_details -> " + (Resolve-Path -Relative $todayPath))

# ---------- C) events (filtered) ----------
$start = (Get-Date).Date.ToString("yyyy-MM-ddT00:00:00")
$end   = (Get-Date).Date.ToString("yyyy-MM-ddT23:59:59")
$uEvents = Join-Url $BaseUrl "/api/events"
$res_events = Try-Requests @(
  @{ method='GET'; url=$uEvents; query=@{ start=$start; end=$end; room_name=$roomName } },
  @{ method='GET'; url=$uEvents; query=@{ room_name=$roomName } },
  @{ method='GET'; url=$uEvents; query=@{ start=$start; end=$end } }
)
$evPath = Join-Path $OutDir 'events_filtered_success.json'
if($res_events -and $res_events.ok){
  Save-Json $evPath $res_events.data
  Add-Content $hints ("ROUTES.events={0}" -f $res_events.url)
  Write-Host ("OK events (filtered) -> " + (Resolve-Path -Relative $evPath))
} else {
  Save-Json $evPath @{ error=$res_events.err; endpoint=$res_events.url }
  Write-Host "WARN: events не удалось получить 200 OK" -ForegroundColor Yellow
}

Write-Host ("DONE. Hints -> " + (Resolve-Path -Relative $hints))
