param(
  [string]$Calendar = ".\templates\calendar.html",
  [string]$OutDir   = ".\artifacts",
  [string[]]$Symbols = @("ROOM_HEADER_SLOTS","TOOLTIP_SLOTS","ROOM_HEADER_FMT"),
  [string[]]$Patterns = @(),   # e.g. "(?i)\bevents\s*:", "(?i)eventSources", "(?i)/api/events"
  [int]$Pre = 6,
  [int]$Post = 24,
  [switch]$All,                # also include ALL UPPER_CASE const/let/var from the file
  [string]$OutName = "CALENDAR_SYMBOLS.md"
)

if (-not (Test-Path $Calendar -PathType Leaf)) { Write-Error "Calendar not found: $Calendar"; exit 1 }
if (-not (Test-Path $OutDir -PathType Container)) { New-Item -ItemType Directory -Path $OutDir | Out-Null }
$rep = Join-Path $OutDir $OutName

$text  = Get-Content -Path $Calendar -Raw
$lines = $text -split "`n"

function W-Section([string]$title){ "# $title" | Add-Content $rep -Encoding UTF8; "" | Add-Content $rep -Encoding UTF8 }
function W-Code([string[]]$arr,[string]$lang="js"){
  "```$lang" | Add-Content $rep -Encoding UTF8
  if ($arr) { $arr | Add-Content $rep -Encoding UTF8 }
  "```" | Add-Content $rep -Encoding UTF8
  "" | Add-Content $rep -Encoding UTF8
}

"" | Set-Content $rep -Encoding UTF8
Add-Content $rep "<!-- GENERATED: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') -->" -Encoding UTF8
Add-Content $rep "# Calendar symbols report" -Encoding UTF8
Add-Content $rep ("Source: {0}" -f (Resolve-Path -Relative $Calendar)) -Encoding UTF8
Add-Content $rep "" -Encoding UTF8

# Auto-collect all UPPER_CASE const/let/var if requested
if ($All) {
  $upper = @()
  $rxUpper = [regex]'(?m)^\s*(?:const|let|var)\s+([A-Z][A-Z0-9_]+)\s*='
  foreach ($m in $rxUpper.Matches($text)) { $upper += $m.Groups[1].Value }
  if ($upper.Count -gt 0) { $Symbols = ($Symbols + $upper | Sort-Object -Unique) }
}

# Custom regex patterns (arbitrary queries)
if ($Patterns -and $Patterns.Count -gt 0) {
  W-Section "Custom pattern matches"
  foreach($pat in $Patterns){
    Add-Content $rep ("### pattern: {0}" -f $pat) -Encoding UTF8
    $rx = [regex]$pat
    $hits = $rx.Matches($text)
    if ($hits.Count -eq 0){ Add-Content $rep "_no matches_" -Encoding UTF8; "" | Add-Content $rep; continue }
    foreach($h in $hits){
      $ln = ($text.Substring(0,[Math]::Min($h.Index,$text.Length)) -split "`n").Count
      $s=[Math]::Max(0,$ln-1-$Pre); $e=[Math]::Min($lines.Count-1,$ln-1+$Post)
      Add-Content $rep ("- @L{0}" -f $ln) -Encoding UTF8
      W-Code $lines[$s..$e] "js"
    }
  }
}

# Per-symbol: definitions + usages
foreach ($sym in ($Symbols | Sort-Object -Unique)) {
  W-Section ("Symbol: {0}" -f $sym)

  # Definitions
  Add-Content $rep "### Definitions" -Encoding UTF8
  $defs = New-Object System.Collections.Generic.List[object]
  $rxDef1 = [regex]("(?m)^\s*(?:const|let|var)\s+" + [regex]::Escape($sym) + "\s*=\s*.+$")
  $rxDef2 = [regex]("(?m)" + [regex]::Escape($sym) + "\s*:\s*.+$")
  foreach ($rx in @($rxDef1,$rxDef2)){
    foreach($m in $rx.Matches($text)){
      $ln = ($text.Substring(0,[Math]::Min($m.Index,$text.Length)) -split "`n").Count
      $s=[Math]::Max(0,$ln-1-$Pre); $e=[Math]::Min($lines.Count-1,$ln-1+$Post)
      $defs.Add([PSCustomObject]@{ line=$ln; ctx=$lines[$s..$e] }) | Out-Null
    }
  }
  if ($defs.Count -gt 0){
    foreach($d in $defs | Sort-Object line){ Add-Content $rep ("- @L{0}" -f $d.line) -Encoding UTF8; W-Code $d.ctx "js" }
  } else { Add-Content $rep "_no definitions found_" -Encoding UTF8; "" | Add-Content $rep -Encoding UTF8 }

  # Usages
  Add-Content $rep "### Usages" -Encoding UTF8
  $rxUse = [regex]("(?m)\b" + [regex]::Escape($sym) + "\b")
  $useHits = $rxUse.Matches($text)
  if ($useHits.Count -gt 0){
    $seen = New-Object 'System.Collections.Generic.HashSet[int]'
    foreach($m in $useHits){
      $ln = ($text.Substring(0,[Math]::Min($m.Index,$text.Length)) -split "`n").Count
      if (-not $seen.Add($ln)) { continue }
      $s=[Math]::Max(0,$ln-1-$Pre); $e=[Math]::Min($lines.Count-1,$ln-1+$Post)
      Add-Content $rep ("- @L{0}" -f $ln) -Encoding UTF8
      W-Code $lines[$s..$e] "js"
    }
  } else { Add-Content $rep "_no usages found_" -Encoding UTF8; "" | Add-Content $rep -Encoding UTF8 }
}

Write-Host ("OK -> " + $rep)
