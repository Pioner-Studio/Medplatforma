from main import db

result = db.patients.update_many({}, {"$set": {"debt_balance": 0, "deposit_balance": 0}})
print(f"Обновлено {result.modified_count} пациентов")
