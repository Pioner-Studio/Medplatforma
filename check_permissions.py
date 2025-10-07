from main import db

print("=== МАТРИЦА ПРАВ ДОСТУПА ===\n")

roles = {
    "chief_doctor": "Главврач",
    "admin": "Администратор",
    "doctor": "Врач",
    "registrar": "Регистратор",
}

print("| Пользователь | Роль | Права |")
print("|--------------|------|-------|")

for user in db.users.find({}, {"full_name": 1, "role": 1, "can_confirm_transfers": 1}).sort(
    "role", 1
):
    name = user.get("full_name", "Без имени")[:30]
    role = roles.get(user.get("role"), user.get("role", "Нет роли"))

    permissions = []
    if user.get("role") == "chief_doctor":
        permissions.append("Согласование планов")
    if user.get("role") in ["admin", "chief_doctor"]:
        permissions.append("Оплата долгов")
    if user.get("role") == "doctor":
        permissions.append("Создание планов")
    if user.get("can_confirm_transfers"):
        permissions.append("Подтверждение переводов")

    perms_str = ", ".join(permissions) if permissions else "Нет особых прав"
    print(f"| {name} | {role} | {perms_str} |")

print("\n=== ГОТОВО ===")
