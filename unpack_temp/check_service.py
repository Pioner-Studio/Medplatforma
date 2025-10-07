#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Проверка услуги в базе данных"""

from pymongo import MongoClient
from bson import ObjectId

client = MongoClient("mongodb://localhost:27017/")
db = client["medplatforma"]

service_id = "68ceefb600a8dfe76f6f32d7"

svc = db.services.find_one({"_id": ObjectId(service_id)})

if svc:
    print(f"✅ Услуга найдена:")
    print(f"  Название: {svc.get('name', 'НЕТ')}")
    print(f"  Цена (price): {svc.get('price', 'НЕТ')}")
    print(f"  Льготная (employee_price): {svc.get('employee_price', 'НЕТ')}")
    print(f"\n📋 ВСЕ ПОЛЯ:")
    for key, value in svc.items():
        if key != "_id":
            print(f"  {key}: {value}")
else:
    print(f"❌ Услуга с ID {service_id} не найдена")
