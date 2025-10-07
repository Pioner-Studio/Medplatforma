Param(
  [string]$Root=".", [string]$Attic="attic", $DryRun=$true, $Zip=$false
)
function To-Bool([object]$v,[bool]$d=$false){ if($v -is [bool]){return $v}; if($v -is [int]){return [bool]$v}; if($null -eq $v){return $d}; $s=($v.ToString()).ToLower().Trim(); switch($s){'true'{$true}'false'{$false}'1'{$true}'0'{$false}'yes'{$true}'no'{$false}'on'{$true}'off'{$false} default{$d}}}
$DryRun=To-Bool $DryRun $true; $Zip=To-Bool $Zip $false
$Root=(Resolve-Path $Root).Path; $ts=Get-Date -Format "yyyyMMdd_HHmmss"; $AtticRoot=Join-Path (Join-Path $Root $Attic) $ts; New-Item -ItemType Directory -Force -Path $AtticRoot|Out-Null
$Exclude=@("\\attic(\\|$)","\\.git(\\|$)","\\.venv(\\|$)","\\venv(\\|$)","\\env(\\|$)","\\node_modules(\\|$)","\\__pycache__(\\|$)","\\.pytest_cache(\\|$)","\\.mypy_cache(\\|$)","\\dist(\\|$)","\\build(\\|$)","\\.idea(\\|$)","\\.vscode(\\|$)")
$Keep=@('main.py','routes_schedule.py','routes_finance.py','routes_transfer.py','production_auth.py','arch_verify.py','update_routes.py','.pre-commit-config.yaml','.gitattributes','requirements.txt','README.md')
$Patterns=@('*backup*.*','*_*backup*.*','*_bak.*','*_old.*','*_tmp.*','*.tmp','*scratch*.*','*playground*.*','*fix*.*','*patch*.*','debug_*.*','test_*.*','main_clean.py','main_backup_*.py','*routes*_copy*.*','seed*.py','implement_*.py','integrate_*.py','integration_*.py','add_missing_*.py','add_*_routes*.py','add_*_api*.py','*_api_insert.py','*insert*.py','remove_*_final*.py')
$all=Get-ChildItem -Path $Root -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $f=$_.FullName; foreach($p in $Exclude){ if($f -match $p){return $false} } $true }
$log=New-Object System.Collections.Generic.List[string]
foreach($it in $all){
  if($Keep -contains $it.Name){ continue }
  $arc=$false; foreach($pat in $Patterns){ if($it.Name -like $pat){ $arc=$true; break } }
  if($arc){
    $rel=$it.FullName.Substring($Root.Length).TrimStart('\','/'); $dest=Join-Path $AtticRoot $rel; $dd=Split-Path $dest -Parent
    if(!(Test-Path $dd)){ New-Item -ItemType Directory -Force -Path $dd|Out-Null }
    if($DryRun){ Write-Host "[would move]" $it.FullName "->" $dest } else { try{ Move-Item -Force -Path $it.FullName -Destination $dest; Write-Host "[moved]" $it.FullName "->" $dest; $log.Add("$($it.FullName) -> $dest") }catch{ Write-Warning "Failed move: $($it.FullName) -> $dest : $($_.Exception.Message)" } }
  }
}
if(-not $DryRun){
  $logPath=Join-Path $AtticRoot "_moved_files.txt"; $log | Set-Content -Encoding UTF8 $logPath; Write-Host "Log saved to $logPath"
  if($Zip){ try{ Add-Type -AssemblyName System.IO.Compression.FileSystem; $zipPath="$AtticRoot.zip"; [System.IO.Compression.ZipFile]::CreateFromDirectory($AtticRoot,$zipPath); Write-Host "Zipped to $zipPath" }catch{ Write-Warning "Zip failed: $($_.Exception.Message)" } }
}
