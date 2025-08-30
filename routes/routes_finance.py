# routes/routes_finance.py
from flask import Blueprint, jsonify, request
from pymongo import MongoClient
import os

bp_finance = Blueprint("finance", __name__)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)
db = client["medplatforma"]
services = db["services"]

# Получить все услуги
@bp_finance.route("/services", methods=["GET"])
def get_services():
    data = list(services.find({}, {"_id": 0}))
    return jsonify(data)

# Добавить услугу (только из прайса)
@bp_finance.route("/services", methods=["POST"])
def add_service():
    payload = request.json
    if not payload.get("code") or not payload.get("name") or not payload.get("price"):
        return jsonify({"error": "code, name и price обязательны"}), 400
    
    existing = services.find_one({"code": payload["code"]})
    if existing:
        return jsonify({"error": "Услуга с таким code уже есть"}), 400

    services.insert_one(payload)
    return jsonify({"status": "ok"})
