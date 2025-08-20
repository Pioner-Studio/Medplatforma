import random
from pymongo import MongoClient
from datetime import datetime, timedelta

client = MongoClient("mongodb+srv://medadmin:medpass123@medplatforma.cnv7fbo.mongodb.net/")
db = client['medplatforma']

# Очистим старых врачей
db.doctors.delete_many({})

names = [
    "Петров П.П.", "Иванова О.К.", "Кузнецов А.С.", "Сидорова Д.Л.",
    "Смирнов М.В.", "Соколова Е.А.", "Васильев И.И.", "Никитина Н.А.",
    "Макаров В.Р.", "Орлова Ю.Л."
]
specialties = [
    "Хирург", "Ортопед", "Терапевт", "Гигиенист", "Имплантолог", "Ортодонт"
]
positions = [
    "Главврач", "Стоматолог-терапевт", "Стоматолог-хирург", "Ортодонт", "Ортопед", "Гигиенист"
]
educations = [
    "МГМСУ им. Евдокимова, диплом с отличием (2010)",
    "РНИМУ им. Пирогова (2012)",
    "Санкт-Петербургский медуниверситет (2014)",
    "Казанский ГМУ (2011)",
    "Московский медуниверситет (2013)"
]
certificates = [
    "Повышение квалификации: Dentsply Sirona (2022)",
    "Имплантология Nobel Biocare (2023)",
    "Курс микроскопной терапии (2021)",
    "Авторские мастер-классы (2022)",
    "Участие в международных конференциях (2024)"
]
bios = [
    "Работает в клинике с {since}. Сотни успешных операций. Внедряет современные методики.",
    "Постоянно проходит обучение. Ведёт научную деятельность.",
    "Проводит сложнейшие операции и консультации. Более 1000 довольных пациентов.",
    "Лектор международных конгрессов, эксперт в эстетической стоматологии.",
    "Разработал уникальные протоколы реабилитации пациентов."
]
reviews_samples = [
    {"stars": 5, "text": "Врач от Бога, рекомендую всем!", "date": "05.2024"},
    {"stars": 4, "text": "Очень внимательный, всё подробно объяснил.", "date": "03.2024"},
    {"stars": 5, "text": "Сделала имплантацию — результат супер!", "date": "01.2024"},
    {"stars": 5, "text": "Спасибо за профессионализм и заботу!", "date": "11.2023"}
]
cases_samples = [
    {"before": "/static/cases/before1.jpg", "after": "/static/cases/after1.jpg"},
    {"before": "/static/cases/before2.jpg", "after": "/static/cases/after2.jpg"}
]
files_samples = [
    {"type": "image", "url": "/static/files/sertifikat_1.jpg", "name": "Сертификат 2022"},
    {"type": "pdf", "url": "/static/files/diplom.pdf", "name": "Диплом"},
]

def generate_events():
    today = datetime(2025, 7, 8)
    events = []
    for i in range(3):
        day = today + timedelta(days=i)
        events.append({
            "title": random.choice(["Пломба", "Консультация", "Лечение", "Имплантация"]),
            "start": (day + timedelta(hours=10 + i)).strftime('%Y-%m-%dT%H:00:00'),
            "end": (day + timedelta(hours=10 + i, minutes=30)).strftime('%Y-%m-%dT%H:30:00'),
            "color": random.choice(["#A2C6FA", "#B4F0C0", "#FDE8A5"])
        })
    return events

def random_phone():
    return "+79" + "".join([str(random.randint(0, 9)) for _ in range(9)])

def random_email(name):
    return name.replace(" ", ".").replace(".", "").lower() + "@clinic.ru"

def random_telegram(name):
    return name.split()[0].lower() + str(random.randint(100, 999))

def random_whatsapp(phone):
    return phone.replace("+", "")

# Генерация расписания в правильном формате для интерфейса (Пн=1 ... Сб=6, Вс=0)
def random_schedule():
    work_days = sorted(random.sample([1,2,3,4,5,6], k=random.randint(4,6)))  # 4–6 рабочих дней
    sch = {}
    for d in work_days:
        start = random.choice(["09:00", "10:00", "12:00"])
        end = random.choice(["16:00", "17:00", "18:00", "19:00"])
        if start < end:
            sch[str(d)] = {"start": start, "end": end}
        else:
            sch[str(d)] = {"start": "09:00", "end": "17:00"}
    return sch

doctors = []
for i, name in enumerate(names):
    phone = random_phone()
    since_year = 2012 + i % 7
    experience = 2025 - since_year
    doc = {
        "_id": f"doc{str(i+1).zfill(3)}",
        "full_name": name,
        "avatar_url": f"/static/avatars/doctor_{i+1}.png",
        "position": random.choice(positions),
        "specialization": random.choice(specialties),
        "phone": phone,
        "email": random_email(name),
        "telegram": random_telegram(name),
        "whatsapp": random_whatsapp(phone),
        "reg_address": "г. Москва, ул. Профсоюзная, д. " + str(5+i),
        "live_address": "г. Москва, ул. Профсоюзная, д. " + str(5+i),
        "notes": "Врач высшей категории.",
        "schedule": random_schedule(),
        "card_number": f"DOC{1000+i}",
        "created_at": "2025-07-01",
        "since": str(since_year),
        "experience": experience,
        "education": random.choice(educations),
        "certificates": random.choice(certificates),
        "bio": random.choice(bios).format(since=since_year),
        "files": random.sample(files_samples, k=random.randint(1,2)),
        "reviews": random.sample(reviews_samples, k=random.randint(2,4)),
        "cases": random.sample(cases_samples, k=random.randint(1,2)),
        "events": generate_events()
    }
    doctors.append(doc)

db.doctors.insert_many(doctors)
print("Демо-врачи с расписанием успешно сгенерированы!")
