Отлично — твой последний отчёт уже содержит всё нужное: **дерево каталогов**, **маршруты с методами**, **шаблоны по папкам**, и **frontend API-вызовы**.&#x20;
Ниже даю готовый гайд (**drop-in файл**) + «быструю команду» для запуска.

---

# 📄 docs/EXPORTS\_GUIDE.md *(drop-in, скопируй целиком в `docs/`)*

````md
# 🚀 Гайд по выгрузкам (Routes + Templates + Tree + Front API)

Цель: в один клик получать файл с:
- **Directory tree** (отфильтрованное дерево «папка → файлы»)
- **Flask routes с методами** (GET/POST/PUT/PATCH/DELETE/…)
- **Шаблоны HTML** по папкам
- **Frontend API calls** (fetch/axios/jQuery)

## Быстрый запуск

```powershell
# из корня проекта
.\scripts\export_routes_front_tree.ps1
````

Результат: `artifacts/ROUTES_METHODS_FRONT_AND_TREE.md`

> Если файла/скрипта нет — см. «Установка одной командой» ниже.

---

## Что внутри отчёта

1. **Directory tree (filtered)** — дерево всех рабочих файлов (мусорные папки исключены).
2. **Flask routes with methods** — каждый маршрут и метод(ы), с путём к файлу и номером строки.
3. **Templates grouped by folder** — все `templates/*.html` с разбивкой по папкам.
4. **Frontend API calls** — все обращения фронта к API в `templates/*.html` и `static/js/*.js`.

---

## Полный снимок проекта (включая Seeds/Fixtures)

Когда нужен полный обзор всего проекта (включая SEED-файлы и фикстуры):

```powershell
# из корня проекта
.\scripts\export_project_snapshot.ps1
```

Результат: `artifacts/PROJECT_SNAPSHOT_FULL.md`

---

## Если календарь не получается выгрузить как .html

Иногда загрузка `.html` даёт «неизвестную ошибку». Тогда шлём календарь как текст/markdown:

**Вариант A — TXT (надёжно):**

```powershell
Get-Content .\templates\calendar.html -Raw | Set-Content .\artifacts\calendar.html.txt -Encoding UTF8
```

**Вариант B — Markdown с подсветкой:**

````powershell
"```html" | Set-Content .\artifacts\calendar_full.md -Encoding utf8
Get-Content .\templates\calendar.html -Raw | Add-Content .\artifacts\calendar_full.md -Encoding utf8
"```" | Add-Content .\artifacts\calendar_full.md -Encoding utf8
````

**(Опционально) Разбить на части, если файл слишком большой:**

```powershell
$src = Get-Content .\templates\calendar.html
$chunk = 3000; $i=0
for ($off=0; $off -lt $src.Count; $off += $chunk) {
  $part = $src[$off..([Math]::Min($off+$chunk-1,$src.Count-1))]
  $i++; $part | Set-Content (".\artifacts\calendar_part_{0:000}.txt" -f $i) -Encoding UTF8
}
```

---

## Установка одной командой (если скриптов ещё нет)

```powershell
# создаёт/обновит скрипт отчёта и сразу запустит его
New-Item -ItemType Directory -Path .\scripts -Force | Out-Null
@'
param(
  [string]$OutDir  = ".\artifacts",
  [string]$OutName = "ROUTES_METHODS_FRONT_AND_TREE.md"
)
$ExcludeDirs  = @(".\.git",".\.venv",".\artifacts",".\node_modules",".\__pycache__", ".\dist",".\build",".\logs",".\WAN",".\.pytest_cache",".\.mypy_cache",".\.idea",".\.vscode")
$ExcludeGlobs = @("*\__pycache__\*","*\site-packages\*","*.map","*.min.*","*.log")

if (-not (Test-Path $OutDir -PathType Container)) { New-Item -ItemType Directory -Path $OutDir | Out-Null }
$outFile = Join-Path $OutDir $OutName
"" | Set-Content -Path $outFile -Encoding utf8
$ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
"<!-- GENERATED: $ts -->" | Add-Content $outFile -Encoding utf8
"# Routes + Front calls + Directory tree" | Add-Content $outFile -Encoding utf8
"" | Add-Content $outFile -Encoding utf8
function Add-Section([string]$title) { "# $title" | Add-Content $outFile -Encoding utf8; "~~~text" | Add-Content $outFile -Encoding utf8 }
function End-Section() { "~~~" | Add-Content $outFile -Encoding utf8; Add-Content $outFile "`n---`n" -Encoding utf8 }

$rootFull = (Resolve-Path ".").Path
$allFiles = Get-ChildItem -Path $rootFull -Recurse -Force -File -ErrorAction SilentlyContinue
$ExcFull = @(); foreach ($d in $ExcludeDirs) { if (Test-Path $d -PathType Container) { $ExcFull += (Resolve-Path $d).Path } }
$allFiles = $allFiles | Where-Object { $p=$_.FullName; -not ($ExcFull | Where-Object { $p.StartsWith($_,[System.StringComparison]::OrdinalIgnoreCase) }) }
foreach ($g in $ExcludeGlobs) { $allFiles = $allFiles | Where-Object { $_.FullName -notlike $g } }
$allFiles = $allFiles | Sort-Object FullName -Unique

# ---- Directory tree
Add-Section "Directory tree (filtered)"
$dirs = $allFiles | ForEach-Object { $_.DirectoryName } | Sort-Object -Unique
foreach ($dir in $dirs) {
  try { $relDir = Resolve-Path -Relative $dir } catch { $relDir = $dir }
  ("{0}" -f $relDir) | Add-Content $outFile -Encoding utf8
  $filesIn = $allFiles | Where-Object { $_.DirectoryName -eq $dir } | Sort-Object Name
  foreach ($f in $filesIn) { ("  - {0}  ({1} KB)" -f $f.Name, [math]::Round($f.Length/1kb,2)) | Add-Content $outFile -Encoding utf8 }
  "" | Add-Content $outFile -Encoding utf8
}
End-Section

# ---- Routes with methods
Add-Section "Flask routes with methods"
$pyFiles = $allFiles | Where-Object { $_.Extension -eq ".py" } | Sort-Object FullName
$rxVerb  = [regex]'(?m)@(?<obj>[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)\.(?<verb>get|post|put|patch|delete|options|head)\(\s*["''](?<path>[^"'']+)["'']'
$rxRoute = [regex]'(?s)@(?<obj>[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)\.route\(\s*["''](?<path>[^"'']+)["'']\s*(?:,\s*methods\s*=\s*(?<methods>\[[^\]]+\]|\([^)]+\)|\{[^}]+\}))?'
$rxAdd   = [regex]'(?s)\.add_url_rule\(\s*["''](?<path>[^"'']+)["'']\s*(?:,\s*methods\s*=\s*(?<methods>\[[^\]]+\]|\([^)]+\)|\{[^}]+\}))?'
function Get-LineNumber([string]$text, [int]$index) { if ($index -lt 0) { return 1 }; (($text.Substring(0,[Math]::Min($index,$text.Length))) -split "`n").Count }
function Parse-Methods([string]$raw) { if (-not $raw) { return @("GET") }; $vals = @([regex]::Matches($raw,'(?i)GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD') | ForEach-Object { $_.Value.ToUpper() } | Sort-Object -Unique); if ($vals.Count -eq 0) { @("GET") } else { $vals } }
$summary = [ordered]@{ GET=0; POST=0; PUT=0; PATCH=0; DELETE=0; OPTIONS=0; HEAD=0 }
foreach ($f in $pyFiles) {
  $txt = Get-Content $f.FullName -Raw -ErrorAction SilentlyContinue; if (-not $txt) { continue }
  $rel = (Resolve-Path -Relative $f.FullName)
  foreach ($m in $rxVerb.Matches($txt)) { $ln=Get-LineNumber $txt $m.Index; $verb=$m.Groups['verb'].Value.ToUpper(); $path=$m.Groups['path'].Value; ("{0}:L{1}: {2} {3}" -f $rel,$ln,$verb,$path) | Add-Content $outFile; $summary[$verb]++ }
  foreach ($m in $rxRoute.Matches($txt)) { $ln=Get-LineNumber $txt $m.Index; $path=$m.Groups['path'].Value; foreach ($method in (Parse-Methods $m.Groups['methods'].Value)) { ("{0}:L{1}: {2} {3}" -f $rel,$ln,$method,$path) | Add-Content $outFile; $summary[$method]++ } }
  foreach ($m in $rxAdd.Matches($txt))   { $ln=Get-LineNumber $txt $m.Index; $path=$m.Groups['path'].Value; foreach ($method in (Parse-Methods $m.Groups['methods'].Value)) { ("{0}:L{1}: {2} {3}" -f $rel,$ln,$method,$path) | Add-Content $outFile; $summary[$method]++ } }
}
End-Section

Add-Section "Routes summary by method"
foreach ($k in $summary.Keys) { ("{0}: {1}" -f $k, $summary[$k]) | Add-Content $outFile }
End-Section

# ---- Templates
Add-Section "Templates grouped by folder"
$tplFiles = $allFiles | Where-Object { $_.Extension -eq ".html" -and $_.FullName -like "*\templates\*" } | Sort-Object DirectoryName, Name
if ($tplFiles) {
  $curr = ""
  foreach ($t in $tplFiles) {
    $rel = (Resolve-Path -Relative $t.FullName); $dir = Split-Path $rel -Parent
    if ($dir -ne $curr) { "" | Add-Content $outFile; ">>> $dir" | Add-Content $outFile; $curr = $dir }
    ("  - {0}  ({1} KB)" -f (Split-Path $rel -Leaf), [math]::Round($t.Length/1kb,2)) | Add-Content $outFile
  }
} else { "No templates found." | Add-Content $outFile }
End-Section

# ---- Frontend API calls
Add-Section "Frontend API calls (fetch/axios/jQuery)"
$webFiles = @(); if (Test-Path .\templates) { $webFiles += Get-ChildItem .\templates -Recurse -Filter *.html -File -ErrorAction SilentlyContinue }
if (Test-Path .\static\js) { $webFiles += Get-ChildItem .\static\js -Recurse -Filter *.js -File -ErrorAction SilentlyContinue }
$rxFetch = [regex]'(?i)fetch\(\s*["''](?<url>[^"'']+)["''](?:\s*,\s*\{[^}]*\bmethod\s*:\s*["''](?<method>GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD)["''])?'
$rxAxios = [regex]'(?i)axios\.(?<verb>get|post|put|patch|delete|options|head)\(\s*["''](?<url>[^"'']+)["'']'
$rxAjaxU = [regex]'(?is)\$\.ajax\(\s*\{[^}]*\burl\s*:\s*["''](?<url>[^"'']+)["'']'
$rxAjaxT = [regex]'(?i)\btype\s*:\s*["''](?<type>GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD)["'']'
foreach ($f in ($webFiles | Sort-Object FullName)) {
  $text = Get-Content $f.FullName -Raw -ErrorAction SilentlyContinue; if (-not $text) { continue }
  $rel = (Resolve-Path -Relative $f.FullName)
  foreach ($m in $rxFetch.Matches($text)) { $ln = ($text.Substring(0,[Math]::Min($m.Index,$text.Length)) -split "`n").Count; $method = if ($m.Groups['method'].Success) { $m.Groups['method'].Value.ToUpper() } else { "GET" }; ("{0}:L{1}: {2} {3}" -f $rel,$ln,$method,$m.Groups['url'].Value) | Add-Content $outFile }
  foreach ($m in $rxAxios.Matches($text)) { $ln = ($text.Substring(0,[Math]::Min($m.Index,$text.Length)) -split "`n").Count; $method = $m.Groups['verb'].Value.ToUpper(); ("{0}:L{1}: {2} {3}" -f $rel,$ln,$method,$m.Groups['url'].Value) | Add-Content $outFile }
  foreach ($m in $rxAjaxU.Matches($text)) { $ln = ($text.Substring(0,[Math]::Min($m.Index,$text.Length)) -split "`n").Count; $win = $text.Substring($m.Index, [Math]::Min(500, $text.Length - $m.Index)); $typeMatch = $rxAjaxT.Match($win); $method = if ($typeMatch.Success) { $typeMatch.Groups['type'].Value.ToUpper() } else { "GET" }; ("{0}:L{1}: {2} {3}" -f $rel,$ln,$method,$m.Groups['url'].Value) | Add-Content $outFile }
}
End-Section
'@ | Set-Content -Path .\scripts\export_routes_front_tree.ps1 -Encoding UTF8
.\scripts\export_routes_front_tree.ps1
```

---

## «Быстрая команда» (alias)

Чтобы запускать отчёт коротко — командой `exp`, на текущую сессию:

```powershell
Set-Alias exp ".\scripts\export_routes_front_tree.ps1"
# теперь достаточно написать:
exp
```

> По желанию это можно добавить в профиль PowerShell, чтобы alias жил всегда.

---

## Правила фиксации

* В чек-лист записываем пункт выполненным **только после подтверждения** (текст-команда или скрин).
* Всегда присылай файлы из `artifacts/` (я читаю их целиком и даю drop-in/патчи с якорями).

```
```
