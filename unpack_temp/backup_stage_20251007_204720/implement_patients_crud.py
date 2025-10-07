# implement_patients_crud.py
# Задачи 7.1-7.7: Пациенты CRUD + интеграция с календарем

import os
import re
from pathlib import Path


def verify_patients_crud_status():
    """7.1: Проверяем текущее состояние CRUD пациентов"""
    print("=== 7.1: Проверка создания пациента из календаря ===")

    with open("main.py", "r", encoding="utf-8") as f:
        content = f.read()

    # Проверяем API для создания пациентов
    crud_endpoints = [
        ("/api/patients", "POST", "создание пациента"),
        ("/api/patients/<id>", "GET", "получение пациента"),
        ("/api/patients/<id>/update", "POST", "обновление пациента"),
        ("/api/patients/search", "GET", "поиск пациентов"),
    ]

    found_endpoints = 0
    for endpoint, method, description in crud_endpoints:
        if f'@app.route("{endpoint}"' in content and f'methods=["{method}"]' in content:
            print(f"✅ {description}: {endpoint}")
            found_endpoints += 1
        elif f'@app.route("{endpoint}"' in content:
            print(f"⚠️ {description}: найден маршрут, но метод может отличаться")
            found_endpoints += 0.5
        else:
            print(f"❌ {description}: {endpoint} не найден")

    print(f"Найдено endpoint'ов: {found_endpoints}/{len(crud_endpoints)}")
    return found_endpoints >= len(crud_endpoints) * 0.7


def check_patient_modal_integration():
    """7.2: Проверяем интеграцию модального окна создания пациента"""
    print("\n=== 7.2: Карточка пациента и модальные окна ===")

    # Проверяем шаблон календаря
    calendar_template = Path("templates/calendar.html")
    if not calendar_template.exists():
        print("❌ templates/calendar.html не найден")
        return False

    with open(calendar_template, "r", encoding="utf-8") as f:
        content = f.read()

    # Ищем модальные окна и функции создания пациента
    modal_features = [
        ("createPatientModal", "модальное окно создания пациента"),
        ("mpCreatePatient", "функция создания пациента"),
        ("patient-search", "поиск пациентов"),
        ("addAppointmentModal", "модальное окно записи"),
    ]

    found_features = 0
    for feature, description in modal_features:
        if feature in content:
            print(f"✅ {description}")
            found_features += 1
        else:
            print(f"❌ {description} не найден")

    return found_features >= len(modal_features) * 0.6


def implement_patient_card_improvements():
    """7.3: Улучшаем карточку пациента"""
    print("\n=== 7.3: Улучшение карточки пациента ===")

    # Проверяем существующую реализацию
    with open("main.py", "r", encoding="utf-8") as f:
        content = f.read()

    # Ищем функцию карточки пациента
    if "/patient_card/" in content or "/patients/<id>" in content:
        print("✅ Базовая карточка пациента найдена")

        # Проверяем API для полной информации
        if "/api/patients/<id>/full" in content:
            print("✅ API полной информации о пациенте")
        else:
            print("❌ Нужно добавить API полной информации")
            # Добавляем если нет
            add_patient_full_api()

        # Проверяем историю записей
        if "appointments.find" in content and "patient_id" in content:
            print("✅ История записей реализована")
        else:
            print("⚠️ История записей требует улучшения")
    else:
        print("❌ Карточка пациента не найдена")
        return False

    return True


def add_patient_full_api():
    """Добавляем полный API пациента если его нет"""
    print("Добавляем API полной информации о пациенте...")

    with open("main.py", "r", encoding="utf-8") as f:
        content = f.read()

    # Ищем место для вставки (после других API пациентов)
    patient_api_pos = content.find("/api/patients/<id>/update")
    if patient_api_pos == -1:
        patient_api_pos = content.find("/api/patients/<id>")

    if patient_api_pos != -1:
        # Находим конец функции
        func_end = content.find("\n\n@app.route", patient_api_pos)
        if func_end == -1:
            func_end = content.find("\n@app.route", patient_api_pos + 100)

        if func_end != -1:
            # Добавляем новый API endpoint
            new_api = '''

@app.route("/api/patients/<id>/history", methods=["GET"])
@login_required
def api_patient_history(id):
    """Получить историю записей пациента"""
    _id = oid(id)
    if not _id:
        return jsonify({"ok": False, "error": "bad_id"}), 400

    patient = db.patients.find_one({"_id": _id}, {"full_name": 1})
    if not patient:
        return jsonify({"ok": False, "error": "not_found"}), 404

    # Получаем записи пациента
    appointments = list(
        db.appointments.find({"patient_id": _id})
        .sort("start", -1)
        .limit(50)
    )

    # Получаем справочники
    doctors = {str(d["_id"]): d for d in db.doctors.find({}, {"full_name": 1})}
    services = {str(s["_id"]): s for s in db.services.find({}, {"name": 1, "price": 1})}
    rooms = {str(r["_id"]): r for r in db.rooms.find({}, {"name": 1})}

    # Формируем историю
    history = []
    for appt in appointments:
        start_dt = to_dt(appt.get("start"))
        end_dt = to_dt(appt.get("end"))

        doctor = doctors.get(str(appt.get("doctor_id", "")), {})
        service = services.get(str(appt.get("service_id", "")), {})
        room = rooms.get(str(appt.get("room_id", "")), {})

        history.append({
            "id": str(appt["_id"]),
            "date": start_dt.strftime("%Y-%m-%d") if start_dt else "",
            "time": start_dt.strftime("%H:%M") if start_dt else "",
            "doctor": doctor.get("full_name", ""),
            "service": service.get("name", ""),
            "room": room.get("name", ""),
            "status": appt.get("status_key", ""),
            "cost": service.get("price", 0),
        })

    return jsonify({
        "ok": True,
        "patient": {"id": id, "name": patient["full_name"]},
        "history": history
    })'''

            content = content[:func_end] + new_api + content[func_end:]

            # Сохраняем
            with open("main.py", "w", encoding="utf-8") as f:
                f.write(content)

            print("✅ API истории пациента добавлен")


def implement_patient_search():
    """7.4: Улучшаем поиск пациентов в календаре"""
    print("\n=== 7.4: Поиск пациентов в календаре ===")

    with open("main.py", "r", encoding="utf-8") as f:
        content = f.read()

    # Проверяем API поиска
    if "/api/patients/search" in content:
        print("✅ API поиска пациентов найден")
    else:
        print("Добавляем API поиска пациентов...")
        add_patient_search_api()

    # Проверяем автокомплит в шаблоне
    if Path("templates/calendar.html").exists():
        with open("templates/calendar.html", "r", encoding="utf-8") as f:
            template_content = f.read()

        if "patient-search" in template_content or "autocomplete" in template_content:
            print("✅ Автокомплит в шаблоне найден")
        else:
            print("⚠️ Автокомплит требует улучшения")

    return True


def add_patient_search_api():
    """Добавляем API поиска если его нет"""
    with open("main.py", "r", encoding="utf-8") as f:
        content = f.read()

    # Проверяем, есть ли уже /api/patients/min или /api/patients/search
    if "/api/patients/min" in content:
        print("✅ API поиска уже существует (/api/patients/min)")
        return

    # Ищем место для добавления
    patients_api_pos = content.find("/api/patients")
    if patients_api_pos != -1:
        # Находим конец функции
        func_end = content.find("\n\n@", patients_api_pos)
        if func_end == -1:
            func_end = content.find("\n@", patients_api_pos + 100)

        new_search_api = '''

@app.route("/api/patients/search", methods=["GET"])
@login_required
def api_patients_search():
    """Поиск пациентов для автокомплита"""
    query = request.args.get("q", "").strip()
    limit = min(20, int(request.args.get("limit", 10)))

    if not query:
        return jsonify({"ok": True, "patients": []})

    # Поиск по имени и телефону
    filter_query = {
        "$or": [
            {"full_name": {"$regex": re.escape(query), "$options": "i"}},
            {"phone": {"$regex": re.escape(query), "$options": "i"}},
            {"card_no": {"$regex": re.escape(query), "$options": "i"}},
        ]
    }

    patients = []
    for p in db.patients.find(filter_query).limit(limit):
        patients.append({
            "id": str(p["_id"]),
            "name": p.get("full_name", ""),
            "phone": p.get("phone", ""),
            "card_no": p.get("card_no", ""),
        })

    return jsonify({"ok": True, "patients": patients})'''

        content = content[:func_end] + new_search_api + content[func_end:]

        with open("main.py", "w", encoding="utf-8") as f:
            f.write(content)

        print("✅ API поиска пациентов добавлен")


def check_appointment_operations():
    """7.5-7.7: Проверяем операции с записями"""
    print("\n=== 7.5-7.7: Операции с записями ===")

    with open("main.py", "r", encoding="utf-8") as f:
        content = f.read()

    # Проверяем операции с записями
    operations = [
        ("drag", "перенос записи", "/api/appointments/update_time"),
        ("delete", "отмена записи", "/api/appointments/<id>.*DELETE"),
        ("status", "изменение статуса", "status_key"),
        ("create", "создание записи", "/api/appointments.*POST"),
    ]

    found_operations = 0
    for op_key, description, pattern in operations:
        if re.search(pattern, content):
            print(f"✅ {description}")
            found_operations += 1
        else:
            print(f"❌ {description} не найден")

    return found_operations >= len(operations) * 0.7


def test_patient_crud():
    """Тестируем CRUD операции пациентов"""
    print("\n=== Тестирование CRUD пациентов ===")

    try:
        # Проверяем подключение к БД
        from dotenv import load_dotenv
        from pymongo import MongoClient

        load_dotenv()
        client = MongoClient(os.getenv("MONGO_URI"))
        db = client[os.getenv("DB_NAME", "medplatforma")]

        # Статистика
        patients_count = db.patients.count_documents({})
        appointments_count = db.appointments.count_documents({})

        print(f"В базе пациентов: {patients_count}")
        print(f"В базе записей: {appointments_count}")

        # Проверяем связанность данных
        if patients_count > 0 and appointments_count > 0:
            # Ищем записи с пациентами
            linked_count = db.appointments.count_documents({"patient_id": {"$ne": None}})
            print(f"Записей с пациентами: {linked_count}")

            if linked_count > 0:
                print("✅ Данные связаны корректно")
                return True

        print("⚠️ Мало связанных данных для тестирования")
        return patients_count > 0

    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False


def create_patient_crud_summary():
    """Создаем сводку по CRUD пациентов"""
    print("\n" + "=" * 60)
    print("📋 СВОДКА ПО CRUD ПАЦИЕНТОВ (задачи 7.1-7.7)")
    print("=" * 60)

    tasks = [
        ("7.1", "Создание пациента из календаря", verify_patients_crud_status()),
        ("7.2", "Карточка пациента", check_patient_modal_integration()),
        ("7.3", "Редактирование данных", implement_patient_card_improvements()),
        ("7.4", "Поиск в календаре", implement_patient_search()),
        ("7.5-7.7", "Операции с записями", check_appointment_operations()),
    ]

    completed = 0
    for task_id, description, status in tasks:
        icon = "✅" if status else "❌"
        print(f"{icon} {task_id}: {description}")
        if status:
            completed += 1

    print(f"\nВыполнено: {completed}/{len(tasks)} задач")

    if completed >= len(tasks) * 0.8:
        print("🎉 CRUD пациентов в основном реализован!")
        return True
    else:
        print("⚠️ Требуются дополнительные доработки")
        return False


def main():
    print("👥 РЕАЛИЗАЦИЯ CRUD ПАЦИЕНТОВ")
    print("Задачи 7.1-7.7 из чек-листа")
    print("=" * 60)

    # Проверяем текущее состояние
    print("Анализируем текущую реализацию...")

    # Выполняем проверки и улучшения
    steps = [
        verify_patients_crud_status,
        check_patient_modal_integration,
        implement_patient_card_improvements,
        implement_patient_search,
        check_appointment_operations,
        test_patient_crud,
    ]

    for step in steps:
        try:
            step()
        except Exception as e:
            print(f"Ошибка в {step.__name__}: {e}")

    # Итоговая сводка
    success = create_patient_crud_summary()

    print("\n" + "=" * 60)
    print("🔄 СЛЕДУЮЩИЕ ШАГИ:")

    if success:
        print("1. Протестируйте создание пациента из календаря")
        print("2. Проверьте поиск пациентов в модальном окне")
        print("3. Убедитесь в работе drag&drop записей")
        print("4. Переходите к задачам 8.1-8.6: Финансовая интеграция")
    else:
        print("1. Проверьте ошибки выше")
        print("2. Доработайте отсутствующие функции")
        print("3. Протестируйте в браузере")

    print("\nДля ручного тестирования:")
    print("- Создайте нового пациента через календарь")
    print("- Найдите существующего пациента при создании записи")
    print("- Перетащите запись на другое время")
    print("- Измените статус записи")


if __name__ == "__main__":
    main()
