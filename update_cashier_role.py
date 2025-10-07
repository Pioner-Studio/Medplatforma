from main import db
from bson.objectid import ObjectId

print("=== ОБНОВЛЕНИЕ РОЛИ НАКОНЕЧНОГО А.В. ===\n")

# Найти Наконечного
user = db.users.find_one({"login": "nakonechny"})

if user:
    print(f"Найден: {user['full_name']}")
    print(f"Текущая роль: {user.get('role', 'Нет роли')}")
    print(f"Флаг кассира: {user.get('can_confirm_transfers', False)}")

    # Обновить
    result = db.users.update_one(
        {"_id": user["_id"]}, {"$set": {"role": "admin", "can_confirm_transfers": True}}
    )

    print(f"\n✓ Обновлено записей: {result.modified_count}")

    # Проверка
    updated = db.users.find_one({"_id": user["_id"]})
    print(f"✓ Новая роль: {updated['role']}")
    print(f"✓ Может подтверждать переводы: {updated['can_confirm_transfers']}")
else:
    print("❌ Пользователь nakonechny не найден!")

print("\n=== ГОТОВО ===")
