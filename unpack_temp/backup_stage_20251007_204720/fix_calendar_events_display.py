# fix_calendar_events_display.py
# Исправляем отображение записей в календаре

import re


def fix_api_events_function():
    """Исправляем функцию api_events для правильного отображения записей"""
    print("=== Исправление функции api_events ===")

    with open("main.py", "r", encoding="utf-8") as f:
        content = f.read()

    # Ищем и заменяем функцию api_events полностью
    api_events_pattern = r'@app\.route\("/api/events"\).*?@login_required.*?def api_events\(\):.*?return jsonify\(events\)'

    new_api_events = """@app.route("/api/events")
@login_required
def api_events():
    # 1) Диапазон, который шлёт FullCalendar
    start_str = request.args.get("start")
    end_str = request.args.get("end")
    patient_id = (request.args.get("patient_id") or "").strip()

    # 2) Фильтры (поддерживаем и id, и имена)
    doctor_id = request.args.get("doctor_id")
    room_id = request.args.get("room_id")
    room_name = request.args.get("room_name")
    service_id = request.args.get("service_id")
    service_name = request.args.get("service_name")

    start_dt = parse_iso(start_str)
    end_dt = parse_iso(end_str)

    # 3) Базовый запрос: пересечение диапазона
    q = {}
    if start_dt and end_dt:
        q["start"] = {"$lt": end_dt}
        q["end"] = {"$gt": start_dt}

    # 🔥 ФИЛЬТРАЦИЯ ПО РОЛЯМ
    user_role = session.get("user_role", "")
    user_id = session.get("user_id", "")

    if user_role == "doctor":
        # Врач видит только свои записи
        try:
            # Находим ObjectId врача по user_id
            user_doc = db.users.find_one({"_id": ObjectId(user_id)})
            if user_doc:
                # Ищем врача по email/login
                doctor = db.doctors.find_one({"email": user_doc.get("login", "")})
                if doctor:
                    q["doctor_id"] = doctor["_id"]
                else:
                    # Если связь не найдена, не показываем записи
                    return jsonify([])
            else:
                return jsonify([])
        except Exception:
            return jsonify([])

    elif user_role == "registrar":
        # Регистратор видит все записи (без дополнительных фильтров)
        pass

    elif user_role == "admin":
        # Админ видит все записи (без дополнительных фильтров)
        pass

    else:
        # Неизвестная роль - показываем все записи (для совместимости)
        pass

    # 4) Фильтр по врачу (если передан)
    if doctor_id:
        try:
            q["doctor_id"] = ObjectId(doctor_id)
        except Exception:
            pass

    # 5) Фильтр по кабинету
    if room_id:
        try:
            q["room_id"] = ObjectId(room_id)
        except Exception:
            pass
    elif room_name:
        r = db.rooms.find_one({"name": room_name}, {"_id": 1})
        if r:
            q["room_id"] = r["_id"]

    # 6) Фильтр по услуге
    if service_id:
        try:
            q["service_id"] = ObjectId(service_id)
        except Exception:
            pass
    elif service_name:
        s = db.services.find_one({"name": service_name}, {"_id": 1})
        if s:
            q["service_id"] = s["_id"]

    # 6+) Фильтр по пациенту
    if patient_id:
        try:
            q["patient_id"] = ObjectId(patient_id)
        except Exception:
            pass

    # 7) Справочники для названий/цветов
    doctors_map = {str(d["_id"]): d for d in db.doctors.find({}, {"full_name": 1, "avatar": 1})}
    patients_map = {str(p["_id"]): p for p in db.patients.find({}, {"full_name": 1, "avatar": 1})}
    services_map = {
        str(s["_id"]): s for s in db.services.find({}, {"name": 1, "color": 1, "duration_min": 1})
    }
    status_map = {
        s["key"]: s for s in db.visit_statuses.find({}, {"key": 1, "title": 1, "color": 1})
    }
    rooms_map = {str(r["_id"]): r for r in db.rooms.find({}, {"name": 1})}

    # 8) Формируем ответ в формате FullCalendar
    events = []
    cursor = db.appointments.find(q).sort("start", 1)

    for a in cursor:
        # --- нормализуем ID как строки (могут быть None)
        did = str(a.get("doctor_id") or "")
        pid = str(a.get("patient_id") or "")
        sid = str(a.get("service_id") or "")
        rid = str(a.get("room_id") or "")

        # --- гарантируем тип datetime
        a_start = to_dt(a.get("start"))
        if not a_start:
            # битая запись без даты — пропускаем
            continue

        a_end = to_dt(a.get("end"))
        if not a_end:
            # если нет end — считаем по длительности услуги (если есть), иначе 30 мин
            dur = services_map.get(sid, {}).get("duration_min", 30)
            try:
                dur = int(dur)
            except Exception:
                dur = 30
            a_end = add_minutes(a_start, dur)

        # --- справочники
        doc = doctors_map.get(did, {})
        pat = patients_map.get(pid, {})
        srv = services_map.get(sid, {})
        rm = rooms_map.get(rid, {})
        st = status_map.get(a.get("status_key", "scheduled"), {})

        # --- заголовок события
        title = f'{srv.get("name", "Услуга")} — {pat.get("full_name", "Пациент")}'

        events.append(
            {
                "id": str(a["_id"]),
                "title": title,
                "start": a_start.isoformat(),
                "end": a_end.isoformat(),
                "backgroundColor": st.get("color") or srv.get("color") or "#3498db",
                "borderColor": st.get("color") or srv.get("color") or "#3498db",
                "extendedProps": {
                    "patient": pat.get("full_name", ""),
                    "doctor": doc.get("full_name", ""),
                    "service": srv.get("name", ""),
                    "room": rm.get("name", ""),
                    "status": st.get("title", ""),
                    "doctor_id": did,
                    "patient_id": pid,
                    "service_id": sid,
                    "room_id": rid,
                },
            }
        )

    return jsonify(events)"""

    # Заменяем функцию
    content = re.sub(api_events_pattern, new_api_events, content, flags=re.DOTALL)

    # Сохраняем
    with open("main.py", "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Функция api_events исправлена")


def ensure_role_required_decorator():
    """Убеждаемся, что декоратор role_required добавлен к api_events"""
    print("=== Проверка декоратора для api_events ===")

    with open("main.py", "r", encoding="utf-8") as f:
        content = f.read()

    # Ищем функцию api_events
    api_events_pos = content.find('@app.route("/api/events")')
    if api_events_pos == -1:
        print("❌ Функция api_events не найдена")
        return

    # Проверяем, есть ли уже @role_required
    func_section = content[api_events_pos : api_events_pos + 500]

    if "@role_required" not in func_section:
        print("Добавляем декоратор @role_required к api_events...")

        # Находим позицию def api_events
        def_pos = content.find("def api_events():", api_events_pos)
        if def_pos != -1:
            # Добавляем декоратор перед функцией
            role_decorator = '@role_required("admin", "registrar", "doctor")\n'
            content = content[:def_pos] + role_decorator + content[def_pos:]

            # Сохраняем
            with open("main.py", "w", encoding="utf-8") as f:
                f.write(content)

            print("✅ Декоратор добавлен к api_events")
    else:
        print("✅ Декоратор уже есть у api_events")


def check_appointments_data():
    """Проверяем наличие записей в базе данных"""
    print("=== Проверка данных appointments ===")

    try:
        from dotenv import load_dotenv
        from pymongo import MongoClient
        import os

        load_dotenv()
        client = MongoClient(os.getenv("MONGO_URI"))
        db = client[os.getenv("DB_NAME", "medplatforma")]

        # Считаем записи
        total_appointments = db.appointments.count_documents({})
        print(f"Всего записей в БД: {total_appointments}")

        if total_appointments > 0:
            # Показываем несколько примеров
            sample = list(db.appointments.find({}).limit(3))
            print("Примеры записей:")
            for i, appt in enumerate(sample, 1):
                print(f"  {i}. ID: {appt.get('_id')}")
                print(f"     Начало: {appt.get('start')}")
                print(f"     Конец: {appt.get('end')}")
                print(f"     Врач ID: {appt.get('doctor_id')}")
                print(f"     Пациент ID: {appt.get('patient_id')}")
                print()
        else:
            print("❌ В базе нет записей!")

        # Проверяем связанные коллекции
        doctors_count = db.doctors.count_documents({})
        patients_count = db.patients.count_documents({})
        services_count = db.services.count_documents({})

        print(f"Врачей: {doctors_count}")
        print(f"Пациентов: {patients_count}")
        print(f"Услуг: {services_count}")

        return total_appointments > 0

    except Exception as e:
        print(f"❌ Ошибка проверки БД: {e}")
        return False


def test_api_endpoint():
    """Тестируем API endpoint"""
    print("=== Тестирование API /api/events ===")

    try:
        import requests
        from datetime import datetime, timedelta

        # Параметры запроса (как FullCalendar)
        start_date = datetime.now().replace(day=1)
        end_date = start_date + timedelta(days=32)

        params = {"start": start_date.isoformat(), "end": end_date.isoformat()}

        # Делаем запрос
        response = requests.get("http://localhost:5000/api/events", params=params)

        print(f"Статус ответа: {response.status_code}")

        if response.status_code == 200:
            try:
                events = response.json()
                print(f"Получено событий: {len(events)}")

                if events:
                    print("Первое событие:")
                    first_event = events[0]
                    for key, value in first_event.items():
                        print(f"  {key}: {value}")
                else:
                    print("События не найдены")

            except Exception as e:
                print(f"Ошибка парсинга JSON: {e}")
                print("Ответ сервера:", response.text[:500])
        else:
            print(f"Ошибка API: {response.status_code}")
            print("Ответ:", response.text[:500])

    except requests.exceptions.ConnectionError:
        print("❌ Сервер не запущен. Запустите: python main.py")
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")


def main():
    print("🔧 ИСПРАВЛЕНИЕ ОТОБРАЖЕНИЯ ЗАПИСЕЙ В КАЛЕНДАРЕ")
    print("=" * 60)

    # 1. Исправляем функцию api_events
    fix_api_events_function()

    # 2. Проверяем декораторы
    ensure_role_required_decorator()

    # 3. Проверяем данные в БД
    has_data = check_appointments_data()

    if not has_data:
        print("\n❌ ПРОБЛЕМА: В базе нет записей!")
        print("Решение:")
        print("1. Создайте несколько записей через интерфейс")
        print("2. Или импортируйте тестовые данные")
        return

    print("\n" + "=" * 60)
    print("✅ ИСПРАВЛЕНИЯ ПРИМЕНЕНЫ!")
    print("\nДля проверки:")
    print("1. python main.py")
    print("2. Откройте http://localhost:5000")
    print("3. Проверьте отображение записей в календаре")
    print("4. Если записи не видны, проверьте консоль браузера на ошибки")

    print("\nЕсли сервер уже запущен, протестируем API:")
    test_api_endpoint()


if __name__ == "__main__":
    main()
