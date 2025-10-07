param(
  [string]$Calendar = ".\templates\calendar.html",
  [string]$OutDir   = ".\artifacts"
)
if (-not (Test-Path $Calendar -PathType Leaf)) { Write-Error "Не найден файл: $Calendar"; exit 1 }
if (-not (Test-Path $OutDir -PathType Container)) { New-Item -ItemType Directory -Path $OutDir | Out-Null }

$txt = Join-Path $OutDir "calendar.html.txt"
Get-Content -Path $Calendar -Raw | Set-Content -Path $txt -Encoding UTF8
Write-Host ("OK -> " + $txt)
