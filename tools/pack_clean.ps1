param(
    [string]$Root = "D:\Projects\medplatforma"
)

$stamp = Get-Date -Format 'yyyy-MM-dd_HH-mm-ss'
$tmp   = Join-Path $env:TEMP "mp_pack_$stamp"
$out   = Join-Path $Root "medplatforma_backup_$stamp.zip"

Write-Host "▶ Подготовка архива проекта из $Root"

robocopy $Root $tmp /MIR `
  /XD .git .venv __pycache__ exports .pytest_cache .vscode .idea `
  /XF *.pyc *.log *.tmp *.zip desktop.ini `
  /NJH /NJS /NFL /NDL /NP | Out-Null

if (Test-Path $out) { Remove-Item $out -Force }
Compress-Archive -Path "$tmp\*" -DestinationPath $out -CompressionLevel Optimal -Force

Remove-Item $tmp -Recurse -Force
Write-Host "✅ Архив готов: $out"
