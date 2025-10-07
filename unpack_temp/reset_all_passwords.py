from main import db
from werkzeug.security import generate_password_hash

print("=== СБРОС ПАРОЛЕЙ ВСЕХ ПОЛЬЗОВАТЕЛЕЙ ===\n")

# Новые пароли (простые для тестирования)
users_passwords = {
    "gogueva": "123456",
    "nakonechny": "123456",
    "nakonechnaya": "123456",
    "ayvazyan": "123456",
    "kurdov": "123456",
    "kalachev": "123456",
    "mirgatiya": "123456",
    "Aksenova": "123456",
}

updated = 0
errors = 0

for login, password in users_passwords.items():
    try:
        # Найти пользователя
        user = db.users.find_one({"login": login})

        if not user:
            print(f"⚠️ Пользователь {login} не найден")
            continue

        # Сгенерировать хэш пароля
        password_hash = generate_password_hash(password, method="pbkdf2:sha256")

        # Обновить в БД
        result = db.users.update_one(
            {"_id": user["_id"]},
            {
                "$set": {"password": password_hash, "password_hash": password_hash},
                "$unset": {"pwd": ""},  # Удалить старое поле если есть
            },
        )

        if result.modified_count > 0:
            print(f"✓ {user.get('full_name', login)}: пароль обновлен")
            updated += 1
        else:
            print(f"- {user.get('full_name', login)}: не требовалось обновление")

    except Exception as e:
        print(f"❌ Ошибка для {login}: {e}")
        errors += 1

print(f"\n=== ИТОГО ===")
print(f"Обновлено: {updated}")
print(f"Ошибок: {errors}")
print(f"\n⚠️ ВАЖНО: Все пароли теперь 123456")
print(f"Измените их после первого входа!")
