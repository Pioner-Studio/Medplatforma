# production_migration.py
# Скрипт для очистки demo данных и загрузки production данных

from pymongo import MongoClient
import bcrypt
from datetime import datetime

# Подключение к MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["clubstom"]


def clear_demo_data():
    """Очистка всех demo/test данных"""
    print("🗑️ Очистка demo данных...")

    # Очищаем все коллекции
    collections_to_clear = [
        "users",
        "doctors",
        "services",
        "rooms",
        "appointments",
        "patients",
        "finances",
    ]

    for collection_name in collections_to_clear:
        result = db[collection_name].delete_many({})
        print(f"   Удалено из {collection_name}: {result.deleted_count} записей")

    print("✅ Demo данные очищены")


def create_production_users():
    """Создание production пользователей"""
    print("👥 Создание пользователей...")

    # Реальные пользователи
    users = [
        {
            "name": "Гогуева Алина Темурлановна",
            "login": "Gogueva",
            "role": "admin",
            "phone": "79251837932",
            "password": bcrypt.hashpw("ClubStom2024!".encode("utf-8"), bcrypt.gensalt()).decode(
                "utf-8"
            ),
            "created_at": datetime.now(),
            "is_active": True,
        },
        {
            "name": "Наконечный Алексей Владимирович",
            "login": "Nakonechnyi",
            "role": "admin",
            "phone": "79852788171",
            "password": bcrypt.hashpw("ClubStom2024!".encode("utf-8"), bcrypt.gensalt()).decode(
                "utf-8"
            ),
            "created_at": datetime.now(),
            "is_active": True,
        },
        {
            "name": "Наконечная Елена Ивановна",
            "login": "Nakonechnaia",
            "role": "admin",
            "phone": "79164848085",
            "password": bcrypt.hashpw("ClubStom2024!".encode("utf-8"), bcrypt.gensalt()).decode(
                "utf-8"
            ),
            "created_at": datetime.now(),
            "is_active": True,
        },
        {
            "name": "Аксенова Ульяна Денисовна",
            "login": "Aksenova",
            "role": "registrar",
            "phone": "79175051978",
            "password": bcrypt.hashpw("ClubStom2024!".encode("utf-8"), bcrypt.gensalt()).decode(
                "utf-8"
            ),
            "created_at": datetime.now(),
            "is_active": True,
        },
    ]

    result = db.users.insert_many(users)
    print(f"✅ Создано пользователей: {len(result.inserted_ids)}")


def create_production_doctors():
    """Создание врачей"""
    print("👨‍⚕️ Создание врачей...")

    # Нужно исправить кодировку из файла
    doctors = [
        {
            "full_name": "Гогуева Алина Темурлановна",
            "specialty": "Главный врач, Терапевт",
            "phone": "79251837932",
            "is_active": True,
            "created_at": datetime.now(),
        },
        {
            "full_name": "Айвазян Альберт Гагикович",
            "specialty": "Хирург-имплантолог",
            "phone": "79150424721",
            "is_active": True,
            "created_at": datetime.now(),
        },
        {
            "full_name": "Курдов Кадыр Мурадович",
            "specialty": "Ортопед",
            "phone": "79015713021",
            "is_active": True,
            "created_at": datetime.now(),
        },
        {
            "full_name": "Калачев Алексей Николаевич",
            "specialty": "Ортодонт",
            "phone": "79191093938",
            "is_active": True,
            "created_at": datetime.now(),
        },
        {
            "full_name": "Миргатия Ольга Сергеевна",
            "specialty": "Детский стоматолог, Терапевт",
            "phone": "79164422955",
            "is_active": True,
            "created_at": datetime.now(),
        },
    ]

    result = db.doctors.insert_many(doctors)
    print(f"✅ Создано врачей: {len(result.inserted_ids)}")


def create_production_services():
    """Создание услуг с ценами"""
    print("💰 Создание прайс-листа...")

    services_data = [
        ("КТ", 60, 6000, 4000),
        ("Гигиена полости рта взр", 60, 13000, 10000),
        ("Гигиена полости рта дет", 60, 12000, 9500),
        ("Пародонтологическое лечение десен мембранами", 60, 13000, 9500),
        ("Отбеливание", 60, 35000, 31500),
        ("Каппы для домашнего отбеливания с гелем", 60, 27000, 20500),
        ("ICON", 60, 15000, 11500),
        ("Кариес поверхностный взр", 60, 13000, 10000),
        ("Кариес поверхностный дет", 60, 11000, 9000),
        ("Кариес глубокий взр", 60, 19000, 14500),
        ("Кариес глубокий детск", 60, 17000, 13500),
        ("Коронка детская", 60, 25000, 18000),
        ("Клиновидные дефекты", 60, 17000, 12000),
        ("Реставрация эстетическая (сколы)", 60, 19000, 14000),
        ("Восстановление стенки зуба со штифтом (Build up)", 60, 21000, 14500),
        ("Реставрация художественная= аналог виниров", 60, 30000, 23500),
        ("Кюретаж, 1 зуб", 60, 3000, 2200),
        ("Первичное лечение 1канального зуба в одно посещение (пульпит)", 60, 27000, 23500),
        ("Перелечивание 1 канала", 60, 27000, 22000),
        ("Удаление зуба простой", 60, 15000, 12500),
        ("Удаление зуба сложный", 60, 22000, 17000),
        ("Имплант shtraumann", 60, 100000, 81500),
        ("Имплант Nobel", 60, 100000, 81500),
        ("Имплант Dentium", 60, 80000, 66000),
        ("Синус-лифтинг", 60, 65000, 54000),
        ("Костная пластика", 60, 75000, 63000),
        ("Формирователь десны", 60, 13000, 12500),
        ("Пластика десны", 60, 13000, 11000),
        ("ALL oin 4 1 челюсть Nobel", 60, 400000, 31500),
        ("ALL on 6 1 челюсть Nobel", 60, 600000, 464000),
        ("ALL oin 4 1 челюсть Dentium", 60, 320000, 232000),
        ("ALL on 6 1 челюсть Dentium", 60, 480000, 341000),
        ("Ортопедическая конструкция ALL on 6 1 челюсть протез временный", 60, 250000, 201000),
        ("Ортопедическая конструкция ALL on 4 1 челюсть протез временный", 60, 200000, 163000),
        ("Ортопедическая конструкция ALL on 6 1 челюсть протез постоянный", 60, 300000, 237000),
        ("Ортопедическая конструкция ALL on 4 1 челюсть протез постоянный", 60, 250000, 199000),
        ("Постоянный протез сьемный пластик без имплантации 1 челюсть", 60, 100000, 79000),
        ("Брекеты", 60, 450000, 354000),
        ("Брекеты частичные локальные на 2 зуба", 60, 60000, 55000),
        ("Аппарат Марка Росса (несьемный аппарат для расширения верх челюсти)", 60, 100000, 85000),
        ("Элайнеры", 60, 500000, 440000),
        ("Временная коронка на зубе пластик", 60, 20000, 17500),
        ("Временная коронка на имплантате", 60, 30000, 26000),
        ("Постоянная коронка на зубе Emax керамика", 60, 55000, 41500),
        ("Постоянная коронка на зубе диоксид циркония", 60, 50000, 37500),
        ("Постоянная коронка на импланте Емах", 60, 55000, 45500),
        ("Постоянная коронка на импланте на основе диоксида циркония", 60, 50000, 41500),
        ("Виниры авторские\\высокая эстетика", 60, 85000, 67000),
        ("Винир простой", 60, 55000, 46500),
        ("Сплинт", 60, 120000, 100500),
        ("Миосплинт для профилактики стираемости", 60, 30000, 24000),
        (
            "Восковое моделирование для тотальных работ 1 челюсть 14 зубов, на 6 мес",
            60,
            120000,
            116000,
        ),
        (
            "Временная композитная накладка длительного ношения (в кресле) 14 шт, 1 челюсть, на 6 мес",
            60,
            140000,
            83500,
        ),
        ("этап 1. воск моделир+накладка, 2 нед работа на 6 мес", 60, 260000, 200000),
        ("Вкладка", 60, 40000, 33500),
    ]

    services = []
    for name, duration, price_client, price_staff in services_data:
        services.append(
            {
                "name": name,
                "duration_minutes": duration,
                "price_client": price_client,
                "price_staff": price_staff,
                "is_active": True,
                "created_at": datetime.now(),
            }
        )

    result = db.services.insert_many(services)
    print(f"✅ Создано услуг: {len(result.inserted_ids)}")


def create_production_rooms():
    """Создание кабинетов"""
    print("🏥 Создание кабинетов...")

    rooms_list = ["Терапия", "Эндодонтия", "Ортопедия", "Хирургия", "Детский", "Ортодонтия"]

    rooms = []
    for i, room_name in enumerate(rooms_list, 1):
        rooms.append(
            {"name": room_name, "number": i, "is_active": True, "created_at": datetime.now()}
        )

    result = db.rooms.insert_many(rooms)
    print(f"✅ Создано кабинетов: {len(result.inserted_ids)}")


def create_indexes():
    """Создание индексов для оптимизации"""
    print("🔍 Создание индексов...")

    # Индексы для быстрого поиска
    db.users.create_index("login", unique=True)
    db.doctors.create_index("phone")
    db.services.create_index("name")
    db.appointments.create_index([("date", 1), ("time", 1)])
    db.appointments.create_index("doctor_id")
    db.patients.create_index("phone")
    db.finances.create_index([("date", 1), ("service_id", 1)])

    print("✅ Индексы созданы")


def main():
    """Главная функция миграции"""
    print("🚀 Начинаем миграцию на Production данные...")
    print("=" * 50)

    try:
        # Шаг 1: Очистка demo данных
        clear_demo_data()
        print()

        # Шаг 2: Создание production данных
        create_production_users()
        create_production_doctors()
        create_production_services()
        create_production_rooms()
        print()

        # Шаг 3: Создание индексов
        create_indexes()
        print()

        print("=" * 50)
        print("🎉 Миграция завершена успешно!")
        print()
        print("📋 Созданные данные:")
        print("   👥 Пользователи: 4 (3 админа + 1 регистратор)")
        print("   👨‍⚕️ Врачи: 5")
        print("   💰 Услуги: 55")
        print("   🏥 Кабинеты: 6")
        print()
        print("🔐 Пароль по умолчанию для всех: ClubStom2024!")
        print("⚠️  Рекомендую сменить пароли после первого входа")

    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        raise


if __name__ == "__main__":
    main()
