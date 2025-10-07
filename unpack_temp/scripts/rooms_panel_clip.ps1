param(
  [ValidateSet('schedule','status','details')]
  [string]$Kind,
  [string]$Room = 'РћСЂС‚РѕРїРµРґРёСЏ',
  [string]$OutDir = '.\docs\evidence\rooms_panel'
)

New-Item -ItemType Directory -Path $OutDir -Force | Out-Null

switch ($Kind) {
  'schedule' { $file = "doctor_schedule_today_{0}.json" -f $Room }
  'status'   { $file = "status_now.json" }
  'details'  { $file = "today_details_{0}_busy.json" -f $Room }
}
$dest = Join-Path $OutDir $file

try {
  $raw = Get-Clipboard -Raw
  if ([string]::IsNullOrWhiteSpace($raw)) { throw "Р’ Р±СѓС„РµСЂРµ РїСѓСЃС‚Рѕ. РЎРєРѕРїРёСЂСѓР№ Response (РїСЂР°РІС‹Р№ РєР»РёРє в†’ Copy в†’ Copy response) Рё РїРѕРІС‚РѕСЂРё." }
  $null = $raw | ConvertFrom-Json -ErrorAction Stop  # РІР°Р»РёРґР°С†РёСЏ JSON
  Set-Content -Path $dest -Value $raw -Encoding UTF8
  Write-Host ("OK -> " + (Resolve-Path -Relative $dest))
}
catch {
  $fallback = [System.IO.Path]::ChangeExtension($dest, ".txt")
  Set-Content -Path $fallback -Value $raw -Encoding UTF8
  Write-Host ("WARN: Р±СѓС„РµСЂ РЅРµ РїРѕС…РѕР¶ РЅР° JSON: " + $_.Exception.Message) -ForegroundColor Yellow
  Write-Host ("РЎРѕС…СЂР°РЅРёР» РєР°Рє " + (Resolve-Path -Relative $fallback))
  Write-Host "РџРѕРґСЃРєР°Р·РєР°: РѕС‚РєСЂРѕР№ РІРєР»Р°РґРєСѓ Response, СѓР±РµРґРёСЃСЊ С‡С‚Рѕ РЅР°С‡РёРЅР°РµС‚СЃСЏ СЃ { РёР»Рё [ }, Рё СЃРЅРѕРІР° Copy в†’ Copy response."
}

