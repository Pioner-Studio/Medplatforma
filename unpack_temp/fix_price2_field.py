#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Исправление: копирование price2 → employee_price
"""

from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["medplatforma"]

# Находим ВСЕ услуги
all_services = list(db.services.find({}))

print(f"Всего услуг: {len(all_services)}")

updated = 0
for svc in all_services:
    # Проверяем есть ли price2
    if "price2" in svc and svc["price2"] is not None:
        # Копируем price2 → employee_price и удаляем price2
        db.services.update_one(
            {"_id": svc["_id"]},
            {"$set": {"employee_price": svc["price2"]}, "$unset": {"price2": 1}},
        )
        updated += 1
        print(f"✅ {svc['name']}: {svc['price2']} → employee_price")
    elif "employee_price" not in svc or svc.get("employee_price") is None:
        # Если нет ни price2, ни employee_price - ставим employee_price = price
        db.services.update_one(
            {"_id": svc["_id"]}, {"$set": {"employee_price": svc.get("price", 0)}}
        )
        print(f"⚠️ {svc['name']}: нет цен, ставим employee_price = price ({svc.get('price', 0)})")

print(f"\n✅ Обновлено услуг с price2: {updated}")

# Финальная проверка
services_check = list(
    db.services.find({}, {"name": 1, "price": 1, "employee_price": 1, "price2": 1}).limit(3)
)
print(f"\n📋 Первые 3 услуги:")
for s in services_check:
    print(
        f"  {s['name']}: price={s.get('price')}, employee_price={s.get('employee_price')}, price2={s.get('price2', 'нет')}"
    )
