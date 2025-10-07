# init_database.py
from main import db
from datetime import datetime

print("=== ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ ===\n")

# 1. Создаем индексы для новых коллекций
print("1. Создаю индексы...")

# treatment_plans
db.treatment_plans.create_index("patient_id")
db.treatment_plans.create_index("doctor_id")
db.treatment_plans.create_index("status")
db.treatment_plans.create_index([("status", 1), ("chief_doctor_id", 1)])

# debts
db.debts.create_index("patient_id")
db.debts.create_index("status")
db.debts.create_index([("patient_id", 1), ("status", 1)])

# payments
db.payments.create_index("patient_id")
db.payments.create_index("status")
db.payments.create_index([("status", 1), ("confirmed_by_admin_id", 1)])

# advances
db.advances.create_index("patient_id")
db.advances.create_index("status")

print("✓ Индексы созданы\n")

# 2. Добавляем поля в patients
print("2. Обновляю коллекцию patients...")
result = db.patients.update_many({}, {"$set": {"bonus_balance": 0, "referral_chain": []}})
print(f"✓ Обновлено пациентов: {result.matched_count}\n")

# 3. Проверяем коллекции
print("3. Проверка коллекций:")
collections = {
    "treatment_plans": db.treatment_plans.count_documents({}),
    "debts": db.debts.count_documents({}),
    "payments": db.payments.count_documents({}),
    "advances": db.advances.count_documents({}),
    "patients": db.patients.count_documents({}),
    "users": db.users.count_documents({}),
}

for name, count in collections.items():
    print(f"  {name}: {count} документов")

print("\n=== ИНИЦИАЛИЗАЦИЯ ЗАВЕРШЕНА ===")
