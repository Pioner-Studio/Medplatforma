Param([switch]$NoPush)

if (-not (Test-Path ".git")) { Write-Error "Запусти из корня репозитория (.git не найден)."; exit 1 }

# --- 1) .gitignore: добавить недостающие правила
$rules = @(
  ".venv/","**/.venv/","venv/","env/","__pycache__/","*.pyc",
  ".venv_bad_*/",".venv_off_*/","unpack_temp/","attic/","exports/","backups/",
  "*.zip","backup_snapshot_*.zip","snapshot_*.zip","docs.zip",
  "*_bak.*","*_old.*","*_tmp.*","*.tmp","debug_*.*","test_*.*","*scratch*.*","*playground*.*",
  "main_clean.py","main.py.backup*","*routes*_copy*.*",
  "seed*.py","*fix*.*","*patch*.*",
  "implement_*.py","integrate_*.py","integration_*.py",
  "add_missing_*.py","add_*_routes*.py","add_*_api*.py","*_api_insert.py","*insert*.py","remove_*_final*.py"
)
$gi = ".gitignore"
$existing = (Test-Path $gi) ? (Get-Content $gi -ErrorAction SilentlyContinue) : @()
$added = @()
foreach($r in $rules){ if(-not ($existing -contains $r)){ Add-Content $gi $r; $added += $r } }
if ($added.Count) { Write-Host "Добавлены в .gitignore:`n  - " ($added -join "`n  - ") } else { Write-Host ".gitignore уже ок" }

# --- 2) Снять мусор из индекса (файлы на диске остаются)
$rx = '(?i)(^|/)(\.venv_bad_.*|unpack_temp/.*|attic/.*|exports/.*|backups/.*|seed.*\.py|.*fix.*\.(py|ps1|txt)|.*patch.*\.(py|ps1)|debug_.*|test_.*|.*_bak\..*|.*_old\..*|.*_tmp\..*|main\.py\.backup.*|main_clean\.py|.*routes.*_copy.*|implement_.*\.py|integrate_.*\.py|integration_.*\.py|add_missing_.*\.py|add_.*_routes.*\.py|add_.*_api.*\.py|.*_api_insert\.py|.*insert.*\.py|remove_.*_final.*|.*backup.*\.(py|html|txt)|.*\.zip)$'
$tracked = @(git ls-files | Where-Object { $_ -match $rx })
if ($tracked.Count) {
  Write-Host "Снимаю из индекса:`n  - " ($tracked -join "`n  - ")
  git rm --cached -- $tracked | Out-Null
} else {
  Write-Host "Мусор в индексе не найден."
}

# --- 3) Перегенерить карту маршрутов и README-карты (если есть Python)
$pyOk = (Get-Command python -ErrorAction SilentlyContinue) -ne $null
if ($pyOk -and (Test-Path "arch_verify.py")) {
  python arch_verify.py --root . --out docs\routes.json
}
if ($pyOk -and (Test-Path "update_routes.py") -and (Test-Path "docs\routes.json")) {
  python update_routes.py
}

# --- 4) Коммит и (опц.) пуш
git add -A
# есть ли staged-изменения?
git diff --cached --quiet; $has = ($LASTEXITCODE -ne 0)
if ($has) {
  git commit -m "chore(clean): .gitignore, untrack junk, refresh routes" --no-verify | Out-Null
} else {
  Write-Host "Нет изменений для коммита."
}

if (-not $NoPush) {
  $branch = (git rev-parse --abbrev-ref HEAD).Trim()
  git push -u origin $branch
  Write-Host "Готово. Пуш в ветку $branch."
} else {
  Write-Host "Готово. Коммит локально (NoPush)."
}
