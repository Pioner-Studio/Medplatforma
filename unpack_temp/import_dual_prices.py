#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Импорт двух прайс-листов для медплатформы
Обновляет services с price (клиенты) и employee_price (сотрудники)
"""

from pymongo import MongoClient
from bson import ObjectId
import sys

# Данные из services_price_dual.xlsx
SERVICES_DATA = [
    {"name": "КТ", "duration_min": 60, "price": 6000, "employee_price": 4000},
    {
        "name": "Гигиена полости рта взр",
        "duration_min": 60,
        "price": 13000,
        "employee_price": 10000,
    },
    {"name": "Гигиена полости рта дет", "duration_min": 60, "price": 12000, "employee_price": 9500},
    {
        "name": "Пародонтологическое лечение десен мембранами",
        "duration_min": 60,
        "price": 13000,
        "employee_price": 9500,
    },
    {"name": "Отбеливание", "duration_min": 60, "price": 35000, "employee_price": 31500},
    {
        "name": "Каппы для домашнего отбеливания с гелем",
        "duration_min": 60,
        "price": 27000,
        "employee_price": 20500,
    },
    {"name": "ICON", "duration_min": 60, "price": 15000, "employee_price": 11500},
    {
        "name": "Кариес поверхностный взр",
        "duration_min": 60,
        "price": 13000,
        "employee_price": 10000,
    },
    {
        "name": "Кариес поверхностный дет",
        "duration_min": 60,
        "price": 11000,
        "employee_price": 9000,
    },
    {"name": "Кариес глубокий взр", "duration_min": 60, "price": 19000, "employee_price": 14500},
    {"name": "Кариес глубокий детск", "duration_min": 60, "price": 17000, "employee_price": 13500},
    {"name": "Коронка детская", "duration_min": 60, "price": 25000, "employee_price": 18000},
    {"name": "Клиновидные дефекты", "duration_min": 60, "price": 17000, "employee_price": 12000},
    {
        "name": "Реставрация эстетическая (сколы)",
        "duration_min": 60,
        "price": 19000,
        "employee_price": 14000,
    },
    {
        "name": "Восстановление стенки зуба со штифтом (Build up)",
        "duration_min": 60,
        "price": 21000,
        "employee_price": 14500,
    },
    {
        "name": "Реставрация художественная= аналог виниров",
        "duration_min": 60,
        "price": 30000,
        "employee_price": 23500,
    },
    {"name": "Кюретаж, 1 зуб", "duration_min": 60, "price": 3000, "employee_price": 2200},
    {
        "name": "Первичное лечение 1канального зуба в одно посещение (пульпит)",
        "duration_min": 60,
        "price": 27000,
        "employee_price": 23500,
    },
    {"name": "Перелечивание 1 канала", "duration_min": 60, "price": 27000, "employee_price": 22000},
    {"name": "Удаление зуба простой", "duration_min": 60, "price": 15000, "employee_price": 12500},
    {"name": "Удаление зуба сложный", "duration_min": 60, "price": 22000, "employee_price": 17000},
    {"name": "Имплант shtraumann", "duration_min": 60, "price": 100000, "employee_price": 81500},
    {"name": "Имплант Nobel", "duration_min": 60, "price": 100000, "employee_price": 81500},
    {"name": "Имплант Dentium", "duration_min": 60, "price": 80000, "employee_price": 66000},
    {"name": "Синус-лифтинг", "duration_min": 60, "price": 65000, "employee_price": 54000},
    {"name": "Костная пластика", "duration_min": 60, "price": 75000, "employee_price": 63000},
    {"name": "Формирователь десны", "duration_min": 60, "price": 13000, "employee_price": 12500},
    {"name": "Пластика десны", "duration_min": 60, "price": 13000, "employee_price": 11000},
    {
        "name": "ALL oin 4 1 челюсть Nobel",
        "duration_min": 60,
        "price": 400000,
        "employee_price": 31500,
    },
    {
        "name": "ALL on 6 1 челюсть Nobel",
        "duration_min": 60,
        "price": 600000,
        "employee_price": 464000,
    },
    {
        "name": "ALL oin 4 1 челюсть Dentium",
        "duration_min": 60,
        "price": 320000,
        "employee_price": 232000,
    },
    {
        "name": "ALL on 6 1 челюсть Dentium",
        "duration_min": 60,
        "price": 480000,
        "employee_price": 341000,
    },
    {
        "name": "Ортопедическая конструкция ALL on 6 1 челюсть протез временный",
        "duration_min": 60,
        "price": 250000,
        "employee_price": 201000,
    },
    {
        "name": "Ортопедическая конструкция ALL on 4 1 челюсть протез временный",
        "duration_min": 60,
        "price": 200000,
        "employee_price": 163000,
    },
    {
        "name": "Ортопедическая конструкция ALL on 6 1 челюсть протез постоянный",
        "duration_min": 60,
        "price": 300000,
        "employee_price": 237000,
    },
    {
        "name": "Ортопедическая конструкция ALL on 4 1 челюсть протез постоянный",
        "duration_min": 60,
        "price": 250000,
        "employee_price": 199000,
    },
    {
        "name": "Постоянный протез сьемный пластик без имплантации 1 челюсть",
        "duration_min": 60,
        "price": 100000,
        "employee_price": 79000,
    },
    {"name": "Брекеты", "duration_min": 60, "price": 450000, "employee_price": 354000},
    {
        "name": "Брекеты частичные локальные на 2 зуба",
        "duration_min": 60,
        "price": 60000,
        "employee_price": 55000,
    },
    {
        "name": "Аппарат Марка Росса (несьемный аппарат для расширения верх челюсти)",
        "duration_min": 60,
        "price": 100000,
        "employee_price": 85000,
    },
    {"name": "Элайнеры", "duration_min": 60, "price": 500000, "employee_price": 440000},
    {
        "name": "Временная коронка на зубе пластик",
        "duration_min": 60,
        "price": 20000,
        "employee_price": 17500,
    },
    {
        "name": "Временная коронка на имплантате",
        "duration_min": 60,
        "price": 30000,
        "employee_price": 26000,
    },
    {
        "name": "Постоянная коронка на зубе Emax керамика",
        "duration_min": 60,
        "price": 55000,
        "employee_price": 41500,
    },
    {
        "name": "Постоянная коронка на зубе диоксид циркония",
        "duration_min": 60,
        "price": 50000,
        "employee_price": 37500,
    },
    {
        "name": "Постоянная коронка на импланте Емах",
        "duration_min": 60,
        "price": 55000,
        "employee_price": 45500,
    },
    {
        "name": "Постоянная коронка на импланте на основе диоксида циркония",
        "duration_min": 60,
        "price": 50000,
        "employee_price": 41500,
    },
    {
        "name": "Виниры авторские\\высокая эстетика",
        "duration_min": 60,
        "price": 85000,
        "employee_price": 67000,
    },
    {"name": "Винир простой", "duration_min": 60, "price": 55000, "employee_price": 46500},
    {"name": "Сплинт", "duration_min": 60, "price": 120000, "employee_price": 100500},
    {
        "name": "Миосплинт для профилактики стираемости",
        "duration_min": 60,
        "price": 30000,
        "employee_price": 24000,
    },
    {
        "name": "Восковое моделирование для тотальных работ 1 челюсть 14 зубов, на 6 мес",
        "duration_min": 60,
        "price": 120000,
        "employee_price": 116000,
    },
    {
        "name": "Временная композитная накладка длительного ношения (в кресле) 14 шт, 1 челюсть, на 6 мес",
        "duration_min": 60,
        "price": 140000,
        "employee_price": 83500,
    },
    {
        "name": "этап 1. воск моделир+накладка, 2 нед работа на 6 мес",
        "duration_min": 60,
        "price": 260000,
        "employee_price": 200000,
    },
    {"name": "Вкладка", "duration_min": 60, "price": 40000, "employee_price": 33500},
]


def update_services():
    """Обновление услуг с двумя прайсами"""
    try:
        client = MongoClient("mongodb://localhost:27017/")
        db = client["medplatforma"]

        updated_count = 0
        not_found = []

        for service_data in SERVICES_DATA:
            name = service_data["name"]

            # Ищем услугу по названию
            result = db.services.update_one(
                {"name": name},
                {
                    "$set": {
                        "price": service_data["price"],
                        "employee_price": service_data["employee_price"],
                        "duration_min": service_data["duration_min"],
                    }
                },
            )

            if result.matched_count > 0:
                updated_count += 1
                print(f"✅ {name}: {service_data['price']}₽ / {service_data['employee_price']}₽")
            else:
                not_found.append(name)
                print(f"❌ НЕ НАЙДЕНО: {name}")

        print(f"\n📊 ИТОГИ:")
        print(f"Обновлено услуг: {updated_count}")
        print(f"Не найдено: {len(not_found)}")

        if not_found:
            print(f"\n⚠️ Эти услуги нужно добавить вручную:")
            for name in not_found:
                print(f"  - {name}")

        # Проверка результата
        total_with_emp = db.services.count_documents({"employee_price": {"$exists": True}})
        print(f"\n✅ Всего услуг с льготной ценой: {total_with_emp}")

    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("🚀 ИМПОРТ ДВУХ ПРАЙС-ЛИСТОВ")
    print("=" * 50)
    update_services()
    print("=" * 50)
    print("✅ ИМПОРТ ЗАВЕРШЁН!")
