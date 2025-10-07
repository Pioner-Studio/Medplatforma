param(
  [string]$Calendar = ".\templates\calendar.html",
  [string]$OutDir   = ".\artifacts"
)

# — проверка наличия файла календаря
if (-not (Test-Path $Calendar -PathType Leaf)) {
  Write-Error ("Файл не найден: " + $Calendar)
  exit 1
}

# — создаём папку выгрузок
if (-not (Test-Path $OutDir -PathType Container)) { New-Item -ItemType Directory -Path $OutDir | Out-Null }

# — собираем пути назначения
$txt = Join-Path $OutDir "calendar.html.txt"
$md  = Join-Path $OutDir "calendar_full.md"

# — печатаем информацию о входном файле
$fi = Get-Item $Calendar
Write-Host ("READ  -> {0} ({1} KB)" -f $fi.FullName, [math]::Round($fi.Length/1kb,2))

# 1) TXT (надёжно для загрузки)
try {
  Get-Content -Path $Calendar -Raw -ErrorAction Stop | Set-Content -Path $txt -Encoding UTF8 -ErrorAction Stop
  Write-Host ("WRITE -> {0}" -f $txt)
} catch {
  Write-Error ("Не удалось записать TXT: " + $_.Exception.Message)
}

# 2) Markdown с подсветкой (без проблем с бэктиками)
try {
  '```html' | Set-Content -Path $md -Encoding UTF8 -ErrorAction Stop
  Get-Content -Path $Calendar -Raw -ErrorAction Stop | Add-Content -Path $md -Encoding UTF8 -ErrorAction Stop
  '```' | Add-Content -Path $md -Encoding UTF8 -ErrorAction Stop
  Write-Host ("WRITE -> {0}" -f $md)
} catch {
  Write-Error ("Не удалось записать MD: " + $_.Exception.Message)
}

# 3) (опционально) авто-чанки для очень больших файлов (> 512 KB)
if ($fi.Length -gt 512kb) {
  Write-Host "INFO  -> файл большой, режем на части по 3000 строк..."
  $src = Get-Content $Calendar
  $chunk = 3000; $i=0
  for ($off=0; $off -lt $src.Count; $off += $chunk) {
    $part = $src[$off..([Math]::Min($off+$chunk-1,$src.Count-1))]
    $i++; $out = Join-Path $OutDir ("calendar_part_{0:000}.txt" -f $i)
    $part | Set-Content $out -Encoding UTF8
    Write-Host ("WRITE -> {0}" -f $out)
  }
}

# 4) дубль-резерв: просто копия HTML (вдруг пригодится)
try {
  Copy-Item -Path $Calendar -Destination (Join-Path $OutDir "calendar.html") -Force -ErrorAction SilentlyContinue
} catch {}

Write-Host "OK    -> экспорт календаря завершён"
