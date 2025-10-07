# fix_javascript_api_route.py
# Меняем JavaScript чтобы использовал правильный API

with open("templates/calendar.html", "r", encoding="utf-8") as f:
    content = f.read()

# Заменяем старый API на новый
content = content.replace('dictsApi: "/api/admin/seed/dicts"', 'dictsApi: "/api/dicts"')

# Сохраняем
with open("templates/calendar.html", "w", encoding="utf-8") as f:
    f.write(content)

print("✅ JavaScript теперь использует /api/dicts вместо /api/admin/seed/dicts")
