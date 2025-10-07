Param(
  [string]$Root  = ".",
  [string]$Attic = "attic",
  $DryRun        = $true,   # принимает true/false/1/0/yes/no/on/off
  $Zip           = $false
)

function To-Bool([object]$v, [bool]$default=$false){
  if ($v -is [bool]) { return $v }
  if ($v -is [int])  { return [bool]$v }
  if ($null -eq $v)  { return $default }
  $s = ($v.ToString()).ToLower().Trim()
  switch ($s) {
    'true' { return $true }
    'false'{ return $false }
    '1'    { return $true }
    '0'    { return $false }
    'yes'  { return $true }
    'no'   { return $false }
    'on'   { return $true }
    'off'  { return $false }
    default { return $default }
  }
}

$DryRun = To-Bool $DryRun $true
$Zip    = To-Bool $Zip $false

$Root      = (Resolve-Path $Root).Path
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$AtticBase = Join-Path $Root $Attic
$AtticRoot = Join-Path $AtticBase $timestamp
New-Item -ItemType Directory -Force -Path $AtticRoot | Out-Null

# 1) Каталоги, которые не сканируем вовсе
$ExcludePatterns = @(
  "\\attic(\\|$)",         # наш архив
  "\\.git(\\|$)",
  "\\.venv(\\|$)","\\venv(\\|$)","\\env(\\|$)",
  "\\node_modules(\\|$)",
  "\\__pycache__(\\|$)","\\.pytest_cache(\\|$)","\\.mypy_cache(\\|$)",
  "\\dist(\\|$)","\\build(\\|$)",
  "\\.idea(\\|$)","\\.vscode(\\|$)"
)

# 2) Файлы, которые всегда сохраняем
$KeepFiles = @(
  'main.py','routes_schedule.py','routes_finance.py','routes_transfer.py',
  'production_auth.py','arch_verify.py','update_routes.py',
  '.pre-commit-config.yaml','.gitattributes','requirements.txt','README.md'
)

# 3) Паттерны «времянок/фиксов/бэкапов»
$Patterns = @(
  # базовые
  '*backup*.*','*_*backup*.*','*_bak.*','*_old.*','*_tmp.*','*.tmp',
  '*scratch*.*','*playground*.*',
  '*fix*.*','*patch*.*','debug_*.*','test_*.*',
  'main_clean.py','main_backup_*.py','*routes*_copy*.*',
  'seed*.py',

  # расширение под твои файлы-скрипты миграций/разовых правок
  'implement_*.py',
  'add_missing_*.py',
  'add_*_routes*.py',
  '*_api_insert.py',
  '*insert*.py',
  'remove_*_final*.py'
)


Write-Host "ROOT: $Root"
Write-Host "ATTIC: $AtticRoot"
Write-Host "DRY RUN: $DryRun`n"

$log = New-Object System.Collections.Generic.List[string]

# 4) «Замораживаем» список файлов и сразу исключаем attic/системные каталоги
$allFiles = Get-ChildItem -Path $Root -Recurse -File -ErrorAction SilentlyContinue | Where-Object {
  $full = $_.FullName
  foreach($pat in $ExcludePatterns){ if ($full -match $pat) { return $false } }
  return $true
}

$allFiles | ForEach-Object {
  $p = $_.FullName

  # не трогаем явно помеченные важные файлы
  if ($KeepFiles -contains $_.Name){ return }

  # решаем, архивировать ли по паттернам
  $match = $false
  foreach($pat in $Patterns){ if ($_.Name -like $pat){ $match = $true; break } }

  if ($match){
    $rel  = $p.Substring($Root.Length).TrimStart('\','/')
    $dest = Join-Path $AtticRoot $rel
    $destDir = Split-Path $dest -Parent
    if (!(Test-Path $destDir)){ New-Item -ItemType Directory -Force -Path $destDir | Out-Null }

    if ($DryRun){
      Write-Host "[would move]" $p "->" $dest
    } else {
      try {
        Move-Item -Force -Path $p -Destination $dest
        Write-Host "[moved]" $p "->" $dest
        $log.Add("$p -> $dest")
      } catch {
        Write-Warning "Failed move: $p -> $dest : $($_.Exception.Message)"
      }
    }
  }
}

if (-not $DryRun) {
  $logPath = Join-Path $AtticRoot "_moved_files.txt"
  $log | Set-Content -Encoding UTF8 $logPath
  Write-Host "Log saved to $logPath"

  if ($Zip) {
    try {
      Add-Type -AssemblyName System.IO.Compression.FileSystem
      $zipPath = "$AtticRoot.zip"
      [System.IO.Compression.ZipFile]::CreateFromDirectory($AtticRoot, $zipPath)
      Write-Host "Zipped to $zipPath"
    } catch {
      Write-Warning "Zip failed: $($_.Exception.Message)"
    }
  }
}
