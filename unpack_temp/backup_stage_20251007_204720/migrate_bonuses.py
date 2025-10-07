from main import db
from datetime import datetime

# Добавляем поля бонусов всем пациентам
result = db.patients.update_many(
    {"bonus_balance": {"$exists": False}},
    {
        "$set": {
            "bonus_balance": 0,
            "referred_by_patient_id": None,
            "referred_by_name": None,
            "bonus_updated_at": datetime.utcnow(),
        }
    },
)

print(f"Обновлено пациентов: {result.modified_count}")

# Создаём коллекцию bonus_history с индексами
db.bonus_history.create_index([("patient_id", 1), ("ts", -1)])
db.bonus_history.create_index("related_ledger_id")

print("Коллекция bonus_history создана с индексами")
