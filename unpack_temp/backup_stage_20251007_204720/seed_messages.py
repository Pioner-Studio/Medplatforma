# seed_messages.py
from datetime import datetime, timedelta
from pymongo import MongoClient
client = MongoClient("mongodb+srv://medadmin:medpass123@medplatforma.cnv7fbo.mongodb.net/")
db = client['medplatforma']

now = datetime.now()
messages = [
    {
        "chat_id": "admin-doctor",
        "participants": ["Иванова Анна (админ)", "Д-р Сидоров Алексей"],
        "messages": [
            {
                "sender": "Иванова Анна (админ)",
                "avatar": "/static/avatars/staff_1.png",
                "role": "Админ",
                "text": "Добрый день! В 13:00 ждём отчёт по пациенту Синицыну.",
                "timestamp": (now - timedelta(hours=4)).strftime("%Y-%m-%d %H:%M"),
                "read": True
            },
            {
                "sender": "Д-р Сидоров Алексей",
                "avatar": "/static/avatars/doctor_1.png",
                "role": "Врач",
                "text": "Добрый день! Всё будет готово, отправлю за 30 минут.",
                "timestamp": (now - timedelta(hours=3, minutes=40)).strftime("%Y-%m-%d %H:%M"),
                "read": True
            }
        ]
    },
    {
        "chat_id": "doctors-group",
        "participants": ["Д-р Сидоров Алексей", "Д-р Михайлова Елена", "Д-р Иванов Владимир"],
        "group": True,
        "title": "Врачи",
        "avatar": "/static/avatars/doctor_2.png",
        "messages": [
            {
                "sender": "Д-р Михайлова Елена",
                "avatar": "/static/avatars/doctor_2.png",
                "role": "Врач",
                "text": "Коллеги, нужна рентгенография пациенту Козлова до 15:00!",
                "timestamp": (now - timedelta(hours=2, minutes=12)).strftime("%Y-%m-%d %H:%M"),
                "read": True
            },
            {
                "sender": "Д-р Иванов Владимир",
                "avatar": "/static/avatars/doctor_3.png",
                "role": "Врач",
                "text": "Ок, договорился с рентген-кабинетом.",
                "timestamp": (now - timedelta(hours=2, minutes=8)).strftime("%Y-%m-%d %H:%M"),
                "read": True
            }
        ]
    },
    {
        "chat_id": "admin-all",
        "participants": ["Иванова Анна (админ)", "Все врачи", "ЗТЛ", "Рентген"],
        "group": True,
        "title": "Объявления",
        "avatar": "/static/avatars/staff_2.png",
        "messages": [
            {
                "sender": "Иванова Анна (админ)",
                "avatar": "/static/avatars/staff_1.png",
                "role": "Админ",
                "text": "Коллеги, на следующей неделе обновление системы — всем быть на созвоне во вторник в 10:00.",
                "timestamp": (now - timedelta(hours=1, minutes=45)).strftime("%Y-%m-%d %H:%M"),
                "read": False
            }
        ]
    }
]
db.messages.delete_many({})
db.messages.insert_many(messages)
print("Demo messages loaded!")
