# routes_admin_seed.py
from __future__ import annotations
from flask import Blueprint, current_app, jsonify

# Один блюпринт и читаем из БД
admin_seed_bp = Blueprint("admin_seed", __name__, url_prefix="/api/admin/seed")

def _get_db():
    db = current_app.config.get("DB")
    if db is None:
        raise RuntimeError("DB not attached to app.config['DB']")
    return db

@admin_seed_bp.get("/_routes")
def list_routes():
    return jsonify({
        "ok": True,
        "routes": ["GET /api/admin/seed/_routes", "GET /api/admin/seed/dicts"]
    })

@admin_seed_bp.get("/dicts")
def dicts():
    """
    Возвращает словари для календаря из MongoDB:
      - активные доктора
      - активные услуги
      - активные (или все, если нет поля) кабинеты
    """
    db = _get_db()

    # doctors
    doctors = []
    try:
        for d in db["doctors"].find({"active": True}, {
            "_id": 0, "id": 1, "name": 1, "full_name": 1, "phone": 1, "specialty": 1
        }):
            doctors.append({
                "id": d.get("id"),
                "name": d.get("name") or d.get("full_name"),
                "full_name": d.get("full_name") or d.get("name"),
                "phone": d.get("phone"),
                "specialty": d.get("specialty"),
                "active": True,
            })
    except Exception:
        doctors = []

    # rooms
    rooms = []
    try:
        cursor = db["rooms"].find({}, {"_id": 0, "id": 1, "name": 1, "active": 1})
        for r in cursor:
            if r.get("active") is False:
                continue
            rooms.append({
                "id": r.get("id") or r.get("name"),
                "name": r.get("name"),
                "active": r.get("active", True),
            })
    except Exception:
        rooms = []

    # services
    services = []
    try:
        for s in db["services"].find({"active": True}, {
            "_id": 0, "id": 1, "name": 1, "duration_min": 1, "price_client": 1
        }):
            services.append({
                "id": s.get("id"),
                "name": s.get("name"),
                "duration_min": s.get("duration_min"),
                "price_client": s.get("price_client"),
                "active": True,
            })
    except Exception:
        services = []

    return jsonify({"ok": True, "doctors": doctors, "rooms": rooms, "services": services})
