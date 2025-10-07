from pymongo import MongoClient
from datetime import datetime, timedelta
import random

client = MongoClient("mongodb+srv://medadmin:medpass123@medplatforma.cnv7fbo.mongodb.net/")
db = client['medplatforma']

# Получи список врачей (или подставь id вручную, если нету)
doctors = list(db.doctors.find())
if not doctors:
    # Временно фейки, если нет врачей (лучше использовать реальные _id)
    doctors = [{"_id": "1", "full_name": "Д-р Иванов"}, {"_id": "2", "full_name": "Д-р Петров"}]

def pick_doctor():
    doc = random.choice(doctors)
    return str(doc['_id'])

tasks = [
    {
        "title": "Согласовать план лечения",
        "description": "Обсудить варианты лечения с пациентом Козлова О.",
        "assigned_to": pick_doctor(),
        "due_date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%dT15:00"),
        "status": "active",
        "priority": "high",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
    },
    {
        "title": "Заполнить карту пациента",
        "description": "Добавить все недостающие документы по Сидорову А.",
        "assigned_to": pick_doctor(),
        "due_date": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%dT11:00"),
        "status": "active",
        "priority": "normal",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
    },
    {
        "title": "Провести рентгеноснимок",
        "description": "Рентген кабинет: панорамный снимок для Петрова И.",
        "assigned_to": pick_doctor(),
        "due_date": (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%dT10:00"),
        "status": "overdue",
        "priority": "normal",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
    },
    {
        "title": "Назначить повторный приём",
        "description": "Связаться с пациентом Фёдоровой Т. для записи.",
        "assigned_to": pick_doctor(),
        "due_date": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%dT13:00"),
        "status": "active",
        "priority": "high",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
    },
    {
        "title": "Проверить оплату пациента",
        "description": "Кассир: подтвердить поступление оплаты от Смирновой Л.",
        "assigned_to": pick_doctor(),
        "due_date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%dT18:00"),
        "status": "done",
        "priority": "normal",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
    },
    {
        "title": "Собрать документы для ЗТЛ",
        "description": "Передать все документы по Козловой О. в лабораторию.",
        "assigned_to": pick_doctor(),
        "due_date": (datetime.now() + timedelta(days=4)).strftime("%Y-%m-%dT16:00"),
        "status": "active",
        "priority": "low",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
    },
    {
        "title": "Созвон с партнёрской клиникой",
        "description": "Обсудить условия сотрудничества с Dr. Smile.",
        "assigned_to": pick_doctor(),
        "due_date": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%dT17:00"),
        "status": "active",
        "priority": "normal",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
    },
    {
        "title": "Провести внутренний аудит",
        "description": "Проверить заполнение карт за июнь.",
        "assigned_to": pick_doctor(),
        "due_date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%dT14:00"),
        "status": "done",
        "priority": "high",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
    },
    {
        "title": "Отправить отчёт в бухгалтерию",
        "description": "Экспортировать фин.отчёт за неделю.",
        "assigned_to": pick_doctor(),
        "due_date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%dT10:30"),
        "status": "active",
        "priority": "normal",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
    },
    {
        "title": "Провести инвентаризацию склада",
        "description": "Составить список расходных материалов.",
        "assigned_to": pick_doctor(),
        "due_date": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%dT12:00"),
        "status": "active",
        "priority": "low",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
]

db.tasks.delete_many({})  # Очистить коллекцию, если нужно
db.tasks.insert_many(tasks)

print("✅ Демо-задачи для платформы успешно добавлены!")
