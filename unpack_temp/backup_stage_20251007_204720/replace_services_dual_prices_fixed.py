#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ПОЛНАЯ ЗАМЕНА услуг с двумя прайс-листами
ИСПОЛЬЗУЕТ ТУ ЖЕ БД ЧТО И FLASK
"""

from pymongo import MongoClient
from datetime import datetime
import sys
import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    print("❌ ОШИБКА: MONGO_URI не найден в .env файле")
    sys.exit(1)

# Данные из services_price_dual.xlsx
SERVICES_DATA = [
    {
        "name": "КТ",
        "duration_min": 60,
        "price": 6000,
        "employee_price": 4000,
        "is_active": True,
        "code": "KT",
        "color": "#3498db",
    },
    {
        "name": "Гигиена полости рта взр",
        "duration_min": 60,
        "price": 13000,
        "employee_price": 10000,
        "is_active": True,
        "code": "GIG_V",
        "color": "#3498db",
    },
    {
        "name": "Гигиена полости рта дет",
        "duration_min": 60,
        "price": 12000,
        "employee_price": 9500,
        "is_active": True,
        "code": "GIG_D",
        "color": "#3498db",
    },
    {
        "name": "Пародонтологическое лечение десен мембранами",
        "duration_min": 60,
        "price": 13000,
        "employee_price": 9500,
        "is_active": True,
        "code": "PAR",
        "color": "#3498db",
    },
    {
        "name": "Отбеливание",
        "duration_min": 60,
        "price": 35000,
        "employee_price": 31500,
        "is_active": True,
        "code": "OTB",
        "color": "#3498db",
    },
    {
        "name": "Каппы для домашнего отбеливания с гелем",
        "duration_min": 60,
        "price": 27000,
        "employee_price": 20500,
        "is_active": True,
        "code": "KAP",
        "color": "#3498db",
    },
    {
        "name": "ICON",
        "duration_min": 60,
        "price": 15000,
        "employee_price": 11500,
        "is_active": True,
        "code": "I_7",
        "color": "#3498db",
    },
    {
        "name": "Кариес поверхностный взр",
        "duration_min": 60,
        "price": 13000,
        "employee_price": 10000,
        "is_active": True,
        "code": "KAR_PV",
        "color": "#3498db",
    },
    {
        "name": "Кариес поверхностный дет",
        "duration_min": 60,
        "price": 11000,
        "employee_price": 9000,
        "is_active": True,
        "code": "KAR_PD",
        "color": "#3498db",
    },
    {
        "name": "Кариес глубокий взр",
        "duration_min": 60,
        "price": 19000,
        "employee_price": 14500,
        "is_active": True,
        "code": "KAR_GV",
        "color": "#3498db",
    },
    {
        "name": "Кариес глубокий детск",
        "duration_min": 60,
        "price": 17000,
        "employee_price": 13500,
        "is_active": True,
        "code": "KAR_GD",
        "color": "#3498db",
    },
    {
        "name": "Коронка детская",
        "duration_min": 60,
        "price": 25000,
        "employee_price": 18000,
        "is_active": True,
        "code": "KOR_D",
        "color": "#3498db",
    },
    {
        "name": "Клиновидные дефекты",
        "duration_min": 60,
        "price": 17000,
        "employee_price": 12000,
        "is_active": True,
        "code": "KLIN",
        "color": "#3498db",
    },
    {
        "name": "Реставрация эстетическая (сколы)",
        "duration_min": 60,
        "price": 19000,
        "employee_price": 14000,
        "is_active": True,
        "code": "REST_E",
        "color": "#3498db",
    },
    {
        "name": "Восстановление стенки зуба со штифтом (Build up)",
        "duration_min": 60,
        "price": 21000,
        "employee_price": 14500,
        "is_active": True,
        "code": "BUILD",
        "color": "#3498db",
    },
    {
        "name": "Реставрация художественная= аналог виниров",
        "duration_min": 60,
        "price": 30000,
        "employee_price": 23500,
        "is_active": True,
        "code": "REST_H",
        "color": "#3498db",
    },
    {
        "name": "Кюретаж, 1 зуб",
        "duration_min": 60,
        "price": 3000,
        "employee_price": 2200,
        "is_active": True,
        "code": "KUR",
        "color": "#3498db",
    },
    {
        "name": "Первичное лечение 1канального зуба в одно посещение (пульпит)",
        "duration_min": 60,
        "price": 27000,
        "employee_price": 23500,
        "is_active": True,
        "code": "PULP_1",
        "color": "#3498db",
    },
    {
        "name": "Перелечивание 1 канала",
        "duration_min": 60,
        "price": 27000,
        "employee_price": 22000,
        "is_active": True,
        "code": "PEREL_1",
        "color": "#3498db",
    },
    {
        "name": "Удаление зуба простой",
        "duration_min": 60,
        "price": 15000,
        "employee_price": 12500,
        "is_active": True,
        "code": "UDAL_P",
        "color": "#3498db",
    },
    {
        "name": "Удаление зуба сложный",
        "duration_min": 60,
        "price": 22000,
        "employee_price": 17000,
        "is_active": True,
        "code": "UDAL_S",
        "color": "#3498db",
    },
    {
        "name": "Имплант shtraumann",
        "duration_min": 60,
        "price": 100000,
        "employee_price": 81500,
        "is_active": True,
        "code": "IMP_ST",
        "color": "#3498db",
    },
    {
        "name": "Имплант Nobel",
        "duration_min": 60,
        "price": 100000,
        "employee_price": 81500,
        "is_active": True,
        "code": "IMP_NOB",
        "color": "#3498db",
    },
    {
        "name": "Имплант Dentium",
        "duration_min": 60,
        "price": 80000,
        "employee_price": 66000,
        "is_active": True,
        "code": "IMP_DEN",
        "color": "#3498db",
    },
    {
        "name": "Синус-лифтинг",
        "duration_min": 60,
        "price": 65000,
        "employee_price": 54000,
        "is_active": True,
        "code": "SINUS",
        "color": "#3498db",
    },
    {
        "name": "Костная пластика",
        "duration_min": 60,
        "price": 75000,
        "employee_price": 63000,
        "is_active": True,
        "code": "KOST",
        "color": "#3498db",
    },
    {
        "name": "Формирователь десны",
        "duration_min": 60,
        "price": 13000,
        "employee_price": 12500,
        "is_active": True,
        "code": "FORM",
        "color": "#3498db",
    },
    {
        "name": "Пластика десны",
        "duration_min": 60,
        "price": 13000,
        "employee_price": 11000,
        "is_active": True,
        "code": "PLAST",
        "color": "#3498db",
    },
    {
        "name": "ALL oin 4 1 челюсть Nobel",
        "duration_min": 60,
        "price": 400000,
        "employee_price": 315000,
        "is_active": True,
        "code": "AO4_29",
        "color": "#3498db",
    },
    {
        "name": "ALL on 6 1 челюсть Nobel",
        "duration_min": 60,
        "price": 600000,
        "employee_price": 464000,
        "is_active": True,
        "code": "AO6_30",
        "color": "#3498db",
    },
    {
        "name": "ALL oin 4 1 челюсть Dentium",
        "duration_min": 60,
        "price": 320000,
        "employee_price": 232000,
        "is_active": True,
        "code": "AO4_31",
        "color": "#3498db",
    },
    {
        "name": "ALL on 6 1 челюсть Dentium",
        "duration_min": 60,
        "price": 480000,
        "employee_price": 341000,
        "is_active": True,
        "code": "AO6_32",
        "color": "#3498db",
    },
    {
        "name": "Ортопедическая конструкция ALL on 6 1 челюсть протез временный",
        "duration_min": 60,
        "price": 250000,
        "employee_price": 201000,
        "is_active": True,
        "code": "ORT6_V",
        "color": "#3498db",
    },
    {
        "name": "Ортопедическая конструкция ALL on 4 1 челюсть протез временный",
        "duration_min": 60,
        "price": 200000,
        "employee_price": 163000,
        "is_active": True,
        "code": "ORT4_V",
        "color": "#3498db",
    },
    {
        "name": "Ортопедическая конструкция ALL on 6 1 челюсть протез постоянный",
        "duration_min": 60,
        "price": 300000,
        "employee_price": 237000,
        "is_active": True,
        "code": "ORT6_P",
        "color": "#3498db",
    },
    {
        "name": "Ортопедическая конструкция ALL on 4 1 челюсть протез постоянный",
        "duration_min": 60,
        "price": 250000,
        "employee_price": 199000,
        "is_active": True,
        "code": "ORT4_P",
        "color": "#3498db",
    },
    {
        "name": "Постоянный протез сьемный пластик без имплантации 1 челюсть",
        "duration_min": 60,
        "price": 100000,
        "employee_price": 79000,
        "is_active": True,
        "code": "PROT_P",
        "color": "#3498db",
    },
    {
        "name": "Брекеты",
        "duration_min": 60,
        "price": 450000,
        "employee_price": 354000,
        "is_active": True,
        "code": "BREK",
        "color": "#3498db",
    },
    {
        "name": "Брекеты частичные локальные на 2 зуба",
        "duration_min": 60,
        "price": 60000,
        "employee_price": 55000,
        "is_active": True,
        "code": "BREK_L",
        "color": "#3498db",
    },
    {
        "name": "Аппарат Марка Росса (несьемный аппарат для расширения верх челюсти)",
        "duration_min": 60,
        "price": 100000,
        "employee_price": 85000,
        "is_active": True,
        "code": "APP_MR",
        "color": "#3498db",
    },
    {
        "name": "Элайнеры",
        "duration_min": 60,
        "price": 500000,
        "employee_price": 440000,
        "is_active": True,
        "code": "ELAIN",
        "color": "#3498db",
    },
    {
        "name": "Временная коронка на зубе пластик",
        "duration_min": 60,
        "price": 20000,
        "employee_price": 17500,
        "is_active": True,
        "code": "VREM_Z",
        "color": "#3498db",
    },
    {
        "name": "Временная коронка на имплантате",
        "duration_min": 60,
        "price": 30000,
        "employee_price": 26000,
        "is_active": True,
        "code": "VREM_I",
        "color": "#3498db",
    },
    {
        "name": "Постоянная коронка на зубе Emax керамика",
        "duration_min": 60,
        "price": 55000,
        "employee_price": 41500,
        "is_active": True,
        "code": "POST_ZE",
        "color": "#3498db",
    },
    {
        "name": "Постоянная коронка на зубе диоксид циркония",
        "duration_min": 60,
        "price": 50000,
        "employee_price": 37500,
        "is_active": True,
        "code": "POST_ZD",
        "color": "#3498db",
    },
    {
        "name": "Постоянная коронка на импланте Емах",
        "duration_min": 60,
        "price": 55000,
        "employee_price": 45500,
        "is_active": True,
        "code": "POST_IE",
        "color": "#3498db",
    },
    {
        "name": "Постоянная коронка на импланте на основе диоксида циркония",
        "duration_min": 60,
        "price": 50000,
        "employee_price": 41500,
        "is_active": True,
        "code": "POST_ID",
        "color": "#3498db",
    },
    {
        "name": "Виниры авторские\\высокая эстетика",
        "duration_min": 60,
        "price": 85000,
        "employee_price": 67000,
        "is_active": True,
        "code": "VIN_AVT",
        "color": "#3498db",
    },
    {
        "name": "Винир простой",
        "duration_min": 60,
        "price": 55000,
        "employee_price": 46500,
        "is_active": True,
        "code": "VIN_PR",
        "color": "#3498db",
    },
    {
        "name": "Сплинт",
        "duration_min": 60,
        "price": 120000,
        "employee_price": 100500,
        "is_active": True,
        "code": "SPLINT",
        "color": "#3498db",
    },
    {
        "name": "Миосплинт для профилактики стираемости",
        "duration_min": 60,
        "price": 30000,
        "employee_price": 24000,
        "is_active": True,
        "code": "MIO",
        "color": "#3498db",
    },
    {
        "name": "Восковое моделирование для тотальных работ 1 челюсть 14 зубов, на 6 мес",
        "duration_min": 60,
        "price": 120000,
        "employee_price": 116000,
        "is_active": True,
        "code": "VOSK",
        "color": "#3498db",
    },
    {
        "name": "Временная композитная накладка длительного ношения (в кресле) 14 шт, 1 челюсть, на 6 мес",
        "duration_min": 60,
        "price": 140000,
        "employee_price": 83500,
        "is_active": True,
        "code": "VREM_NAK",
        "color": "#3498db",
    },
    {
        "name": "этап 1. воск моделир+накладка, 2 нед работа на 6 мес",
        "duration_min": 60,
        "price": 260000,
        "employee_price": 200000,
        "is_active": True,
        "code": "ETAP1",
        "color": "#3498db",
    },
    {
        "name": "Вкладка",
        "duration_min": 60,
        "price": 40000,
        "employee_price": 33500,
        "is_active": True,
        "code": "VKLAD",
        "color": "#3498db",
    },
]


def replace_services():
    """Полная замена услуг в ОБЛАЧНОЙ БД"""
    try:
        print(f"Подключение к БД: {MONGO_URI[:30]}...")
        client = MongoClient(MONGO_URI)
        db = client["medplatforma"]  # Явно указываем имя БД

        # Шаг 1: Подсчёт старых услуг
        old_count = db.services.count_documents({})
        print(f"📊 Старых услуг в ОБЛАЧНОЙ БД: {old_count}")

        # Шаг 2: УДАЛЕНИЕ всех старых услуг
        print(f"\n🗑️  УДАЛЕНИЕ старых услуг...")
        result_delete = db.services.delete_many({})
        print(f"✅ Удалено: {result_delete.deleted_count}")

        # Шаг 3: Добавление created_at
        now = datetime.now()
        for service in SERVICES_DATA:
            service["created_at"] = now
            if "description" not in service:
                service["description"] = ""

        # Шаг 4: ВСТАВКА новых услуг
        print(f"\n📥 ВСТАВКА новых услуг с двумя прайсами...")
        result_insert = db.services.insert_many(SERVICES_DATA)
        print(f"✅ Вставлено: {len(result_insert.inserted_ids)}")

        # Шаг 5: Проверка
        new_count = db.services.count_documents({})
        with_employee_price = db.services.count_documents({"employee_price": {"$exists": True}})

        print(f"\n📊 ИТОГОВАЯ СТАТИСТИКА:")
        print(f"Всего услуг в ОБЛАЧНОЙ БД: {new_count}")
        print(f"С льготной ценой: {with_employee_price}")

        # Примеры
        print(f"\n📋 ПРИМЕРЫ (первые 3 услуги):")
        examples = list(db.services.find({}).limit(3))
        for svc in examples:
            print(f"  - {svc['name']}")
            print(f"    ID: {svc['_id']}")
            print(f"    Клиент: {svc['price']}₽ | Сотрудник: {svc['employee_price']}₽")

        print(f"\n✅ ЗАМЕНА В ОБЛАЧНОЙ БД ЗАВЕРШЕНА!")

    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    print("🚀 ПОЛНАЯ ЗАМЕНА УСЛУГ В ОБЛАЧНОЙ БД")
    print("=" * 60)
    replace_services()
    print("=" * 60)
