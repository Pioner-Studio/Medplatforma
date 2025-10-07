from main import db

print("=== ТЕКУЩЕЕ СОСТОЯНИЕ БД ===\n")

# Коллекции
print("Коллекции:")
print(f"  patients: {db.patients.count_documents({})}")
print(f"  appointments: {db.appointments.count_documents({})}")
print(f"  ledger: {db.ledger.count_documents({})}")
print(f"  users: {db.users.count_documents({})}")
print(f"  doctors: {db.doctors.count_documents({})}")
print(f"  services: {db.services.count_documents({})}")
print()

# Роли пользователей
print("Роли пользователей:")
for user in db.users.find({}, {"full_name": 1, "role": 1, "login": 1}):
    print(
        f"  {user.get('full_name', 'Без имени')}: {user.get('role', 'Нет роли')} (login: {user.get('login', 'N/A')})"
    )
print()

# Проверка существования новых коллекций
print("Новые коллекции (если есть):")
all_collections = db.list_collection_names()
for col in ["treatment_plans", "debts", "payments", "advances"]:
    if col in all_collections:
        count = db[col].count_documents({})
        print(f"  {col}: {count} документов")
    else:
        print(f"  {col}: НЕ СУЩЕСТВУЕТ")
