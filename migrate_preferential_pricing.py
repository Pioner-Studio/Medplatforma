from main import db
from datetime import datetime

print("=== МИГРАЦИЯ: Льготный прайс ===\n")

# 1. Добавляем поле use_preferential_pricing всем пациентам
result_patients = db.patients.update_many(
    {"use_preferential_pricing": {"$exists": False}}, {"$set": {"use_preferential_pricing": False}}
)
print(f"✅ Обновлено пациентов: {result_patients.modified_count}")

# 2. Добавляем поле preferential_price всем услугам (null по умолчанию)
result_services = db.services.update_many(
    {"preferential_price": {"$exists": False}}, {"$set": {"preferential_price": None}}
)
print(f"✅ Обновлено услуг: {result_services.modified_count}")

print("\n=== МИГРАЦИЯ ЗАВЕРШЕНА ===")
