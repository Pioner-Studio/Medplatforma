param([switch]$Push)

python tools/generate_docs.py --zip

git add docs/ checklist.md docs.zip
git commit -m "docs: auto-update $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
if ($Push) { git push }
