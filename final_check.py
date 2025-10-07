#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Финальная проверка услуги"""

from pymongo import MongoClient
from bson import ObjectId

client = MongoClient("mongodb://localhost:27017/")
db = client["medplatforma"]

service_id = "68ceefb600a8dfe76f6f32d9"

svc = db.services.find_one({"_id": ObjectId(service_id)})

if svc:
    print(f"Услуга: {svc['name']}")
    print(f"price: {svc.get('price')}")
    print(f"employee_price: {svc.get('employee_price')}")
    print(f"price2: {svc.get('price2', 'НЕТ')}")
else:
    print("Услуга не найдена")
