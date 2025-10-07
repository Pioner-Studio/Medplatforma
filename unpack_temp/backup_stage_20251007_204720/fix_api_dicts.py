# fix_api_dicts.py
import re

# Читаем main.py
with open("main.py", "r", encoding="utf-8") as f:
    content = f.read()

# Находим старую функцию api_dicts
old_pattern = r'@app\.route\("/api/dicts".*?\n(?:.*?\n)*?return jsonify\([^)]+\)'

# Новая функция
new_function = """@app.route("/api/dicts", methods=["GET"])
def api_dicts():
    # Врачи из БД
    doctors = []
    for doc in db.doctors.find({}, {"full_name": 1}):
        doctors.append({"id": str(doc["_id"]), "name": doc.get("full_name", "")})

    # Услуги из БД
    services = []
    for srv in db.services.find({"is_active": True}, {"name": 1, "duration_min": 1, "price": 1}):
        services.append({
            "id": str(srv["_id"]),
            "name": srv.get("name", ""),
            "duration_min": srv.get("duration_min", 30),
            "price": srv.get("price", 0)
        })

    # Пациенты из БД
    patients = []
    for pat in db.patients.find({}, {"full_name": 1, "birthdate": 1}):
        patients.append({
            "id": str(pat["_id"]),
            "name": pat.get("full_name", ""),
            "birthdate": pat.get("birthdate", "")
        })

    # Кабинеты из БД
    rooms = []
    for room in db.rooms.find({}, {"name": 1}):
        rooms.append({"id": str(room["_id"]), "name": room.get("name", "")})

    return jsonify({
        "ok": True,
        "doctors": doctors,
        "services": services,
        "patients": patients,
        "rooms": rooms
    })"""

# Заменяем
content = re.sub(old_pattern, new_function, content, flags=re.DOTALL)

# Сохраняем обратно
with open("main.py", "w", encoding="utf-8") as f:
    f.write(content)

print("✅ Функция api_dicts исправлена!")
