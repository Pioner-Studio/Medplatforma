# implement_finance_integration.py
# Задачи 8.1-8.6: Финансовая интеграция

import os
import re
from dotenv import load_dotenv
from pymongo import MongoClient


def check_current_finance_status():
    """8.1: Проверяем текущее состояние финансового модуля"""
    print("=== 8.1: Анализ текущей финансовой системы ===")

    load_dotenv()
    client = MongoClient(os.getenv("MONGO_URI"))
    db = client[os.getenv("DB_NAME", "medplatforma")]

    # Проверяем коллекции
    collections = {
        "appointments": "записи",
        "ledger": "финансовые операции",
        "services": "услуги с ценами",
        "patients": "пациенты",
    }

    for collection, description in collections.items():
        count = db[collection].count_documents({})
        print(f"📊 {description}: {count}")

    # Проверяем связанность данных
    appointments_with_services = db.appointments.count_documents({"service_id": {"$ne": None}})
    services_with_prices = db.services.count_documents({"price": {"$gt": 0}})
    ledger_entries = db.ledger.count_documents({})

    print(f"\n📈 Связанность данных:")
    print(f"Записей с услугами: {appointments_with_services}")
    print(f"Услуг с ценами: {services_with_prices}")
    print(f"Финансовых операций: {ledger_entries}")

    return {
        "has_appointments": appointments_with_services > 0,
        "has_services_with_prices": services_with_prices > 0,
        "has_ledger": ledger_entries > 0,
    }


def implement_appointment_finance_link():
    """8.2: Автосоздание записи о долге при создании записи"""
    print("\n=== 8.2: Связь записи ↔ финансовая операция ===")

    with open("main.py", "r", encoding="utf-8") as f:
        content = f.read()

    # Ищем функцию создания записи
    create_appointment_patterns = [
        "api_appointments_create",
        "add_event",
        "/api/appointments.*POST",
    ]

    found_create_function = False
    for pattern in create_appointment_patterns:
        if pattern in content:
            print(f"✅ Найдена функция создания записи: {pattern}")
            found_create_function = True
            break

    if not found_create_function:
        print("❌ Функция создания записи не найдена")
        return False

    # Проверяем, есть ли уже интеграция с финансами
    finance_integration_indicators = [
        "db.ledger.insert",
        "service_charge",
        "create_financial_record",
        "auto.*debt",
    ]

    has_integration = any(
        re.search(indicator, content) for indicator in finance_integration_indicators
    )

    if has_integration:
        print("✅ Финансовая интеграция уже присутствует")
    else:
        print("➕ Добавляем финансовую интеграцию...")
        add_finance_integration_to_appointments()

    return True


def add_finance_integration_to_appointments():
    """Добавляем финансовую интеграцию к созданию записей"""
    print("Внедряем автоматическое создание финансовых записей...")

    with open("main.py", "r", encoding="utf-8") as f:
        content = f.read()

    # Ищем функцию api_appointments_create
    create_func_start = content.find("def api_appointments_create")
    if create_func_start == -1:
        print("❌ Функция api_appointments_create не найдена")
        return

    # Ищем место вставки (после db.appointments.insert_one)
    insert_pos = content.find("db.appointments.insert_one", create_func_start)
    if insert_pos == -1:
        print("❌ Не найдено место для вставки финансовой логики")
        return

    # Находим конец строки с insert
    line_end = content.find("\n", insert_pos)

    # Финансовая логика для вставки
    finance_code = """

    # 🔥 ФИНАНСОВАЯ ИНТЕГРАЦИЯ: автосоздание долга
    try:
        if service_oid:
            service = db.services.find_one({"_id": service_oid}, {"price": 1, "name": 1})
            if service and service.get("price", 0) > 0:
                price = int(service["price"])

                # Создаем запись о долге (service_charge)
                finance_record = {
                    "patient_id": patient_oid,
                    "appointment_id": ins.inserted_id,
                    "kind": "service_charge",
                    "amount": price,
                    "service_id": service_oid,
                    "description": f"Услуга: {service.get('name', '')}",
                    "created_at": datetime.utcnow(),
                    "status": "pending"  # ожидает оплаты
                }

                db.ledger.insert_one(finance_record)
                print(f"[FINANCE] Создан долг на {price}₽ для пациента {patient_oid}")
    except Exception as e:
        print(f"[FINANCE ERROR] {e}")"""

    # Вставляем код
    content = content[:line_end] + finance_code + content[line_end:]

    # Сохраняем
    with open("main.py", "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Финансовая интеграция добавлена к созданию записей")


def implement_payment_processing():
    """8.3: Оплата услуги и обновление статуса записи"""
    print("\n=== 8.3: Обработка оплат ===")

    with open("main.py", "r", encoding="utf-8") as f:
        content = f.read()

    # Проверяем существующий API оплат
    payment_apis = ["/api/finance/record", "/api/payments", "api_finance_record"]

    has_payment_api = any(api in content for api in payment_apis)

    if has_payment_api:
        print("✅ API оплат найден")

        # Проверяем, обновляется ли статус записи при оплате
        if "appointment.*paid" in content or "status.*paid" in content:
            print("✅ Обновление статуса записи при оплате реализовано")
        else:
            print("➕ Добавляем обновление статуса записи при оплате...")
            enhance_payment_api_with_appointment_update()
    else:
        print("➕ Создаем API обработки оплат...")
        create_payment_api()


def enhance_payment_api_with_appointment_update():
    """Улучшаем API оплат для обновления статуса записи"""
    with open("main.py", "r", encoding="utf-8") as f:
        content = f.read()

    # Ищем функцию api_finance_record
    finance_func_pos = content.find("def api_finance_record")
    if finance_func_pos == -1:
        print("❌ Функция api_finance_record не найдена")
        return

    # Ищем место добавления логики (перед return)
    func_end = content.find("return jsonify", finance_func_pos)
    if func_end == -1:
        return

    # Добавляем логику обновления статуса записи
    appointment_update_code = """

    # 🔥 ОБНОВЛЕНИЕ СТАТУСА ЗАПИСИ ПРИ ОПЛАТЕ
    if kind == "payment" and service_id:
        try:
            # Находим запись по service_id и patient_id
            appointment = db.appointments.find_one({
                "patient_id": pid,
                "service_id": service_id,
                "status_key": {"$in": ["scheduled", "confirmed"]}
            })

            if appointment:
                # Проверяем, покрывает ли оплата стоимость услуги
                service = db.services.find_one({"_id": service_id}, {"price": 1})
                if service and amount >= service.get("price", 0):
                    # Обновляем статус записи на "paid"
                    db.appointments.update_one(
                        {"_id": appointment["_id"]},
                        {"$set": {"status_key": "paid", "paid_at": ts}}
                    )
                    print(f"[FINANCE] Запись {appointment['_id']} помечена как оплаченная")
        except Exception as e:
            print(f"[APPOINTMENT UPDATE ERROR] {e}")"""

    # Вставляем код
    content = content[:func_end] + appointment_update_code + "\n    " + content[func_end:]

    # Сохраняем
    with open("main.py", "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Добавлено обновление статуса записи при оплате")


def create_payment_api():
    """Создаем API для обработки оплат если его нет"""
    print("Создаем базовый API оплат...")

    with open("main.py", "r", encoding="utf-8") as f:
        content = f.read()

    # Ищем место для добавления (после других API)
    api_section = content.find("/api/finance/record")
    if api_section == -1:
        # Ищем любой другой API
        api_section = content.find("/api/patients")
        if api_section == -1:
            print("❌ Не найдено место для добавления API")
            return

    # Находим конец функции
    func_end = content.find("\n\n@app.route", api_section)
    if func_end == -1:
        func_end = content.find("\n@app.route", api_section + 100)

    # Новый API оплат
    payment_api = '''

@app.route("/api/payments/process", methods=["POST"])
@login_required
def api_process_payment():
    """Обработка оплаты пациента"""
    data = request.get_json(force=True, silent=True) or {}

    patient_id = data.get("patient_id")
    amount = data.get("amount", 0)
    payment_method = data.get("method", "cash")  # cash, card, transfer
    service_id = data.get("service_id")
    appointment_id = data.get("appointment_id")

    if not patient_id or amount <= 0:
        return jsonify({"ok": False, "error": "invalid_data"}), 400

    try:
        patient_oid = ObjectId(patient_id)
        service_oid = ObjectId(service_id) if service_id else None
        appointment_oid = ObjectId(appointment_id) if appointment_id else None

        ts = datetime.now()

        # Создаем запись об оплате
        payment_record = {
            "patient_id": patient_oid,
            "kind": "payment",
            "amount": int(amount),
            "method": payment_method,
            "service_id": service_oid,
            "appointment_id": appointment_oid,
            "ts": ts,
            "ts_iso": ts.strftime("%Y-%m-%dT%H:%M"),
            "processed_by": session.get("user_id"),
            "status": "completed"
        }

        result = db.ledger.insert_one(payment_record)

        # Обновляем статус записи если указана
        if appointment_oid:
            db.appointments.update_one(
                {"_id": appointment_oid},
                {"$set": {"status_key": "paid", "paid_at": ts}}
            )

        return jsonify({
            "ok": True,
            "payment_id": str(result.inserted_id),
            "amount": amount,
            "method": payment_method
        })

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500'''

    # Вставляем API
    content = content[:func_end] + payment_api + content[func_end:]

    # Сохраняем
    with open("main.py", "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ API обработки оплат создан")


def implement_financial_reports():
    """8.4: Отчеты по доходам врачей/услуг"""
    print("\n=== 8.4: Финансовые отчеты ===")

    with open("main.py", "r", encoding="utf-8") as f:
        content = f.read()

    # Проверяем существующие отчеты
    report_indicators = [
        "/finance_report",
        "doctor.*revenue",
        "service.*income",
        "financial.*analytics",
    ]

    has_reports = any(re.search(indicator, content) for indicator in report_indicators)

    if has_reports:
        print("✅ Финансовые отчеты найдены")

        # Проверяем детализацию по врачам
        if "doctor.*income" in content or "revenue.*doctor" in content:
            print("✅ Отчеты по врачам реализованы")
        else:
            print("➕ Добавляем отчеты по врачам...")
            add_doctor_revenue_reports()
    else:
        print("➕ Создаем финансовые отчеты...")
        create_financial_reports()


def add_doctor_revenue_reports():
    """Добавляем отчеты по доходам врачей"""
    with open("main.py", "r", encoding="utf-8") as f:
        content = f.read()

    # Ищем существующий finance_report
    report_pos = content.find("def finance_report")
    if report_pos == -1:
        print("❌ Функция finance_report не найдена")
        return

    # Добавляем новый API отчета по врачам
    func_end = content.find("\n\n@app.route", report_pos)
    if func_end == -1:
        func_end = content.find("\n@app.route", report_pos + 100)

    doctor_report_api = '''

@app.route("/api/reports/doctors_revenue", methods=["GET"])
@login_required
@role_required("admin", "registrar")
def api_doctors_revenue_report():
    """Отчет по доходам врачей"""

    # Параметры фильтрации
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    # Базовый пайплайн агрегации
    pipeline = [
        # Соединяем ledger с appointments
        {
            "$lookup": {
                "from": "appointments",
                "localField": "appointment_id",
                "foreignField": "_id",
                "as": "appointment"
            }
        },
        {"$unwind": "$appointment"},

        # Соединяем с врачами
        {
            "$lookup": {
                "from": "doctors",
                "localField": "appointment.doctor_id",
                "foreignField": "_id",
                "as": "doctor"
            }
        },
        {"$unwind": "$doctor"},

        # Группируем по врачам
        {
            "$group": {
                "_id": "$doctor._id",
                "doctor_name": {"$first": "$doctor.full_name"},
                "total_revenue": {"$sum": "$amount"},
                "appointments_count": {"$sum": 1},
                "avg_check": {"$avg": "$amount"}
            }
        },

        # Сортируем по доходу
        {"$sort": {"total_revenue": -1}}
    ]

    # Фильтр по датам если указан
    if start_date and end_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)

            pipeline.insert(0, {
                "$match": {
                    "ts": {"$gte": start_dt, "$lt": end_dt},
                    "kind": "payment"
                }
            })
        except ValueError:
            pass
    else:
        pipeline.insert(0, {"$match": {"kind": "payment"}})

    try:
        results = list(db.ledger.aggregate(pipeline))

        # Форматируем результат
        doctors_revenue = []
        for result in results:
            doctors_revenue.append({
                "doctor_id": str(result["_id"]),
                "doctor_name": result["doctor_name"],
                "total_revenue": int(result["total_revenue"]),
                "appointments_count": result["appointments_count"],
                "avg_check": int(result["avg_check"])
            })

        return jsonify({
            "ok": True,
            "period": f"{start_date} - {end_date}" if start_date and end_date else "Все время",
            "doctors": doctors_revenue,
            "total_doctors": len(doctors_revenue)
        })

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500'''

    # Вставляем API
    content = content[:func_end] + doctor_report_api + content[func_end:]

    # Сохраняем
    with open("main.py", "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Отчет по доходам врачей добавлен")


def create_financial_reports():
    """Создаем базовые финансовые отчеты"""
    print("Создаем систему финансовых отчетов...")
    # Эта функция может быть расширена для создания полноценной отчетности
    add_doctor_revenue_reports()


def test_finance_integration():
    """8.5-8.6: Тестируем финансовую интеграцию"""
    print("\n=== 8.5-8.6: Тестирование финансовой интеграции ===")

    try:
        load_dotenv()
        client = MongoClient(os.getenv("MONGO_URI"))
        db = client[os.getenv("DB_NAME", "medplatforma")]

        # Проверяем связанность данных
        total_appointments = db.appointments.count_documents({})
        appointments_with_services = db.appointments.count_documents({"service_id": {"$ne": None}})
        ledger_entries = db.ledger.count_documents({})

        print(f"📊 Статистика:")
        print(f"Всего записей: {total_appointments}")
        print(f"Записей с услугами: {appointments_with_services}")
        print(f"Финансовых операций: {ledger_entries}")

        # Проверяем типы операций в ledger
        operation_types = db.ledger.distinct("kind")
        print(f"Типы операций: {operation_types}")

        # Анализируем долги
        if "service_charge" in operation_types and "payment" in operation_types:
            total_charges = list(
                db.ledger.aggregate(
                    [
                        {"$match": {"kind": "service_charge"}},
                        {"$group": {"_id": None, "total": {"$sum": "$amount"}}},
                    ]
                )
            )

            total_payments = list(
                db.ledger.aggregate(
                    [
                        {"$match": {"kind": "payment"}},
                        {"$group": {"_id": None, "total": {"$sum": "$amount"}}},
                    ]
                )
            )

            charges_sum = total_charges[0]["total"] if total_charges else 0
            payments_sum = total_payments[0]["total"] if total_payments else 0

            print(f"💰 Общая сумма услуг: {charges_sum}₽")
            print(f"💳 Общая сумма оплат: {payments_sum}₽")
            print(f"💸 Общий долг: {charges_sum - payments_sum}₽")

            if ledger_entries > 0:
                print("✅ Финансовая система активна")
                return True

        print("⚠️ Финансовые операции требуют настройки")
        return False

    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False


def create_finance_summary():
    """Создаем итоговую сводку по финансовой интеграции"""
    print("\n" + "=" * 60)
    print("💰 СВОДКА ПО ФИНАНСОВОЙ ИНТЕГРАЦИИ (задачи 8.1-8.6)")
    print("=" * 60)

    # Проверяем выполнение задач
    finance_status = check_current_finance_status()

    tasks = [
        ("8.1", "Анализ финансовой системы", True),
        ("8.2", "Автосоздание долга", implement_appointment_finance_link()),
        ("8.3", "Обработка оплат", implement_payment_processing()),
        ("8.4", "Отчеты по врачам/услугам", implement_financial_reports()),
        ("8.5-8.6", "Управление долгами", test_finance_integration()),
    ]

    completed = 0
    for task_id, description, status in tasks:
        icon = "✅" if status else "❌"
        print(f"{icon} {task_id}: {description}")
        if status:
            completed += 1

    print(f"\nВыполнено: {completed}/{len(tasks)} задач")

    if completed >= len(tasks) * 0.8:
        print("🎉 ФИНАНСОВАЯ ИНТЕГРАЦИЯ РЕАЛИЗОВАНА!")
        return True
    else:
        print("⚠️ Требуются дополнительные доработки")
        return False


def main():
    print("💰 ФИНАНСОВАЯ ИНТЕГРАЦИЯ")
    print("Задачи 8.1-8.6 из чек-листа")
    print("=" * 60)

    # Выполняем интеграцию
    success = create_finance_summary()

    print("\n" + "=" * 60)
    print("🔄 СЛЕДУЮЩИЕ ШАГИ:")

    if success:
        print("1. Протестируйте создание записи - должен создаваться долг")
        print("2. Проверьте оплату через API /api/payments/process")
        print("3. Убедитесь в обновлении статуса записи при оплате")
        print("4. Проверьте отчет по доходам врачей")
        print("5. Переходите к задачам 9.1-9.4: Реальные пользователи")
    else:
        print("1. Проверьте ошибки в финансовой интеграции")
        print("2. Убедитесь в корректности цен услуг")
        print("3. Протестируйте создание долгов и оплат")

    print("\nДля ручного тестирования:")
    print("- Создайте запись с услугой (должен создаться долг)")
    print("- Оплатите услугу через API или интерфейс")
    print("- Проверьте изменение статуса записи на 'paid'")
    print("- Посмотрите отчет по доходам врачей")


if __name__ == "__main__":
    main()
