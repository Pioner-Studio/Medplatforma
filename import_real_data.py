# -*- coding: utf-8 -*-
"""
Robust CSV -> Mongo importer for medplatforma
Usage examples:
  python import_real_data.py --wipe --ensure-admin demo "ClubStom2024!"
  python import_real_data.py
"""

from __future__ import annotations
import os, sys, csv, argparse, re
from decimal import Decimal, InvalidOperation
from typing import List, Dict, Any, Iterable

from dotenv import load_dotenv
from pymongo import MongoClient, ASCENDING, UpdateOne
from pymongo.errors import OperationFailure
from werkzeug.security import generate_password_hash

# ---------- helpers ----------


def _truthy(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    s = str(v or "").strip().lower()
    return s in {"1", "true", "yes", "y", "on", "да", "истина", "active", "активен"}


def _money(v: Any) -> float | None:
    if v is None:
        return None
    s = str(v).strip().replace(" ", "").replace("\u00a0", "")
    if not s:
        return None
    s = s.replace(",", ".")
    s = re.sub(r"[^\d.\-]", "", s)
    if s == "" or s == "." or s == "-":
        return None
    try:
        return float(Decimal(s))
    except InvalidOperation:
        return None


def _norm(s: Any) -> str:
    return str(s or "").strip()


def read_csv(path: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        rdr = csv.DictReader(f)
        for row in rdr:
            # пропускаем полностью пустые строки
            if not row or all((v is None or str(v).strip() == "") for v in row.values()):
                continue
            clean: Dict[str, Any] = {}
            for k, v in row.items():
                if k is None:
                    continue
                k2 = k.strip()
                if isinstance(v, str):
                    v = v.strip()
                clean[k2] = v
            rows.append(clean)
    print(f"Read CSV: {os.path.basename(path)} -> {len(rows)} rows")
    return rows


def bulk_upsert(col, ops: Iterable[UpdateOne]) -> int:
    ops = list(ops)
    if not ops:
        return 0
    res = col.bulk_write(ops, ordered=False)
    return (res.upserted_count or 0) + (res.modified_count or 0)


# ---------- loaders ----------


def load_rooms(db, rows: List[Dict[str, Any]]) -> int:
    try:
        db.rooms.create_index([("name", ASCENDING)], unique=True, name="uniq_room_name")
    except OperationFailure:
        pass
    ops = []
    for r in rows:
        name = _norm(r.get("name"))
        if not name:
            continue
        doc = {
            "name": name,
            "active": _truthy(r.get("active", True)),
        }
        ops.append(UpdateOne({"name": name}, {"$set": doc}, upsert=True))
    n = bulk_upsert(db.rooms, ops)
    print(f"[rooms] imported: {n}")
    return n


def load_users(db, rows: List[Dict[str, Any]]) -> int:
    try:
        db.users.create_index([("login", ASCENDING)], unique=True, name="uniq_login")
    except OperationFailure:
        pass
    ops = []
    for r in rows:
        login = _norm(r.get("login"))
        if not login:
            continue
        full_name = _norm(r.get("full_name") or r.get("name"))
        role = _norm(r.get("role") or "admin").lower() or "admin"
        active = _truthy(r.get("active", True))
        phone = _norm(r.get("phone"))
        email = _norm(r.get("email"))

        pwd_hash = _norm(r.get("password_hash"))
        if not pwd_hash:
            plain = _norm(r.get("password"))
            pwd_hash = generate_password_hash(plain) if plain else None

        doc = {
            "login": login,
            "full_name": full_name or login,
            "role": role,
            "active": active,
            "phone": phone or None,
            "email": email or None,
        }
        if pwd_hash:
            doc["password_hash"] = pwd_hash

        ops.append(UpdateOne({"login": login}, {"$set": doc}, upsert=True))
    n = bulk_upsert(db.users, ops)
    print(f"[users] imported: {n}")
    return n


def load_doctors(db, rows: List[Dict[str, Any]]) -> int:
    try:
        db.doctors.create_index(
            [("full_name", ASCENDING), ("phone", ASCENDING)],
            unique=True,
            name="uniq_doc_name_phone",
        )
    except OperationFailure:
        pass
    ops = []
    for r in rows:
        full_name = _norm(r.get("full_name") or r.get("name"))
        if not full_name:
            continue
        phone = _norm(r.get("phone"))
        specialty = _norm(r.get("specialty"))
        active = _truthy(r.get("active", True))
        doc = {
            "full_name": full_name,
            "phone": phone or None,
            "specialty": specialty or None,
            "active": active,
        }
        ops.append(
            UpdateOne({"full_name": full_name, "phone": phone or None}, {"$set": doc}, upsert=True)
        )
    n = bulk_upsert(db.doctors, ops)
    print(f"[doctors] imported: {n}")
    return n


def load_services(db, rows: List[Dict[str, Any]]) -> int:
    try:
        db.services.create_index([("code", ASCENDING)], unique=True, name="uniq_service_code")
    except OperationFailure:
        pass
    ops = []
    for r in rows:
        code = _norm(r.get("code")) or None
        name = _norm(r.get("name"))
        if not (code or name):
            continue
        price1 = _money(r.get("price") or r.get("price1"))
        price2 = _money(r.get("price2"))
        active = _truthy(r.get("active", True))
        doc = {
            "code": code,
            "name": name,
            "price": price1,
            "price2": price2,
            "active": active,
        }
        key = {"code": code} if code else {"name": name}
        ops.append(UpdateOne(key, {"$set": doc}, upsert=True))
    n = bulk_upsert(db.services, ops)
    print(f"[services] imported: {n}")
    return n


# ---------- main ----------


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--wipe", action="store_true", help="drop rooms/users/doctors/services before import"
    )
    ap.add_argument("--rooms", default="rooms.csv")
    ap.add_argument("--users", default="users.csv")
    ap.add_argument("--doctors", default="doctors.csv")
    ap.add_argument("--services", default="services_price_dual.csv")
    ap.add_argument(
        "--ensure-admin",
        nargs=2,
        metavar=("LOGIN", "PASSWORD"),
        help="create/update admin with given password",
    )
    args = ap.parse_args()

    load_dotenv()
    client = MongoClient(os.getenv("MONGO_URI"))
    db = client[os.getenv("DB_NAME", "medplatforma")]

    if args.wipe:
        for c in ("rooms", "users", "doctors", "services"):
            try:
                db.drop_collection(c)
            except Exception:
                pass
        print("[wipe] collections dropped: rooms, users, doctors, services")

    total = {"rooms": 0, "users": 0, "doctors": 0, "services": 0}

    if os.path.exists(args.rooms):
        total["rooms"] = load_rooms(db, read_csv(args.rooms))
    if os.path.exists(args.users):
        total["users"] = load_users(db, read_csv(args.users))
    if os.path.exists(args.doctors):
        total["doctors"] = load_doctors(db, read_csv(args.doctors))
    if os.path.exists(args.services):
        total["services"] = load_services(db, read_csv(args.services))

    if args.ensure_admin:
        login, password = args.ensure_admin
        h = generate_password_hash(password)
        db.users.update_one(
            {"login": login},
            {
                "$set": {
                    "login": login,
                    "full_name": "Администратор",
                    "role": "admin",
                    "active": True,
                    "password_hash": h,
                }
            },
            upsert=True,
        )
        print(f"[admin] ensured: {login}")

    print("----- DONE -----")
    for k, v in total.items():
        print(f"{k:<8}: {v}")


if __name__ == "__main__":
    main()
