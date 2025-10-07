Param(
  [string]$Root = ".",
  [switch]$DryRun = $true
)

$Root = (Resolve-Path $Root).Path

# Папки, которые НЕЛЬЗЯ трогать
$ExcludeDirs = @(
  "\.git($|\\)", "\.venv($|\\)", "node_modules($|\\)",
  "env($|\\)", "venv($|\\)", "\.idea($|\\)", "\.vscode($|\\)"
)

# Ключевые каталоги/файлы, которые сохраняем
$KeepRoots = @('templates','static','docs','tools')
$KeepFiles = @(
  'main.py','routes_schedule.py','routes_finance.py','routes_transfer.py',
  'production_auth.py','arch_verify.py','update_routes.py',
  '.pre-commit-config.yaml','.gitattributes','requirements.txt','README.md'
)

# Паттерны «мусора»
$Patterns = @(
  '*backup*.*','*_*backup*.*','*_bak.*','*_old.*','*_tmp.*','*.tmp',
  '*scratch*.*','*playground*.*',
  '*fix*.*','*patch*.*','debug_*.*','test_*.*',
  'main_clean.py','main_backup_*.py','*routes*_copy*.*',
  'seed*.py'
)

Write-Host "ROOT: $Root"
Write-Host "DRY RUN: $DryRun`n"

Get-ChildItem -Path $Root -Recurse -File | ForEach-Object {
  $p = $_.FullName

  # 1) Исключаем системные каталоги (быстро отсекаем .venv/.git)
  foreach($dir in $ExcludeDirs){
    if ($p -match $dir) { return }
  }

  # 2) Сохраняем ключевые папки
  foreach($k in $KeepRoots){
    if ($p -match "\\$k(\\|$)") { return }
  }

  # 3) Сохраняем ключевые файлы по имени
  if ($KeepFiles -contains $_.Name) { return }

  # 4) Проверяем на «мусорные» паттерны
  $match = $false
  foreach($pat in $Patterns){
    if ($_.Name -like $pat) { $match = $true; break }
  }

  if ($match){
    if ($DryRun){ Write-Host "[would remove]" $p }
    else {
      try {
        Remove-Item -Force $p
        Write-Host "[removed]" $p
      } catch {
        Write-Warning "Failed remove: $p  -> $($_.Exception.Message)"
      }
    }
  }
}
