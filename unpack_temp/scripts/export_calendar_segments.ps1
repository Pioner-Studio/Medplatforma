param(
  [string]$CalendarHtml = ".\templates\calendar.html",
  [string]$MainPy       = ".\main.py",
  [string]$OutDir       = ".\artifacts",
  [string]$OutName      = "request_calendar_segments.md"
)

function Ensure-OutFile {
  param([string]$OutDir, [string]$OutName)
  if (-not (Test-Path $OutDir -PathType Container)) { New-Item -ItemType Directory -Path $OutDir | Out-Null }
  $outFile = Join-Path $OutDir $OutName
  "" | Set-Content -Path $outFile -Encoding utf8
  return $outFile
}

function Write-Section {
  param([string]$OutFile,[string]$Title,[string]$Lang,[string[]]$Lines)
  "# $Title"                  | Add-Content -Path $OutFile -Encoding utf8
  ""                          | Add-Content -Path $OutFile -Encoding utf8
  "~~~$Lang"                  | Add-Content -Path $OutFile -Encoding utf8
  if ($Lines) { $Lines | Add-Content -Path $OutFile -Encoding utf8 }
  "~~~"                       | Add-Content -Path $OutFile -Encoding utf8
  ""                          | Add-Content -Path $OutFile -Encoding utf8
  "---"                       | Add-Content -Path $OutFile -Encoding utf8
  ""                          | Add-Content -Path $OutFile -Encoding utf8
}

function BlockByAnchors {
  param([string]$File,[string]$StartMarker,[string]$EndMarker)
  if (-not (Test-Path $File -PathType Leaf)) { return $null }
  $lines = Get-Content -Path $File
  $startMatch = $lines | Select-String -SimpleMatch $StartMarker | Select-Object -First 1
  if (-not $startMatch) { return $null }
  $startLine = $startMatch.LineNumber
  $slice = $lines[($startLine-1)..($lines.Length-1)]
  $endMatch = $slice | Select-String -SimpleMatch $EndMarker | Select-Object -First 1
  if (-not $endMatch) { return $null }
  $endLine = $startLine + $endMatch.LineNumber - 1
  return $lines[($startLine-1)..($endLine-1)]
}

function BlockByPatternWithContext {
  param([string]$File,[string]$Pattern,[int]$Pre,[int]$Post)
  if (-not (Test-Path $File -PathType Leaf)) { return $null }
  $match = Select-String -Path $File -Pattern $Pattern | Select-Object -First 1
  if ($match) {
    $lines = Get-Content -Path $File
    $s = [Math]::Max(1, $match.LineNumber - $Pre)
    $e = [Math]::Min($lines.Length, $match.LineNumber + $Post)
    return $lines[($s-1)..($e-1)]
  }
  return $null
}

$OUT = Ensure-OutFile -OutDir $OutDir -OutName $OutName
$ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
"<!-- GENERATED: $ts -->" | Add-Content -Path $OUT -Encoding utf8
"" | Add-Content -Path $OUT -Encoding utf8

# 1) calendar.html — patient mini-search HTML block
# Preferred anchors:
#   <!-- PATIENT-SEARCH START --> ... <!-- PATIENT-SEARCH END -->
$block1 = BlockByAnchors -File $CalendarHtml -StartMarker "<!-- PATIENT-SEARCH START -->" -EndMarker "<!-- PATIENT-SEARCH END -->"
if (-not $block1) {
  # Fallback: ~10 lines before and 40 after the first input that hints patient/пациент
  $pattern = '(?i)<input[^>]*(patient|пациент)'
  $block1 = BlockByPatternWithContext -File $CalendarHtml -Pattern $pattern -Pre 10 -Post 40
}
if (-not $block1) { $block1 = @("/* NOT FOUND: patient search HTML */") }
Write-Section -OutFile $OUT -Title "calendar.html — patient search HTML" -Lang "html" -Lines $block1

# 2) calendar.html — JS for mini-search
# Preferred anchors:
#   // MINI-SEARCH START ... // MINI-SEARCH END
$block2 = BlockByAnchors -File $CalendarHtml -StartMarker "// MINI-SEARCH START" -EndMarker "// MINI-SEARCH END"
if (-not $block2) {
  # Fallback: from 'MINI-SEARCH' keyword for ~120 lines
  $block2 = BlockByPatternWithContext -File $CalendarHtml -Pattern "(?i)MINI-SEARCH" -Pre 0 -Post 120
}
if (-not $block2) { $block2 = @("/* NOT FOUND: mini-search JS */") }
Write-Section -OutFile $OUT -Title "calendar.html — mini-search JS" -Lang "javascript" -Lines $block2

# 3) calendar.html — events fetch block (events: (...) or eventSources)
# Preferred anchors:
#   /* EVENTS FETCH START */ ... /* EVENTS FETCH END */
$block3 = BlockByAnchors -File $CalendarHtml -StartMarker "/* EVENTS FETCH START */" -EndMarker "/* EVENTS FETCH END */"
if (-not $block3) {
  # Try "events:" object/function
  $block3 = BlockByPatternWithContext -File $CalendarHtml -Pattern "(?i)\bevents\s*:" -Pre 0 -Post 150
}
if (-not $block3) {
  # Or eventSources array
  $block3 = BlockByPatternWithContext -File $CalendarHtml -Pattern "(?i)eventSources" -Pre 0 -Post 150
}
if (-not $block3) { $block3 = @("/* NOT FOUND: events fetch block */") }
Write-Section -OutFile $OUT -Title "calendar.html — events fetch" -Lang "javascript" -Lines $block3

# 4) main.py — GET /api/events handler
# Range: from route decorator to first "return jsonify("
$block4 = $null
if (Test-Path $MainPy -PathType Leaf) {
  $pyLines = Get-Content -Path $MainPy
  $rx = '^\s*@(?:app|[\w_]+)\.route\("/api/events",\s*methods=\["GET"\]\)'
  $routeMatch = Select-String -InputObject $pyLines -Pattern $rx | Select-Object -First 1
  if ($routeMatch) {
    $startLine = $routeMatch.LineNumber
    $slice = $pyLines[($startLine-1)..($pyLines.Length-1)]
    $returnMatch = Select-String -InputObject $slice -Pattern 'return\s+jsonify\(' | Select-Object -First 1
    if ($returnMatch) {
      $endLine = $startLine + $returnMatch.LineNumber - 1
    } else {
      $endLine = [Math]::Min($pyLines.Length, $startLine + 120)
    }
    $block4 = $pyLines[($startLine-1)..($endLine-1)]
  }
}
if (-not $block4) { $block4 = @("# NOT FOUND: @app.route('/api/events', methods=['GET']) block") }
Write-Section -OutFile $OUT -Title "main.py — /api/events handler" -Lang "python" -Lines $block4

Write-Host ("DONE -> " + $OUT)
