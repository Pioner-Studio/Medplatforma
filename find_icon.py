#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Поиск услуги ICON с актуальным ID"""

from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["medplatforma"]

svc = db.services.find_one({"name": "ICON"})

if svc:
    print(f"Услуга: {svc['name']}")
    print(f"_id: {svc['_id']}")
    print(f"price: {svc.get('price')}")
    print(f"employee_price: {svc.get('employee_price')}")
    print(f"\nОткройте в браузере:")
    print(f"http://localhost:5000/edit_service/{svc['_id']}")
else:
    print("Услуга ICON не найдена")
