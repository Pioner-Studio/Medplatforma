# Скрипт обновления документации
Write-Host "=== ОБНОВЛЕНИЕ ДОКУМЕНТАЦИИ ===" -ForegroundColor Green

# 1. Чек-лист
Write-Host "`n[1/4] Обновление чек-листа..." -ForegroundColor Yellow
$text1 = "`n`n### ЛЬГОТНЫЙ ПРАЙС ДЛЯ СОТРУДНИКОВ/ДРУЗЕЙ`n- ✅ База данных - поля preferential_price в services, use_preferential_pricing в patients`n- ✅ Форма услуги - поле льготная цена`n- ✅ Галочка в карточке пациента`n- ✅ Автоматическое применение льготной цены`n- ✅ Протестировано: 5000₽ → 2500₽`n"
Add-Content -Path "documents\Чек-лист 26.09.md" -Value $text1 -Encoding UTF8
Write-Host "✅ Готово" -ForegroundColor Green

# 2. Архитектура
Write-Host "`n[2/4] Обновление архитектуры..." -ForegroundColor Yellow
$text2 = "`n`n## ОБНОВЛЕНИЕ 27.09.2025: ЛЬГОТНЫЙ ПРАЙС`n`nservices.preferential_price → routes_finance.add_post() → проверка patients.use_preferential_pricing → выбор цены → ledger.amount`n"
Add-Content -Path "documents\АРХИТЕКТУРА СВЯЗЕЙ МЕДПЛАТФОРМЫ.md" -Value $text2 -Encoding UTF8
Write-Host "✅ Готово" -ForegroundColor Green

# 3. Рабочий протокол
Write-Host "`n[3/4] Обновление протокола..." -ForegroundColor Yellow
$text3 = "`n`n## РАБОТА С ОШИБКАМИ`n### После устранения ошибки фиксировать в АРХИВЕ ОШИБОК`n### При создании связей регистрировать в АРХИТЕКТУРЕ`n"
Add-Content -Path "documents\РАБОЧИЙ ПРОТОКОЛ ДЛЯ РАЗРАБОТКИ МЕДПЛАТФОРМЫ.md" -Value $text3 -Encoding UTF8
Write-Host "✅ Готово" -ForegroundColor Green

# 4. Архив ошибок
Write-Host "`n[4/4] Создание архива ошибок..." -ForegroundColor Yellow
$text4 = "# АРХИВ ОШИБОК 27.09.2025`n`n## ОШИБКА 1: UndefinedError form`nРешение: item→form в edit_service`n`n## ОШИБКА 2: Льготная цена не применяется`nРешение: исправлены отступы в routes_finance.py`n"
Set-Content -Path "documents\АРХИВ ОШИБОК И РЕШЕНИЙ 27.09.2025.md" -Value $text4 -Encoding UTF8
Write-Host "✅ Готово" -ForegroundColor Green

Write-Host "`n=== ЗАВЕРШЕНО: 4 файла обновлено ===" -ForegroundColor Green
