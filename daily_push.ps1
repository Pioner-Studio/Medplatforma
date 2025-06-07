Set-Location -Path "$PSScriptRoot"
git add .
git commit -m ("AutoPush - " + (Get-Date -Format 'dd.MM.yyyy HH:mm'))
git push
