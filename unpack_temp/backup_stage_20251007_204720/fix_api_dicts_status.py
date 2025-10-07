# fix_api_dicts_status.py
# Исправляем статус код 400 на 200 в функции api_dicts

with open("main.py", "r", encoding="utf-8") as f:
    content = f.read()

# Заменяем ", 400" на "" в return jsonify
content = content.replace(
    'return jsonify({\n        "ok": True,\n        "doctors": doctors,\n        "services": services,\n        "patients": patients,\n        "rooms": rooms\n    }), 400',
    'return jsonify({\n        "ok": True,\n        "doctors": doctors,\n        "services": services,\n        "patients": patients,\n        "rooms": rooms\n    })',
)

# Сохраняем
with open("main.py", "w", encoding="utf-8") as f:
    f.write(content)

print("✅ Исправлен статус код в api_dicts - теперь возвращает 200 вместо 400")
