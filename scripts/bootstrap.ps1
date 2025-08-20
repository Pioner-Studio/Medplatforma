# scripts/bootstrap.ps1
param(
  [switch]$RecreateVenv = $true
)

Write-Host "== ClubStom bootstrap =="

# 1. venv
if ($RecreateVenv) {
  if (Test-Path .\.venv) { Remove-Item -Recurse -Force .\.venv }
  py -0p | Write-Host
  py -m venv .venv
}
.\.venv\Scripts\Activate.ps1

# 2. pip + deps
python -m pip install --upgrade pip
pip install -r requirements.txt

# 3. генерация docs + zip
python tools/generate_docs.py --lint --zip --note "bootstrap on $(hostname)"

Write-Host "== Done =="
