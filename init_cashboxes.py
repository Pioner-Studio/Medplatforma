# init_cashboxes.py
from main import db
from datetime import datetime

# Текущие суммы по источникам из ledger
alpha_balance = sum(
    int(op.get("amount", 0)) for op in db.ledger.find({"kind": "income", "source": "alpha"})
)
sber_balance = sum(
    int(op.get("amount", 0)) for op in db.ledger.find({"kind": "income", "source": "sber"})
)
cash_balance = sum(
    int(op.get("amount", 0)) for op in db.ledger.find({"kind": "income", "source": "cash"})
)

# Вычитаем расходы
alpha_expenses = sum(
    int(op.get("amount", 0))
    for op in db.ledger.find(
        {"kind": {"$in": ["expense", "purchase", "salary"]}, "source": "alpha"}
    )
)
sber_expenses = sum(
    int(op.get("amount", 0))
    for op in db.ledger.find({"kind": {"$in": ["expense", "purchase", "salary"]}, "source": "sber"})
)
cash_expenses = sum(
    int(op.get("amount", 0))
    for op in db.ledger.find({"kind": {"$in": ["expense", "purchase", "salary"]}, "source": "cash"})
)

cashboxes = [
    {
        "_id": "alpha",
        "name": "Альфа-Банк",
        "balance": alpha_balance - alpha_expenses,
        "initial_balance": 0,
        "currency": "RUB",
        "updated_at": datetime.utcnow(),
    },
    {
        "_id": "sber",
        "name": "Сбер",
        "balance": sber_balance - sber_expenses,
        "initial_balance": 0,
        "currency": "RUB",
        "updated_at": datetime.utcnow(),
    },
    {
        "_id": "cash",
        "name": "Наличные",
        "balance": cash_balance - cash_expenses,
        "initial_balance": 0,
        "currency": "RUB",
        "updated_at": datetime.utcnow(),
    },
]

print("Инициализация касс...")
print(f"\nДоходы: Alpha={alpha_balance}₽, Sber={sber_balance}₽, Cash={cash_balance}₽")
print(f"Расходы: Alpha={alpha_expenses}₽, Sber={sber_expenses}₽, Cash={cash_expenses}₽")
print()

for c in cashboxes:
    db.cashboxes.update_one({"_id": c["_id"]}, {"$set": c}, upsert=True)
    print(f"✅ Касса {c['name']}: {c['balance']} ₽")

print(f"\nВсего касс создано: {db.cashboxes.count_documents({})}")
