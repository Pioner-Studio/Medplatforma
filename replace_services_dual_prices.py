#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ПОЛНАЯ ЗАМЕНА услуг с двумя прайс-листами
ВНИМАНИЕ: Удаляет все существующие услуги и создаёт новые!
"""

from pymongo import MongoClient
from datetime import datetime
import sys

# Данные из services_price_dual.xlsx
SERVICES_DATA = [
    {"name": "КТ", "duration_min": 60, "price": 6000, "employee_price": 4000, "is_active": True},
    {
        "name": "Гигиена полости рта взр",
        "duration_min": 60,
        "price": 13000,
        "employee_price": 10000,
        "is_active": True,
    },
    {
        "name": "Гигиена полости рта дет",
        "duration_min": 60,
        "price": 12000,
        "employee_price": 9500,
        "is_active": True,
    },
    {
        "name": "Пародонтологическое лечение десен мембранами",
        "duration_min": 60,
        "price": 13000,
        "employee_price": 9500,
        "is_active": True,
    },
    {
        "name": "Отбеливание",
        "duration_min": 60,
        "price": 35000,
        "employee_price": 31500,
        "is_active": True,
    },
    {
        "name": "Каппы для домашнего отбеливания с гелем",
        "duration_min": 60,
        "price": 27000,
        "employee_price": 20500,
        "is_active": True,
    },
    {
        "name": "ICON",
        "duration_min": 60,
        "price": 15000,
        "employee_price": 11500,
        "is_active": True,
    },
    {
        "name": "Кариес поверхностный взр",
        "duration_min": 60,
        "price": 13000,
        "employee_price": 10000,
        "is_active": True,
    },
    {
        "name": "Кариес поверхностный дет",
        "duration_min": 60,
        "price": 11000,
        "employee_price": 9000,
        "is_active": True,
    },
    {
        "name": "Кариес глубокий взр",
        "duration_min": 60,
        "price": 19000,
        "employee_price": 14500,
        "is_active": True,
    },
    {
        "name": "Кариес глубокий детск",
        "duration_min": 60,
        "price": 17000,
        "employee_price": 13500,
        "is_active": True,
    },
    {
        "name": "Коронка детская",
        "duration_min": 60,
        "price": 25000,
        "employee_price": 18000,
        "is_active": True,
    },
    {
        "name": "Клиновидные дефекты",
        "duration_min": 60,
        "price": 17000,
        "employee_price": 12000,
        "is_active": True,
    },
    {
        "name": "Реставрация эстетическая (сколы)",
        "duration_min": 60,
        "price": 19000,
        "employee_price": 14000,
        "is_active": True,
    },
    {
        "name": "Восстановление стенки зуба со штифтом (Build up)",
        "duration_min": 60,
        "price": 21000,
        "employee_price": 14500,
        "is_active": True,
    },
    {
        "name": "Реставрация художественная= аналог виниров",
        "duration_min": 60,
        "price": 30000,
        "employee_price": 23500,
        "is_active": True,
    },
    {
        "name": "Кюретаж, 1 зуб",
        "duration_min": 60,
        "price": 3000,
        "employee_price": 2200,
        "is_active": True,
    },
    {
        "name": "Первичное лечение 1канального зуба в одно посещение (пульпит)",
        "duration_min": 60,
        "price": 27000,
        "employee_price": 23500,
        "is_active": True,
    },
    {
        "name": "Перелечивание 1 канала",
        "duration_min": 60,
        "price": 27000,
        "employee_price": 22000,
        "is_active": True,
    },
    {
        "name": "Удаление зуба простой",
        "duration_min": 60,
        "price": 15000,
        "employee_price": 12500,
        "is_active": True,
    },
    {
        "name": "Удаление зуба сложный",
        "duration_min": 60,
        "price": 22000,
        "employee_price": 17000,
        "is_active": True,
    },
    {
        "name": "Имплант shtraumann",
        "duration_min": 60,
        "price": 100000,
        "employee_price": 81500,
        "is_active": True,
    },
    {
        "name": "Имплант Nobel",
        "duration_min": 60,
        "price": 100000,
        "employee_price": 81500,
        "is_active": True,
    },
    {
        "name": "Имплант Dentium",
        "duration_min": 60,
        "price": 80000,
        "employee_price": 66000,
        "is_active": True,
    },
    {
        "name": "Синус-лифтинг",
        "duration_min": 60,
        "price": 65000,
        "employee_price": 54000,
        "is_active": True,
    },
    {
        "name": "Костная пластика",
        "duration_min": 60,
        "price": 75000,
        "employee_price": 63000,
        "is_active": True,
    },
    {
        "name": "Формирователь десны",
        "duration_min": 60,
        "price": 13000,
        "employee_price": 12500,
        "is_active": True,
    },
    {
        "name": "Пластика десны",
        "duration_min": 60,
        "price": 13000,
        "employee_price": 11000,
        "is_active": True,
    },
    {
        "name": "ALL oin 4 1 челюсть Nobel",
        "duration_min": 60,
        "price": 400000,
        "employee_price": 31500,
        "is_active": True,
    },
    {
        "name": "ALL on 6 1 челюсть Nobel",
        "duration_min": 60,
        "price": 600000,
        "employee_price": 464000,
        "is_active": True,
    },
    {
        "name": "ALL oin 4 1 челюсть Dentium",
        "duration_min": 60,
        "price": 320000,
        "employee_price": 232000,
        "is_active": True,
    },
    {
        "name": "ALL on 6 1 челюсть Dentium",
        "duration_min": 60,
        "price": 480000,
        "employee_price": 341000,
        "is_active": True,
    },
    {
        "name": "Ортопедическая конструкция ALL on 6 1 челюсть протез временный",
        "duration_min": 60,
        "price": 250000,
        "employee_price": 201000,
        "is_active": True,
    },
    {
        "name": "Ортопедическая конструкция ALL on 4 1 челюсть протез временный",
        "duration_min": 60,
        "price": 200000,
        "employee_price": 163000,
        "is_active": True,
    },
    {
        "name": "Ортопедическая конструкция ALL on 6 1 челюсть протез постоянный",
        "duration_min": 60,
        "price": 300000,
        "employee_price": 237000,
        "is_active": True,
    },
    {
        "name": "Ортопедическая конструкция ALL on 4 1 челюсть протез постоянный",
        "duration_min": 60,
        "price": 250000,
        "employee_price": 199000,
        "is_active": True,
    },
    {
        "name": "Постоянный протез сьемный пластик без имплантации 1 челюсть",
        "duration_min": 60,
        "price": 100000,
        "employee_price": 79000,
        "is_active": True,
    },
    {
        "name": "Брекеты",
        "duration_min": 60,
        "price": 450000,
        "employee_price": 354000,
        "is_active": True,
    },
    {
        "name": "Брекеты частичные локальные на 2 зуба",
        "duration_min": 60,
        "price": 60000,
        "employee_price": 55000,
        "is_active": True,
    },
    {
        "name": "Аппарат Марка Росса (несьемный аппарат для расширения верх челюсти)",
        "duration_min": 60,
        "price": 100000,
        "employee_price": 85000,
        "is_active": True,
    },
    {
        "name": "Элайнеры",
        "duration_min": 60,
        "price": 500000,
        "employee_price": 440000,
        "is_active": True,
    },
    {
        "name": "Временная коронка на зубе пластик",
        "duration_min": 60,
        "price": 20000,
        "employee_price": 17500,
        "is_active": True,
    },
    {
        "name": "Временная коронка на имплантате",
        "duration_min": 60,
        "price": 30000,
        "employee_price": 26000,
        "is_active": True,
    },
    {
        "name": "Постоянная коронка на зубе Emax керамика",
        "duration_min": 60,
        "price": 55000,
        "employee_price": 41500,
        "is_active": True,
    },
    {
        "name": "Постоянная коронка на зубе диоксид циркония",
        "duration_min": 60,
        "price": 50000,
        "employee_price": 37500,
        "is_active": True,
    },
    {
        "name": "Постоянная коронка на импланте Емах",
        "duration_min": 60,
        "price": 55000,
        "employee_price": 45500,
        "is_active": True,
    },
    {
        "name": "Постоянная коронка на импланте на основе диоксида циркония",
        "duration_min": 60,
        "price": 50000,
        "employee_price": 41500,
        "is_active": True,
    },
    {
        "name": "Виниры авторские\\высокая эстетика",
        "duration_min": 60,
        "price": 85000,
        "employee_price": 67000,
        "is_active": True,
    },
    {
        "name": "Винир простой",
        "duration_min": 60,
        "price": 55000,
        "employee_price": 46500,
        "is_active": True,
    },
    {
        "name": "Сплинт",
        "duration_min": 60,
        "price": 120000,
        "employee_price": 100500,
        "is_active": True,
    },
    {
        "name": "Миосплинт для профилактики стираемости",
        "duration_min": 60,
        "price": 30000,
        "employee_price": 24000,
        "is_active": True,
    },
    {
        "name": "Восковое моделирование для тотальных работ 1 челюсть 14 зубов, на 6 мес",
        "duration_min": 60,
        "price": 120000,
        "employee_price": 116000,
        "is_active": True,
    },
    {
        "name": "Временная композитная накладка длительного ношения (в кресле) 14 шт, 1 челюсть, на 6 мес",
        "duration_min": 60,
        "price": 140000,
        "employee_price": 83500,
        "is_active": True,
    },
    {
        "name": "этап 1. воск моделир+накладка, 2 нед работа на 6 мес",
        "duration_min": 60,
        "price": 260000,
        "employee_price": 200000,
        "is_active": True,
    },
    {
        "name": "Вкладка",
        "duration_min": 60,
        "price": 40000,
        "employee_price": 33500,
        "is_active": True,
    },
]


def replace_services():
    """Полная замена услуг"""
    try:
        client = MongoClient("mongodb://localhost:27017/")
        db = client["medplatforma"]

        # Шаг 1: Подсчёт старых услуг
        old_count = db.services.count_documents({})
        print(f"📊 Старых услуг в базе: {old_count}")

        # Шаг 2: УДАЛЕНИЕ всех старых услуг
        print(f"\n🗑️  УДАЛЕНИЕ старых услуг...")
        result_delete = db.services.delete_many({})
        print(f"✅ Удалено: {result_delete.deleted_count}")

        # Шаг 3: Добавление created_at к каждой услуге
        now = datetime.utcnow()
        for service in SERVICES_DATA:
            service["created_at"] = now

        # Шаг 4: ВСТАВКА новых услуг
        print(f"\n📥 ВСТАВКА новых услуг с двумя прайсами...")
        result_insert = db.services.insert_many(SERVICES_DATA)
        print(f"✅ Вставлено: {len(result_insert.inserted_ids)}")

        # Шаг 5: Проверка
        new_count = db.services.count_documents({})
        with_employee_price = db.services.count_documents({"employee_price": {"$exists": True}})

        print(f"\n📊 ИТОГОВАЯ СТАТИСТИКА:")
        print(f"Всего услуг: {new_count}")
        print(f"С льготной ценой: {with_employee_price}")

        # Примеры
        print(f"\n📋 ПРИМЕРЫ (первые 3 услуги):")
        examples = list(db.services.find({}).limit(3))
        for svc in examples:
            print(f"  - {svc['name']}")
            print(f"    Клиент: {svc['price']}₽ | Сотрудник: {svc['employee_price']}₽")

        print(f"\n✅ ЗАМЕНА ЗАВЕРШЕНА УСПЕШНО!")

    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    print("🚀 ПОЛНАЯ ЗАМЕНА УСЛУГ С ДВУМЯ ПРАЙСАМИ")
    print("=" * 60)
    print("⚠️  ВНИМАНИЕ: Все существующие услуги будут УДАЛЕНЫ!")
    print("=" * 60)

    # Подтверждение (закомментируйте если хотите автозапуск)
    # response = input("Продолжить? (yes/no): ")
    # if response.lower() != 'yes':
    #     print("Отменено пользователем")
    #     sys.exit(0)

    replace_services()
    print("=" * 60)
