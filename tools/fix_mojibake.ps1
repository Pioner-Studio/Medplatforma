# tools\fix_mojibake.ps1
param(
  [Parameter(Mandatory=$true)][string]$Path  # например: .\templates\calendar.html
)

$ErrorActionPreference = 'Stop'
$full = (Resolve-Path -LiteralPath $Path).Path
$stamp = Get-Date -Format 'yyyy-MM-dd_HH-mm-ss'

# 1) Бэкап
$bak = "$full.bak_$stamp"
Copy-Item -LiteralPath $full -Destination $bak -Force
Write-Host "Backup: $bak"

function Contains-Cyrillic([string]$s) {
  return ($s -match '[\u0400-\u04FF]')  # диапазон кириллицы
}

# 2) Пробуем восстановление двумя стратегиями
# S1: "Р°/Рµ/Рё..." → исходник был UTF-8, а его прочли как cp1251
#    фикс: bytes = cp1251(text); good = utf8(bytes)
# S2: "Ð°/Ñƒ/Ð¸..." → исходник был UTF-8, а его прочли как Latin1
#    фикс: bytes = latin1(text); good = utf8(bytes)

$broken = Get-Content -LiteralPath $full -Raw -Encoding UTF8   # читаем как есть

# .NET перекодировки
$encCp1251 = [System.Text.Encoding]::GetEncoding(1251)
$encUtf8   = [System.Text.Encoding]::UTF8
$encLatin1 = [System.Text.Encoding]::GetEncoding("iso-8859-1")

# Strategy 1
$bytesS1 = $encCp1251.GetBytes($broken)
$tryS1   = $encUtf8.GetString($bytesS1)

# Strategy 2
$bytesS2 = $encLatin1.GetBytes($broken)
$tryS2   = $encUtf8.GetString($bytesS2)

# Выбираем лучший: где больше кириллицы
$c1 = ([regex]::Matches($tryS1, '[\u0400-\u04FF]')).Count
$c2 = ([regex]::Matches($tryS2, '[\u0400-\u04FF]')).Count
$fixed = if ($c2 -gt $c1) { $tryS2 } else { $tryS1 }
$chosen = if ($c2 -gt $c1) { 'latin1→utf8' } else { 'cp1251→utf8' }

# 3) Чиним <meta charset>, если нужно (вставка в <head>)
if ($fixed -notmatch '(?i)<meta\s+charset=') {
  $fixed = $fixed -replace '(?is)(<head[^>]*>)', '$1' + "`r`n" + '    <meta charset="UTF-8">'
} else {
  $fixed = $fixed -replace '(?is)<meta\s+charset=["'']?[^"''>]+["'']?', '<meta charset="UTF-8">'
}

# 4) Сохраняем в UTF-8 (без ломания исходника)
$fixed | Set-Content -LiteralPath $full -Encoding UTF8
Write-Host "Fixed with: $chosen"
Write-Host "Saved: $full (UTF-8)"

# 5) Покажем превью (первые 5 строк, чтобы убедиться глазами)
$preview = ($fixed -split "`r?`n")[0..([Math]::Min(4, ($fixed -split "`r?`n").Count-1))]
Write-Host "`n--- Preview ---"
$preview | ForEach-Object { Write-Host $_ }
Write-Host "-----------------`n"
Write-Host "Если что-то не так: верни назад бэкап:  Copy-Item `"$bak`" `"$full`" -Force"
