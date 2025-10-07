# fix_calendar_view.py
import re

# Читаем main.py
with open("main.py", "r", encoding="utf-8") as f:
    content = f.read()

# Ищем и заменяем функцию calendar_view
pattern = r'@app\.route\("/calendar"\)\s*@login_required\s*def calendar_view\(\):.*?return render_template\([^)]+\)'

new_function = """@app.route("/calendar")
@login_required
def calendar_view():
    # Получаем реальные данные из БД для шаблона
    doctors = list(db.doctors.find({"status": "активен"}))
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
        services=services,  # ← ДОБАВИЛИ УСЛУГИ!
    )"""

# Заменяем функцию
content = re.sub(pattern, new_function, content, flags=re.DOTALL)

# Сохраняем
with open("main.py", "w", encoding="utf-8") as f:
    f.write(content)

print("✅ Функция calendar_view исправлена - добавлены услуги!")
