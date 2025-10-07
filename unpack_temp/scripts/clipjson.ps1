param([Parameter(Mandatory=$true)][string]$OutPath)

$dir = Split-Path -Parent $OutPath
if (-not (Test-Path $dir -PathType Container)) { New-Item -ItemType Directory -Path $dir | Out-Null }

# Читаем буфер, пишем как есть (UTF-8)
$txt = Get-Clipboard -Raw
Set-Content -Path $OutPath -Value $txt -Encoding UTF8

Write-Host ("OK -> " + (Resolve-Path -Relative $OutPath))
