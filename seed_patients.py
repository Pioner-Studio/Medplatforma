import random
from pymongo import MongoClient

client = MongoClient("mongodb+srv://medadmin:medpass123@medplatforma.cnv7fbo.mongodb.net/")
db = client['medplatforma']

# Очистим старых пациентов
db.patients.delete_many({})

names = [
    "Климов Егор", "Сидорова Дарья", "Павлова Юлия", "Иванов Андрей",
    "Петрова Анна", "Максимов Павел", "Григорьев Тимур", "Васильева Вера",
    "Орлов Дмитрий", "Смирнова Ксения"
]

def random_phone():
    return "+79" + "".join([str(random.randint(0, 9)) for _ in range(9)])

def random_email(name):
    return name.replace(" ", ".").lower() + "@mail.ru"

def random_telegram(name):
    return name.split()[0].lower() + str(random.randint(10, 99))

def random_whatsapp(phone):
    return phone.replace("+", "")

patients = []
for i, name in enumerate(names):
    phone = random_phone()
    pat = {
        "_id": f"pat{str(i+1).zfill(3)}",
        "full_name": name,
        "dob": f"{random.randint(1970, 2004)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
        "phone": phone,
        "email": random_email(name),
        "telegram": random_telegram(name),
        "whatsapp": random_whatsapp(phone),
        "passport": f"{random.randint(1000,9999)} {random.randint(100000,999999)}",
        "referral": random.choice(names),
        "reg_address": "г. Москва, ул. Примерная, д. " + str(10+i),
        "live_address": "г. Москва, ул. Примерная, д. " + str(10+i),
        "debt": random.choice([0, -1000, 500, 0]),
        "deposit": random.choice([0, 1000, 2000]),
        "partner_points": random.choice([0, 5, 10, 20]),
        "business": random.choice(["-", "IT", "Торговля", "Фриланс", "Маркетинг"]),
        "hobby": random.choice(["-", "Чтение", "Спорт", "Путешествия", "Кино"]),
        "notes": random.choice(["", "Аллергия на антибиотики", "Требуется консультация"]),
        "created_at": "2025-07-01",
        "avatar_url": f"/static/avatars/patient_{i+1}.png"
    }
    patients.append(pat)

db.patients.insert_many(patients)
print("Демо-пациенты успешно сгенерированы!")
