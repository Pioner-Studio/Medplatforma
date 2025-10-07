param(
  [string]$CalTxt = ".\artifacts\calendar.html.txt",
  [string]$OutDir = ".\docs\evidence\rooms_panel",
  [int]$Pre = 40,
  [int]$Post = 40
)

function Ensure-OutDir([string]$p){ if(-not(Test-Path $p -PathType Container)){ New-Item -ItemType Directory -Path $p | Out-Null } }

function Read-Text([string]$p){
  if (-not (Test-Path $p -PathType Leaf)) { throw "Не найден файл: $p" }
  return Get-Content -Path $p -Raw
}
function Split-Lines($text){ return ($text -split "`n") }

function LineFromIndex($text, [int]$idx){
  if ($idx -lt 0) { return 0 }
  $slice = $text.Substring(0, [Math]::Min($idx, $text.Length))
  return ($slice -split "`n").Count - 1
}

function Dump-Context([string[]]$lines, [int]$lineIdx, [int]$pre, [int]$post){
  $start = [Math]::Max(0, $lineIdx - $pre)
  $end   = [Math]::Min($lines.Count - 1, $lineIdx + $post)
  return $lines[$start..$end]
}

function Find-And-Write([string]$text, [string[]]$patterns, [string]$outPath, [string]$hint){
  $lines = Split-Lines $text
  $found = $false
  foreach($pat in $patterns){
    $rx = [regex]$pat
    $m = $rx.Match($text)
    if($m.Success){
      $lineIdx = LineFromIndex $text $m.Index
      $ctx = Dump-Context $lines $lineIdx $Pre $Post
      $ctx | Set-Content -Path $outPath -Encoding UTF8
      $found = $true
      break
    }
  }
  if(-not $found){
    @(
      "// not found automatically"
      ("// hint: {0}" -f $hint)
      ("// tried patterns: {0}" -f ($patterns -join " | "))
    ) | Set-Content -Path $outPath -Encoding UTF8
  }
}

# main
Ensure-OutDir $OutDir
$text = Read-Text $CalTxt

# 1) Hover/click handler (заголовок кабинета)
$pat_hover = @(
  '(?i)\.on\s*\(\s*["''](?:mouseenter|mouseover|click)["'']',              # jQuery делегирование
  '(?i)addEventListener\s*\(\s*["''](?:mouseenter|mouseover|click)["'']',   # addEventListener
  '(?i)(mouseenter|mouseover|click)\s*[:=]\s*function',                      # объектные хэндлеры
  '(?i)\.room(?:-title)?'                                                    # fallback: упоминание селектора
)
Find-And-Write $text $pat_hover (Join-Path $OutDir "code_hover_handler.js") `
  "Ищи обработчики mouseenter/mouseover/click по .room/.room-title или контейнер .rooms"

# 2) Запрос слотов и сбор тултипа
$pat_slots = @(
  '(?is)(fetch|axios|\$\.get|\$\.ajax).*?(free[_-]?slots|/api/rooms|/api/free_slots)'
)
Find-And-Write $text $pat_slots (Join-Path $OutDir "code_free_slots_and_tip.js") `
  "В этом участке рядом с запросом к free_slots ищи рендер тултипа"

# 3) Шаблон/функция тултипа
$pat_tip = @(
  '(?i)Свобод|Занят',                          # русские слова
  '(?i)tooltip|tip|showRoomTip|updateTip'      # англ. ключи
)
Find-And-Write $text $pat_tip (Join-Path $OutDir "code_tip_template.js") `
  "Функция/шаблон, где собирается HTML с надписью «Свободен/Занят»"

# 4) Конфиг рабочего дня и шаг слота
$pat_work = @(
  '(?i)WORK_(START|END)',
  '(?i)workday|clinic(Start|End)',
  '(?i)\b(SLOT|STEP|minutesPerSlot)\b'
)
Find-And-Write $text $pat_work (Join-Path $OutDir "code_workday_config.js") `
  "Константы границ рабочего дня и шаг слота (например, WORK_START, minutesPerSlot)"

# 5) Временные утилиты
$pat_time = @(
  '(?i)parseTime|formatTime|minToHHMM|hhmmToMinutes|nowMinutes'
)
Find-And-Write $text $pat_time (Join-Path $OutDir "code_time_utils.js") `
  "Функции конвертации времени (строка ⇄ минуты) и текущее время"

Write-Host ("OK -> " + (Resolve-Path -Relative $OutDir))
