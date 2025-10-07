#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Проверка конкретной услуги"""

from pymongo import MongoClient
from bson import ObjectId
import json

client = MongoClient("mongodb://localhost:27017/")
db = client["medplatforma"]

service_id = "68ceefb600a8dfe76f6f32da"

svc = db.services.find_one({"_id": ObjectId(service_id)})

if svc:
    print("УСЛУГА НАЙДЕНА:")
    print(json.dumps(svc, indent=2, default=str, ensure_ascii=False))
else:
    print("❌ Услуга НЕ найдена")

# Проверим первые 3 услуги для сравнения
print("\n" + "=" * 50)
print("ПЕРВЫЕ 3 УСЛУГИ ДЛЯ СРАВНЕНИЯ:")
for s in db.services.find({}).limit(3):
    print(f"\n{s['name']}:")
    print(f"  _id: {s['_id']}")
    print(f"  price: {s.get('price')}")
    print(f"  employee_price: {s.get('employee_price')}")
