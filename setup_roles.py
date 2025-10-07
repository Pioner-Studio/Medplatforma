# setup_roles.py
from main import db

print("=== НАЗНАЧЕНИЕ РОЛЕЙ ===\n")

# Гогуева А.Т. → chief_doctor
result1 = db.users.update_one(
    {"full_name": "Гогуева Алина Темурлановна"},
    {"$set": {"role": "chief_doctor", "can_confirm_transfers": False}},
)
print(f"✓ Гогуева А.Т. → chief_doctor {'(обновлено)' if result1.modified_count else '(уже было)'}")

# Наконечный А.В. → admin + подтверждение переводов
result2 = db.users.update_one(
    {"full_name": "Наконечный Алексей Владимирович"},
    {"$set": {"role": "admin", "can_confirm_transfers": True}},
)
print(
    f"✓ Наконечный А.В. → admin + касса {'(обновлено)' if result2.modified_count else '(уже было)'}"
)

# Наконечная Е.И. → admin
result3 = db.users.update_one(
    {"full_name": "Наконечная Елена Ивановна"},
    {"$set": {"role": "admin", "can_confirm_transfers": False}},
)
print(f"✓ Наконечная Е.И. → admin {'(обновлено)' if result3.modified_count else '(уже было)'}")

# Все врачи → doctor
result4 = db.users.update_many(
    {
        "full_name": {
            "$in": [
                "Айвазян Альберт Гагикович",
                "Курдов Кадыр Мурадович",
                "Калачев Алексей Николаевич",
                "Миргатия Ольга Сергеевна",
            ]
        }
    },
    {"$set": {"role": "doctor", "can_confirm_transfers": False}},
)
print(f"✓ Врачи → doctor (обновлено: {result4.modified_count})")

print("\n=== РОЛИ НАЗНАЧЕНЫ ===")
print("\nПроверка:")

users = list(db.users.find({}, {"full_name": 1, "role": 1, "can_confirm_transfers": 1}))
for u in users:
    role_str = u.get("role", "НЕТ РОЛИ")
    transfer_str = " + касса" if u.get("can_confirm_transfers") else ""
    print(f"  {u.get('full_name')}: {role_str}{transfer_str}")
