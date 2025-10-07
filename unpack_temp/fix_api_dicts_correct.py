# fix_api_dicts_correct.py
import re

# Читаем main.py
with open("main.py", "r", encoding="utf-8") as f:
    content = f.read()

# Находим старую функцию api_dicts и заменяем её
pattern = r'@app\.route\("/api/dicts".*?\ndef api_dicts\(\):.*?return jsonify\([^}]+}\)'

new_function = '''@app.route("/api/dicts", methods=["GET"])
def api_dicts():
    """Возвращает справочники для фильтров календаря"""

    # Врачи из реальной БД
    doctors = []
    for doc in db.doctors.find({"status": "активен"}, {"full_name": 1, "specialization": 1}):
        doctors.append({
            "id": str(doc["_id"]),
            "name": doc.get("full_name", ""),
            "specialization": doc.get("specialization", "")
        })

    # Услуги из реальной БД - только активные
    services = []
    for srv in db.services.find({"is_active": True}, {"name": 1, "duration_min": 1, "price": 1}):
        services.append({
            "id": str(srv["_id"]),
            "name": srv.get("name", ""),
            "duration_min": int(srv.get("duration_min", 30)),
            "price": int(srv.get("price", 0))
        })

    # Пациенты из реальной БД
    patients = []
    for pat in db.patients.find({}, {"full_name": 1, "birthdate": 1}).limit(50):
        patients.append({
            "id": str(pat["_id"]),
            "name": pat.get("full_name", ""),
            "birthdate": pat.get("birthdate", "")
        })

    # Кабинеты из реальной БД - только активные
    rooms = []
    for room in db.rooms.find({"active": True}, {"name": 1}):
        rooms.append({
            "id": str(room["_id"]),
            "name": room.get("name", "")
        })

    return jsonify({
        "ok": True,
        "doctors": doctors,
        "services": services,
        "patients": patients,
        "rooms": rooms
    })'''

# Заменяем функцию
content = re.sub(pattern, new_function, content, flags=re.DOTALL)

# Сохраняем
with open("main.py", "w", encoding="utf-8") as f:
    f.write(content)

print("✅ Функция api_dicts исправлена для работы с реальными данными!")
