# seed_logs.py
from pymongo import MongoClient
from datetime import datetime, timedelta
import random

client = MongoClient("mongodb+srv://medadmin:medpass123@medplatforma.cnv7fbo.mongodb.net/")
db = client['medplatforma']

users = [
    {"name": "Иванова Татьяна", "role": "Администратор", "avatar_url": "/static/avatars/u1.png"},
    {"name": "Петров Иван", "role": "Врач", "avatar_url": "/static/avatars/u2.png"},
    {"name": "Сидорова Мария", "role": "Ассистент", "avatar_url": "/static/avatars/u3.png"},
    {"name": "Лебедев Сергей", "role": "Регистратор", "avatar_url": "/static/avatars/u4.png"},
    {"name": "Васильева Мария", "role": "Врач", "avatar_url": "/static/avatars/u5.png"},
]

actions = [
    ("login", "Вход в систему"),
    ("logout", "Выход из системы"),
    ("add_patient", "Добавлен пациент"),
    ("edit_patient", "Изменены данные пациента"),
    ("delete_patient", "Удалён пациент"),
    ("add_event", "Добавлена запись"),
    ("export", "Экспорт данных"),
    ("view_report", "Просмотр отчёта"),
    ("error", "Ошибка авторизации"),
]

def rand_ip():
    return f"192.168.1.{random.randint(1,100)}"

demo = []
dt_now = datetime.now()
for i in range(50):
    user = random.choice(users)
    action, comment = random.choice(actions)
    log = {
        "datetime": (dt_now - timedelta(minutes=i*10)).strftime("%Y-%m-%d %H:%M"),
        "user": user["name"],
        "role": user["role"],
        "avatar_url": user["avatar_url"],
        "ip": rand_ip(),
        "action": action,
        "object": random.choice(["", "Пациент", "Врач", "Задача", "Финансы"]),
        "comment": comment
    }
    demo.append(log)
db.logs.delete_many({})
db.logs.insert_many(demo)
print("OK: demo logs inserted")
