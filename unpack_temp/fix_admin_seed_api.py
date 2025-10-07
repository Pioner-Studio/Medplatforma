# fix_admin_seed_api.py
# Исправляем /api/admin/seed/dicts чтобы он тоже возвращал реальные данные

import re

# Читаем routes_admin_seed.py
with open("routes_admin_seed.py", "r", encoding="utf-8") as f:
    content = f.read()

# Найдем функцию dicts и убедимся, что она возвращает реальные данные
pattern = (
    r'@admin_seed_bp\.route\("/api/admin/seed/dicts".*?\ndef dicts\(\):.*?return jsonify\([^}]+}\)'
)

new_function = '''@admin_seed_bp.route("/api/admin/seed/dicts", methods=["GET"])
def dicts():
    """Возвращает справочники - используем те же данные что и основной API"""
    from main import db

    # Врачи
    doctors = []
    for doc in db.doctors.find({"status": "активен"}, {"full_name": 1, "specialization": 1}):
        doctors.append({
            "id": str(doc["_id"]),
            "name": doc.get("full_name", ""),
            "specialization": doc.get("specialization", "")
        })

    # Услуги - только активные
    services = []
    for srv in db.services.find({"is_active": True}, {"name": 1, "duration_min": 1, "price": 1}):
        services.append({
            "id": str(srv["_id"]),
            "name": srv.get("name", ""),
            "duration_min": int(srv.get("duration_min", 30)),
            "price": int(srv.get("price", 0))
        })

    # Пациенты
    patients = []
    for pat in db.patients.find({}, {"full_name": 1, "birthdate": 1}).limit(50):
        patients.append({
            "id": str(pat["_id"]),
            "name": pat.get("full_name", ""),
            "birthdate": pat.get("birthdate", "")
        })

    # Кабинеты - только активные
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
with open("routes_admin_seed.py", "w", encoding="utf-8") as f:
    f.write(content)

print("✅ Исправлен /api/admin/seed/dicts для синхронности с основным API!")
