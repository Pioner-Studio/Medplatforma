# Скрипт очистки временного кода
$file = "main.py"
$content = Get-Content $file -Raw

# Удалить тестовый роут /test-session
$content = $content -replace '(?s)@app\.route\("/test-session"\).*?return jsonify.*?\n\n', ''

# Удалить тестовый роут /test-treatment-plan  
$content = $content -replace '(?s)@app\.route\("/test-treatment-plan"\).*?return f"<h1>.*?</h1>"\n\n', ''

# Удалить строку с print LOADING
$content = $content -replace 'print\(">>> LOADING treatment_plan_new_get FUNCTION <<<"\)\n\n', ''

# Удалить DEBUG принты в treatment_plan_new_get
$content = $content -replace '\s+# ОТЛАДКА\n\s+print\(f"\[DEBUG\].*?\)\n\s+print\(f"\[DEBUG\].*?\)\n\s+print\(f"\[DEBUG\].*?\)\n', "`n"

$content | Set-Content $file -Encoding utf8

Write-Host "✓ Временный код удален из main.py" -ForegroundColor Green
