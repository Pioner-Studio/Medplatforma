import random
from pymongo import MongoClient

client = MongoClient("mongodb+srv://medadmin:medpass123@medplatforma.cnv7fbo.mongodb.net/")
db = client['medplatforma']

# Очистим старых сотрудников
db.staff.delete_many({})

names = [
    "Куликова Алина", "Гусев Денис", "Зайцева Олеся", "Макаров Семён",
    "Тихонов Михаил", "Корнилова Татьяна", "Орлов Игорь",
    "Мельникова Елена", "Демидова Оксана", "Ефимов Виктор"
]
roles = [
    "Администратор", "Кассир", "Менеджер", "Куратор пациентов",
    "Клинический ассистент", "Оператор call-центра", "Старшая медсестра",
    "Финансовый контролёр", "Секретарь", "Аналитик"
]

# Для картинок аватаров можешь использовать стандартные svg/png из /static/avatars/staff_1.png ... staff_10.png
def random_phone():
    return "+79" + "".join([str(random.randint(0, 9)) for _ in range(9)])

def random_email(name):
    return name.replace(" ", ".").lower() + "@clubstom.pro"

def random_telegram(name):
    base = name.split()[0].lower()
    return f"{base}_{random.randint(10, 99)}"

def random_whatsapp(phone):
    return phone.replace("+", "")

staff_list = []
for i, name in enumerate(names):
    phone = random_phone()
    staff = {
        "_id": f"staff{str(i+1).zfill(3)}",
        "full_name": name,
        "role": roles[i],
        "avatar_url": f"/static/avatars/staff_{i+1}.png",
        "phone": phone,
        "email": random_email(name),
        "telegram": random_telegram(name),
        "whatsapp": random_whatsapp(phone),
        "position": roles[i],
        "date_joined": f"2022-0{random.randint(1,9)}-{random.randint(10,28)}",
        "card_number": f"STF{3000+i}",
        "notes": "Исполнительный, ответственный сотрудник. Всегда готов помочь пациентам и коллегам.",
        "active": True
    }
    staff_list.append(staff)

db.staff.insert_many(staff_list)
print("10 исполнителей (staff) сгенерированы и загружены в базу!")
