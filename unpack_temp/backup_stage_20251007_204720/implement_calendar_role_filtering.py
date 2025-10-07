# implement_calendar_role_filtering.py
# Задачи 6.4-6.5: Фильтрация календаря по ролям и скрытие элементов интерфейса

import re
import os

def update_calendar_api_for_roles():
    """6.4: Фильтрация календаря по ролям"""
    print("=== 6.4: Реализация фильтрации календаря по ролям ===")

    # Читаем main.py
    with open("main.py", "r", encoding="utf-8") as f:
        content = f.read()

    # Находим функцию api_events
    api_events_pattern = r'@app\.route\("/api/events"\).*?def api_events\(\):.*?return jsonify\(events\)'

    match = re.search(api_events_pattern, content, re.DOTALL)
    if not match:
        print("❌ Функция api_events не найдена")
        return False

    # Новая версия api_events с фильтрацией по ролям
    new_api_events = '''@app.route("/api/events")
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

    # 🔥 НОВОЕ: Фильтрация по ролям
    user_role = session.get("user_role", "")
    user_id = session.get("user_id", "")

    if user_role == "doctor":
        # Врач видит только свои записи
        try:
            # Находим ObjectId врача по user_id
            user_doc = db.users.find_one({"_id": ObjectId(user_id)})
            if user_doc and "doctor_id" in user_doc:
                q["doctor_id"] = user_doc["doctor_id"]
            else:
                # Если doctor_id не связан с пользователем, ищем по email/login
                doctor = db.doctors.find_one({"email": user_doc.get("login", "")})
                if doctor:
                    q["doctor_id"] = doctor["_id"]
                else:
                    # Если связь не найдена, не показываем записи
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
        # Неизвестная роль - не показываем записи
        return jsonify([])

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
                    "patient": pat.get("full_name"),
                    "doctor": doc.get("full_name"),
                    "service": srv.get("name"),
                    "room": rm.get("name"),
                    "status": st.get("title"),
                    "doctor_id": did,
                    "patient_id": pid,
                    "service_id": sid,
                    "room_id": rid,
                },
            }
        )

    return jsonify(events)'''

    # Заменяем функцию
    content = re.sub(api_events_pattern, new_api_events, content, flags=re.DOTALL)

    # Сохраняем
    with open("main.py", "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ API календаря обновлён с фильтрацией по ролям")
    return True

def update_calendar_view_for_roles():
    """Обновляем основную функцию календаря для ролей"""
    print("=== Обновление calendar_view для ролей ===")

    # Читаем main.py
    with open("main.py", "r", encoding="utf-8") as f:
        content = f.read()

    # Ищем функцию calendar_view
    calendar_pattern = r'@app\.route\("/calendar"\).*?@login_required.*?def calendar_view\(\):.*?return render_template\([^)]+\)'

    match = re.search(calendar_pattern, content, re.DOTALL)
    if not match:
        print("❌ Функция calendar_view не найдена")
        return False

    # Новая версия с учётом ролей
    new_calendar_view = '''@app.route("/calendar")
@login_required
def calendar_view():
    # Получаем реальные данные из БД для шаблона
    user_role = session.get("user_role", "")
    user_id = session.get("user_id", "")

    # Фильтрация данных по ролям
    if user_role == "doctor":
        # Врач видит только свои данные
        user_doc = db.users.find_one({"_id": ObjectId(user_id)})
        doctor_filter = {}
        if user_doc and "doctor_id" in user_doc:
            doctor_filter = {"_id": user_doc["doctor_id"]}
        else:
            # Поиск по email
            doctor = db.doctors.find_one({"email": user_doc.get("login", "")})
            if doctor:
                doctor_filter = {"_id": doctor["_id"]}
            else:
                doctor_filter = {"_id": None}  # Не найдено - пустой результат

        doctors = list(db.doctors.find(doctor_filter))
    else:
        # Админ и регистратор видят всех врачей
        doctors = list(db.doctors.find({"status": "активен"}))

    # Пациенты и услуги всегда доступны всем ролям
    patients = list(db.patients.find())
    services = list(db.services.find({"is_active": True}))

    rooms = list(db.rooms.find({"active": True}, {"name": 1, "status": 1}).sort("name", 1))
    cabinets = [r["name"] for r in rooms]

    now = datetime.now()

    # Считаем статус "на сейчас" + ближайший приём (если свободен)
    room_info = {}
    for r in rooms:
        state = calc_room_status_now(r, now)  # 'available'|'occupied'|'maintenance'
        text = (
            "Обслуживание"
            if state == "maintenance"
            else ("Занят" if state == "occupied" else "Свободен")
        )
        color = (
            "#d97706" if state == "maintenance" else ("#cc0000" if state == "occupied" else "green")
        )

        next_info = None
        if state == "available":
            a = get_next_event_for_room(r["_id"], now)
            if a:
                sdt = a.get("start")
                in_min = minutes_until(sdt, now)
                srv = (
                    db.services.find_one({"_id": a.get("service_id")}, {"name": 1})
                    if a.get("service_id")
                    else None
                )
                pat = (
                    db.patients.find_one({"_id": a.get("patient_id")}, {"full_name": 1})
                    if a.get("patient_id")
                    else None
                )
                next_info = {
                    "start": sdt.strftime("%Y-%m-%dT%H:%M") if isinstance(sdt, datetime) else "",
                    "service": (srv or {}).get("name", ""),
                    "patient": (pat or {}).get("full_name", ""),
                    "in_minutes": in_min,
                }

        room_info[r["name"]] = {"state": state, "text": text, "color": color, "next": next_info}

    total_rooms = len(cabinets)
    free_rooms = sum(1 for nfo in room_info.values() if nfo["state"] == "available")

    return render_template(
        "calendar.html",
        metrics={"total_rooms": total_rooms, "free_rooms": free_rooms},
        room_info=room_info,
        cabinets=cabinets,
        doctors=doctors,
        patients=patients,
        services=services,
        user_role=user_role,  # Передаём роль в шаблон
    )'''

    # Заменяем функцию
    content = re.sub(calendar_pattern, new_calendar_view, content, flags=re.DOTALL)

    # Сохраняем
    with open("main.py", "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Функция calendar_view обновлена для ролей")
    return True

def update_base_template():
    """6.5: Скрытие элементов меню по ролям"""
    print("=== 6.5: Обновление base.html для скрытия элементов по ролям ===")

    if not os.path.exists("templates/base.html"):
        print("❌ Файл templates/base.html не найден")
        return False

    with open("templates/base.html", "r", encoding="utf-8") as f:
        content = f.read()

    # Элементы, которые нужно скрыть по ролям
    admin_only_links = [
        ('href="/doctors"', "Врачи"),
        ('href="/services"', "Услуги"),
        ('href="/rooms"', "Кабинеты"),
        ('href="/data_tools"', "Инструменты данных"),
        ('href="/backup"', "Резервные копии"),
        ('>Администрирование<', "Раздел администрирования"),
    ]

    admin_registrar_links = [
        ('href="/patients"', "Пациенты"),
        ('href="/finance"', "Финансы"),
    ]

    changes_made = 0

    # Скрываем админские элементы
    for link_pattern, description in admin_only_links:
        if link_pattern in content:
            # Ищем родительский элемент (обычно <li> или <a>)
            link_pos = content.find(link_pattern)

            # Ищем начало тега (назад до <)
            tag_start = content.rfind("<", 0, link_pos)

            # Ищем конец тега (вперёд до >)
            tag_end = content.find(">", link_pos)

            # Если это <li>, ищем </li>
            if content[tag_start:tag_start+3] == "<li":
                closing_tag = content.find("</li>", tag_end) + 5
            else:
                # Ищем закрывающий тег
                tag_name = content[tag_start+1:content.find(" ", tag_start)]
                if " " not in tag_name:
                    tag_name = content[tag_start+1:content.find(">", tag_start)]
                closing_tag = content.find(f"</{tag_name}>", tag_end) + len(f"</{tag_name}>")

            old_element = content[tag
