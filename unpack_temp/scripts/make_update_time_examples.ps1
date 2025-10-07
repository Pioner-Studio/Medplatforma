param([string]$OutDir = ".\artifacts")

if (-not (Test-Path $OutDir -PathType Container)) {
  New-Item -ItemType Directory -Path $OutDir | Out-Null
}

# --- JSON как объекты (никаких here-string) ---
$success = @{
  status = 'ok'
  action = 'update_time'
  appointment_id = 123
  update_time = '2025-09-11T10:30:00Z'
  message = 'Time updated'
}

$conflict = @{
  status = 'conflict'
  action = 'update_time'
  appointment_id = 123
  message = 'Slot is already booked'
  conflict_with = @{
    appointment_id = 456
    start = '2025-09-11T10:15:00Z'
    end   = '2025-09-11T10:45:00Z'
    room  = 'Ортопедия'
    doctor_id = 7
  }
}

$error = @{
  status = 'error'
  action = 'update_time'
  error = 'validation'
  message = 'Outside working hours (09:00–21:00)'
  details = @{
    start = '2025-09-11T08:30:00Z'
    end   = '2025-09-11T09:30:00Z'
    reason = 'non_working_time'
  }
}

# --- Пишем JSON файлы ---
($success | ConvertTo-Json -Depth 6) | Set-Content (Join-Path $OutDir 'update_time_success.json')  -Encoding UTF8
($conflict | ConvertTo-Json -Depth 6) | Set-Content (Join-Path $OutDir 'update_time_conflict.json') -Encoding UTF8
($error   | ConvertTo-Json -Depth 6) | Set-Content (Join-Path $OutDir 'update_time_error.json')    -Encoding UTF8

# --- MD-справка ---
$md = Join-Path $OutDir 'UPDATE_TIME_SAMPLES.md'
'' | Set-Content $md -Encoding UTF8
Add-Content $md '# update_time — sample responses'
Add-Content $md ''

Add-Content $md '## success'
Add-Content $md '```json'
Add-Content $md ($success | ConvertTo-Json -Depth 6)
Add-Content $md '```'
Add-Content $md ''

Add-Content $md '## conflict'
Add-Content $md '```json'
Add-Content $md ($conflict | ConvertTo-Json -Depth 6)
Add-Content $md '```'
Add-Content $md ''

Add-Content $md '## error'
Add-Content $md '```json'
Add-Content $md ($error | ConvertTo-Json -Depth 6)
Add-Content $md '```'

Write-Host ("OK -> " + $md)
Write-Host ("OK -> " + (Join-Path $OutDir 'update_time_success.json'))
Write-Host ("OK -> " + (Join-Path $OutDir 'update_time_conflict.json'))
Write-Host ("OK -> " + (Join-Path $OutDir 'update_time_error.json'))
