<#
  make_docs.ps1 — собирает папку /docs в ZIP-архив
  Пример запуска:
    pwsh -File .\scripts\make_docs.ps1
    # или, если уже в PowerShell:
    .\scripts\make_docs.ps1
#>

param(
  # Путь к папке с документацией
  [string]$DocsPath = ".\docs",

  # Папка, куда складывать ZIP-архивы
  [string]$OutDir = ".\artifacts",

  # Имя файла ZIP (если пусто — сгенерируем с таймстампом)
  [string]$ZipName = ""
)

# --- Проверки ---------------------------------------------------------------
if (-not (Test-Path -Path $DocsPath -PathType Container)) {
  Write-Error "Папка '$DocsPath' не найдена. Создай /docs и положи .md файлы."
  exit 1
}

if (-not (Test-Path -Path $OutDir -PathType Container)) {
  New-Item -ItemType Directory -Path $OutDir | Out-Null
}

# --- Имя ZIP по умолчанию ---------------------------------------------------
if ([string]::IsNullOrWhiteSpace($ZipName)) {
  $stamp = (Get-Date).ToString("yyyyMMdd_HHmmss")
  $ZipName = "docs_bundle_$stamp.zip"
}

$ZipPath = Join-Path $OutDir $ZipName

# --- Сборка ZIP -------------------------------------------------------------
# Примечание: -Force перезапишет существующий архив с тем же именем
if (Test-Path $ZipPath) {
  Remove-Item $ZipPath -Force
}

Write-Host "Собираю '$DocsPath' → '$ZipPath' ..."
Compress-Archive -Path (Join-Path $DocsPath "*") -DestinationPath $ZipPath -Force
Write-Host "Готово: $ZipPath"
