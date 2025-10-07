from pymongo import MongoClient
from datetime import datetime

client = MongoClient("mongodb+srv://medadmin:medpass123@medplatforma.cnv7fbo.mongodb.net/")
db = client['medplatforma']

def upsert(coll, query, doc):
    coll.update_one(query, {"$setOnInsert": doc}, upsert=True)

# 1) Статусы визита
visit_statuses = [
    {"key":"scheduled",  "title":"Запланировано", "color":"#3498db"},
    {"key":"checked_in", "title":"Пришёл",        "color":"#10b981"},
    {"key":"done",       "title":"Выполнено",     "color":"#22c55e"},
    {"key":"canceled",   "title":"Отменено",      "color":"#ef4444"},
]
for s in visit_statuses:
    upsert(db.visit_statuses, {"key": s["key"]}, s)

# 2) Услуги (с длительностью и цветом)
services = [
    {"code":"CONS", "name":"Консультация", "duration_min":20, "price":0,    "color":"#60a5fa", "is_active":True},
    {"code":"HYGI", "name":"Гигиена",      "duration_min":40, "price":3500, "color":"#34d399", "is_active":True},
    {"code":"CANL", "name":"Лечение каналов","duration_min":60, "price":9000,"color":"#f87171","is_active":True},
    {"code":"CROW", "name":"Коронка",      "duration_min":50, "price":15000,"color":"#fbbf24","is_active":True},
    {"code":"XRY",  "name":"Рентген",      "duration_min":15, "price":800,  "color":"#a78bfa","is_active":True},
]
for s in services:
    s["created_at"] = s["updated_at"] = datetime.utcnow()
    upsert(db.services, {"code": s["code"]}, s)

print("OK: core seed done")
