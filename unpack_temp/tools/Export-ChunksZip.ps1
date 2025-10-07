$ErrorActionPreference='Stop'
function Export-ChunksZip {
  param(
    [Parameter(Mandatory=$true)][string]$Path,       # путь к файлу (html, py и т.д.)
    [Parameter(Mandatory=$true)][string]$Lang,       # 'html' | 'python' | 'javascript' | ...
    [int]$LinesPerChunk = 250,                        # по сколько строк резать
    [string]$OutRoot = "D:\Projects\medplatforma\backups\exports"
  )
  $src = (Resolve-Path -LiteralPath $Path).Path
  $name = [IO.Path]::GetFileName($src)
  $base = [IO.Path]::GetFileNameWithoutExtension($src)
  $stamp = Get-Date -Format 'yyyy-MM-dd_HH-mm'
  $tmpDir = Join-Path $env:TEMP ("chunks_" + [guid]::NewGuid().ToString())
  New-Item -ItemType Directory -Force -Path $tmpDir | Out-Null
  New-Item -ItemType Directory -Force -Path $OutRoot | Out-Null

  # читаем как UTF-8 (чтобы не было кракозябр)
  $text  = Get-Content -LiteralPath $src -Raw -Encoding UTF8
  $lines = $text -split "`r?`n"
  if ($lines.Count -eq 0) { throw "Файл пуст: $src" }

  $total = [math]::Ceiling([double]$lines.Count / $LinesPerChunk)
  $fence = '```'
  $firstPartPath = $null

  for ($i = 0; $i -lt $lines.Count; $i += $LinesPerChunk) {
    $part = [math]::Floor($i / $LinesPerChunk) + 1
    $end  = [Math]::Min($i + $LinesPerChunk - 1, $lines.Count - 1)
    $dest = Join-Path $tmpDir ("{0}_part_{1:000}.txt" -f $base, $part)
    $body = ($lines[$i..$end] -join "`n")
    $hdr  = if ($total -gt 1) { "### $name (часть $part/$total)" } else { "### $name" }
    $txt  = $hdr + "`n" + $fence + $Lang + "`n" + $body + "`n" + $fence
    $txt | Out-File -Encoding utf8 $dest
    if (-not $firstPartPath) { $firstPartPath = $dest }
  }

  $zip = Join-Path $OutRoot ("{0}_{1}_parts.zip" -f $base, $stamp)
  if (Test-Path $zip) { Remove-Item $zip -Force }
  Compress-Archive -Path (Join-Path $tmpDir '*') -DestinationPath $zip -CompressionLevel Optimal

  try { Set-Clipboard -Value (Get-Content -LiteralPath $firstPartPath -Raw) } catch {}
  Remove-Item $tmpDir -Recurse -Force
  Write-Host "ZIP ready: $zip (first part copied to clipboard)"
}
