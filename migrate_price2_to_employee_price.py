#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Миграция: переименование price2 → employee_price
"""

from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["medplatforma"]

# Находим все услуги с price2
services_with_price2 = list(db.services.find({"price2": {"$exists": True}}))

print(f"Найдено услуг с price2: {len(services_with_price2)}")

updated = 0
for svc in services_with_price2:
    # Копируем price2 → employee_price
    db.services.update_one(
        {"_id": svc["_id"]}, {"$set": {"employee_price": svc["price2"]}, "$unset": {"price2": ""}}
    )
    updated += 1
    print(f"✅ {svc['name']}: price2={svc['price2']} → employee_price")

print(f"\n✅ Обновлено: {updated} услуг")

# Проверка
total = db.services.count_documents({})
with_employee = db.services.count_documents({"employee_price": {"$exists": True}})
print(f"Всего услуг: {total}")
print(f"С employee_price: {with_employee}")
