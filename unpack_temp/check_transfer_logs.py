#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Проверка логов переводов в audit_logs"""

from pymongo import MongoClient
from dotenv import load_dotenv
import os
import json

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)
db = client["medplatforma"]

# Ищем логи переводов
transfer_logs = list(
    db.audit_logs.find({"action": {"$in": ["transfer_money", "delete_transfer"]}})
    .sort("timestamp", -1)
    .limit(10)
)

print(f"Найдено логов переводов: {len(transfer_logs)}")

if transfer_logs:
    print("\nПоследние записи:")
    for log in transfer_logs:
        print(f"\nДействие: {log.get('action')}")
        print(f"Время: {log.get('timestamp_local')}")
        print(f"Пользователь: {log.get('user_name')}")
        print(f"Комментарий: {log.get('comment')}")
        print(f"Детали: {log.get('details')}")
else:
    print("\n❌ Логи переводов НЕ найдены в audit_logs")
    print("\nПроверяем что вообще есть в audit_logs:")
    all_actions = db.audit_logs.distinct("action")
    print(f"Все типы действий: {all_actions}")
