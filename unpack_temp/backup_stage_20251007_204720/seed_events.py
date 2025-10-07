import random
from datetime import datetime, timedelta
from pymongo import MongoClient

client = MongoClient("mongodb+srv://medadmin:medpass123@medplatforma.cnv7fbo.mongodb.net/")
db = client['medplatforma']

# Очистим старые события
db.events.delete_many({})

# Примерные ID врачей и пациентов (возьми из своей базы/seed-файлов!)
doctor_ids = [f"doc00{i}" for i in range(1, 9)]
patient_ids = [f"pat00{i}" for i in range(1, 11)]

services = ['Лечение', 'Гигиена', 'Пломба', 'Имплантация']
statuses = [
    ('Первичный', '#A2C6FA'),
    ('Отказ', '#FBC7C0'),
    ('Повторный', '#FDE8A5'),
    ('Оплачен', '#B4F0C0')
]

def random_phone():
    return '+79' + ''.join([str(random.randint(0,9)) for _ in range(9)])

def random_telegram():
    names = ['dental_egor', 'smile_olga', 'alex_stom', 'doc_katya', 'dr_maksim', 'teeth_nika']
    return random.choice(names) + str(random.randint(10,99))

def random_whatsapp(phone):
    return phone.replace('+', '')

def random_email(name):
    return name.replace(' ', '.').lower() + "@gmail.com"

events = []
now = datetime.now()
for i in range(20):
    doctor_id = random.choice(doctor_ids)
    patient_id = random.choice(patient_ids)
    service = random.choice(services)
    status, color = random.choice(statuses)
    # Просто раскидываем события на 7 дней, с шагом 1-2 часа
    date = now + timedelta(days=random.randint(0,6), hours=random.randint(8,18))
    date_str = date.strftime("%Y-%m-%dT%H:%M")
    end_str = (date + timedelta(minutes=50)).strftime("%Y-%m-%dT%H:%M")

    patient_name = f"Пациент {patient_id[-2:]}"
    phone = random_phone()
    events.append({
        "_id": f"ev{i+1:03d}",
        "doctor_id": doctor_id,
        "patient_id": patient_id,
        "title": f"{service} - {patient_name}",
        "start": date_str,
        "end": end_str,
        "service": service,
        "sum": random.choice([2000, 3000, 4000, 5000, 7000]),
        "status": status,
        "status_color": color,
        "comment": random.choice(["Первичный прием", "Контрольный осмотр", "Оплачен. Вопросов нет", "Требуется консультация"]),
        "phone": phone,
        "email": random_email(patient_name),
        "telegram": random_telegram(),
        "whatsapp": random_whatsapp(phone),
        "card_number": f"PAT{random.randint(1000,9999)}",
        "birth": f"{random.randint(1970,2004)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
        "address": "г. Москва, ул. Демоданных, д. " + str(random.randint(1, 40)),
        "tags": "VIP" if random.random() < 0.15 else "",
    })

db.events.insert_many(events)
print("Демо-события успешно добавлены!")
