# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify, current_app
from bson import ObjectId
from datetime import datetime

bp = Blueprint("bonus", __name__, url_prefix="/api/patients")


def get_db():
    return current_app.config.get("DB")


@bp.post("/<id>/bonus/add")
def add_bonus(id):
    """Начисление бонусов вручную"""
    db = get_db()
    data = request.get_json()
    amount = int(data.get("amount", 0))
    comment = data.get("comment", "Ручное начисление")

    if amount <= 0:
        return jsonify({"ok": False, "error": "Сумма должна быть больше 0"}), 400

    patient_oid = ObjectId(id)

    # Обновляем баланс
    db.patients.update_one(
        {"_id": patient_oid},
        {"$inc": {"bonus_balance": amount}, "$set": {"bonus_updated_at": datetime.utcnow()}},
    )

    # Записываем в историю
    db.bonus_history.insert_one(
        {
            "patient_id": patient_oid,
            "operation": "manual_accrual",
            "amount": amount,
            "comment": comment,
            "created_by": None,  # TODO: добавить текущего пользователя
            "ts": datetime.utcnow(),
        }
    )

    return jsonify({"ok": True})


@bp.post("/<id>/bonus/withdraw")
def withdraw_bonus(id):
    """Списание бонусов вручную"""
    db = get_db()
    data = request.get_json()
    amount = int(data.get("amount", 0))
    comment = data.get("comment", "Ручное списание")

    if amount <= 0:
        return jsonify({"ok": False, "error": "Сумма должна быть больше 0"}), 400

    patient_oid = ObjectId(id)
    patient = db.patients.find_one({"_id": patient_oid}, {"bonus_balance": 1})

    if not patient or patient.get("bonus_balance", 0) < amount:
        return jsonify({"ok": False, "error": "Недостаточно бонусов"}), 400

    # Обновляем баланс
    db.patients.update_one(
        {"_id": patient_oid},
        {"$inc": {"bonus_balance": -amount}, "$set": {"bonus_updated_at": datetime.utcnow()}},
    )

    # Записываем в историю
    db.bonus_history.insert_one(
        {
            "patient_id": patient_oid,
            "operation": "manual_withdrawal",
            "amount": -amount,
            "comment": comment,
            "created_by": None,
            "ts": datetime.utcnow(),
        }
    )

    return jsonify({"ok": True})


@bp.get("/<id>/bonus/history")
def bonus_history(id):
    """История бонусных операций"""
    db = get_db()
    patient_oid = ObjectId(id)

    history = list(db.bonus_history.find({"patient_id": patient_oid}).sort("ts", -1).limit(50))

    items = []
    for h in history:
        items.append(
            {
                "date": h["ts"].strftime("%d.%m.%Y %H:%M"),
                "amount": h.get("amount", 0),
                "comment": h.get("comment", ""),
            }
        )

    return jsonify({"items": items})
