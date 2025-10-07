<#
  concat_docs.ps1 — склеивает все .md из папки /docs в один большой файл artifacts/docs_bundle.md
  Пример запуска:
    .\scripts\concat_docs.ps1
    .\scripts\concat_docs.ps1 -DocsPath .\docs -OutDir .\artifacts -OutputName docs_bundle.md
  Поддерживает порядок из манифеста docs\_manifest.txt (по одной относительной дорожке на строку).
#>

param(
  [string]$DocsPath = ".\docs",
  [string]$OutDir = ".\artifacts",
  [string]$OutputName = "docs_bundle.md"
)

# --- Проверки папок ---
if (-not (Test-Path -Path $DocsPath -PathType Container)) {
  Write-Error "Папка '$DocsPath' не найдена. Создай /docs и положи .md файлы."
  exit 1
}
if (-not (Test-Path -Path $OutDir -PathType Container)) {
  New-Item -ItemType Directory -Path $OutDir | Out-Null
}

# --- Полные пути ---
$DocsFull = (Resolve-Path $DocsPath).Path
$OutFile = Join-Path $OutDir $OutputName

# --- Собираем список файлов ---
$manifestPath = Join-Path $DocsFull "_manifest.txt"
$files = Get-ChildItem -Path $DocsFull -Filter *.md -Recurse | Sort-Object FullName

# Если есть манифест — уважаем порядок
$ordered = @()
$seen = @{}
if (Test-Path $manifestPath) {
  $lines = Get-Content $manifestPath | Where-Object { $_.Trim() -ne "" -and -not $_.Trim().StartsWith("#") }
  foreach ($line in $lines) {
    $rel = $line.Trim().Replace("/", "\")
    $abs = Join-Path $DocsFull $rel
    if (Test-Path $abs) {
      $fi = Get-Item $abs
      $ordered += $fi
      $seen[$fi.FullName] = $true
    } else {
      Write-Warning "В манифесте указан несуществующий файл: $line"
    }
  }
}
foreach ($f in $files) {
  if (-not $seen.ContainsKey($f.FullName)) { $ordered += $f }
}

# --- Заголовок файла ---
"<!-- GENERATED: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') -->" | Set-Content -Path $OutFile -Encoding utf8
"# MedPlatforma Documentation Bundle" | Add-Content -Path $OutFile -Encoding utf8
"Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Add-Content -Path $OutFile -Encoding utf8
"Source folder: $DocsPath" | Add-Content -Path $OutFile -Encoding utf8
"Files: $($ordered.Count)" | Add-Content -Path $OutFile -Encoding utf8
"" | Add-Content -Path $OutFile -Encoding utf8
"---" | Add-Content -Path $OutFile -Encoding utf8

# --- Склейка с маркерами BEGIN/END ---
foreach ($file in $ordered) {
  $relPath = $file.FullName.Substring($DocsFull.Length).TrimStart('\')
  "" | Add-Content -Path $OutFile -Encoding utf8
  "=== BEGIN FILE: $relPath ===" | Add-Content -Path $OutFile -Encoding utf8
  "" | Add-Content -Path $OutFile -Encoding utf8
  Get-Content -Path $file.FullName -Encoding utf8 | Add-Content -Path $OutFile -Encoding utf8
  "" | Add-Content -Path $OutFile -Encoding utf8
  "=== END FILE: $relPath ===" | Add-Content -Path $OutFile -Encoding utf8
  "" | Add-Content -Path $OutFile -Encoding utf8
}

Write-Host "Готово: $OutFile"
