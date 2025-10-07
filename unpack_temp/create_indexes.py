from main import db

print("=== СОЗДАНИЕ ИНДЕКСОВ ===\n")

# treatment_plans
print("Создаю индексы для treatment_plans...")
db.treatment_plans.create_index("patient_id")
db.treatment_plans.create_index("doctor_id")
db.treatment_plans.create_index("status")
db.treatment_plans.create_index("chief_doctor_id")
print("✓ treatment_plans")

# debts
print("Создаю индексы для debts...")
db.debts.create_index("patient_id")
db.debts.create_index("treatment_plan_id")
db.debts.create_index("status")
print("✓ debts")

# payments
print("Создаю индексы для payments...")
db.payments.create_index("patient_id")
db.payments.create_index("status")
db.payments.create_index("created_at")
print("✓ payments")

# advances
print("Создаю индексы для advances...")
db.advances.create_index("patient_id")
db.advances.create_index("status")
print("✓ advances")

print("\n=== ВСЕ ИНДЕКСЫ СОЗДАНЫ ===")
