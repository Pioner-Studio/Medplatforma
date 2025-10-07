<# pack.ps1 — читает список путей из pack_list.txt и упаковывает их
   Запуск:  powershell -ExecutionPolicy Bypass -File .\pack.ps1
   Доп.:    powershell -ExecutionPolicy Bypass -File .\pack.ps1 -OutZip my_dump.zip -List pack_list_alt.txt
#>

param(
  [string]$OutZip = "needed_files.zip",
  [string]$List = "pack_list.txt"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $List)) {
  Write-Error "Файл списка не найден: $List"
  exit 1
}

# читаем строки, убираем пустые/комментарии (# ...)
$items = Get-Content $List | ForEach-Object { $_.Trim() } | Where-Object {
  ($_ -ne "") -and (-not $_.StartsWith("#"))
}

if ($items.Count -eq 0) {
  Write-Error "Список пуст. Добавь пути в $List и перезапусти."
  exit 1
}

$missing = @()
$existing = @()

foreach ($i in $items) {
  if (Test-Path $i) { $existing += $i } else { $missing += $i }
}

if ($missing.Count -gt 0) {
  Write-Warning "Не найдены файлы/папки:`n$($missing -join "`n")"
  Write-Host "Продолжаю с тем, что есть..." -ForegroundColor Yellow
}

if ($existing.Count -eq 0) {
  Write-Error "Нет ни одного существующего пути для упаковки. Исправь $List и перезапусти."
  exit 1
}

if (Test-Path $OutZip) { Remove-Item $OutZip -Force }
Compress-Archive -Path $existing -DestinationPath $OutZip -Force

Write-Host "Готово: $OutZip" -ForegroundColor Green
