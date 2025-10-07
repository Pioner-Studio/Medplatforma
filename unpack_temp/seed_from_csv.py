# -*- coding: utf-8 -*-
"""
Сидер словарей для ClubStom.
Читает CSV (services/doctors/rooms/users), нормализует, генерирует id,
и сохраняет:
  - по умолчанию -> ./data/dicts.json  (filesystem mode)
  - если заданы переменные окружения MONGO_URL/MONGO_DB -> апсертит в MongoDB

CSV ожидаются в ./seed/
  - services_price_dual.csv  (id?, name, duration_min, price_client, price_staff, active)
  - doctors.csv              (id?, full_name, specialty, phone, email, telegram, active)
  - rooms.csv                (id?, name, active)
  - users.csv                (login, full_name, role, doctor_id?, phone, password?, active)

Запуск:
  python seed_from_csv.py                 # запись ./data/dicts.json
  MONGO_URL="mongodb://localhost:27017" MONGO_DB="clubstom" python seed_from_csv.py

Зависимости: только стандартная библиотека (для файлов/JSON/UUID). Mongo-режим включается, если установлен pymongo.
"""

from __future__ import annotations
import csv, json, os, re, sys, uuid
from pathlib import Path
from typing import Dict, Any, List

# ---- Настройки путей ----
ROOT = Path(__file__).resolve().parent
SEED_DIR = ROOT / "seed"
OUT_DIR = ROOT / "data"
OUT_DIR.mkdir(exist_ok=True)
OUT_JSON = OUT_DIR / "dicts.json"


# ---- Утилиты ----
def norm_bool(v: Any, default=True) -> bool:
    s = str(v).strip().lower()
    if s in {"1", "true", "yes", "y", "да", "истина", "on"}:
        return True
    if s in {"0", "false", "no", "n", "нет", "ложь", "off"}:
        return False
    return default


def ensure_id(seed: str) -> str:
    """Детерминированный UUID5 по строке (чтобы id не прыгали)."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, seed))


def to_int(v: Any, default: int | None = None) -> int | None:
    try:
        return int(float(str(v).strip()))
    except Exception:
        return default


_phone_digits = re.compile(r"\D+")


def norm_phone_ru(v: str | None) -> str | None:
    if not v:
        return None
    digits = _phone_digits.sub("", v)
    # оставляем последние 10 цифр и префикс +7
    if len(digits) >= 10:
        last10 = digits[-10:]
        return f"+7{last10}"
    return f"+7{digits}" if digits else None


def read_csv(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(
                {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
            )
    return rows


# ---- Чтение CSV ----
services_raw = read_csv(SEED_DIR / "services_price_dual.csv")
doctors_raw = read_csv(SEED_DIR / "doctors.csv")
rooms_raw = read_csv(SEED_DIR / "rooms.csv")
users_raw = read_csv(SEED_DIR / "users.csv")

if not any([services_raw, doctors_raw, rooms_raw, users_raw]):
    print(f"[ERROR] В папке {SEED_DIR} не найдено CSV. Положи туда файлы и запусти снова.")
    sys.exit(2)

# ---- Нормализация ----
services: List[Dict[str, Any]] = []
for s in services_raw:
    name = s.get("name") or s.get("Name") or s.get("service") or ""
    if not name:
        continue
    sid = s.get("id") or ensure_id(f"service:{name}")
    services.append(
        {
            "id": sid,
            "name": name,
            "duration_min": to_int(s.get("duration_min") or s.get("duration") or 60, 60),
            "price_client": to_int(
                s.get("price_client") or s.get("price") or s.get("client_price")
            ),
            "price_staff": to_int(s.get("price_staff") or s.get("staff_price")),
            "active": norm_bool(s.get("active", "1")),
        }
    )

doctors: List[Dict[str, Any]] = []
for d in doctors_raw:
    full = d.get("full_name") or d.get("name") or ""
    if not full:
        continue
    did = d.get("id") or ensure_id(f"doctor:{full}")
    doctors.append(
        {
            "id": did,
            "full_name": full,
            "name": full,
            "specialty": d.get("specialty") or d.get("role"),
            "phone": norm_phone_ru(d.get("phone")),
            "email": (d.get("email") or "").strip() or None,
            "telegram": (d.get("telegram") or "").strip() or None,
            "active": norm_bool(d.get("active", "1")),
        }
    )

rooms: List[Dict[str, Any]] = []
for r in rooms_raw:
    name = r.get("name") or r.get("room") or ""
    if not name:
        continue
    rid = r.get("id") or ensure_id(f"room:{name}")
    rooms.append(
        {
            "id": rid,
            "name": name,
            "active": norm_bool(r.get("active", "1")),
        }
    )

users: List[Dict[str, Any]] = []
for u in users_raw:
    login = u.get("login") or u.get("username")
    full = u.get("full_name") or u.get("name")
    if not login or not full:
        continue
    role = (u.get("role") or "").lower().strip() or "user"  # admin/doctor/registrar
    did = u.get("doctor_id") or u.get("doctorId") or ""
    # пароли здесь не хешируем специально — это сид-данные; при авторизации задействуется ваша логика
    users.append(
        {
            "login": login,
            "full_name": full,
            "role": role,
            "doctor_id": did or None,
            "phone": norm_phone_ru(u.get("phone")),
            "password": u.get("password") or u.get("pass") or None,
            "active": norm_bool(u.get("active", "1")),
        }
    )

# ---- Вывод статистики ----
print("[OK] Прочитано из CSV:")
print(f"  services: {len(services)}")
print(f"  doctors : {len(doctors)}")
print(f"  rooms   : {len(rooms)}")
print(f"  users   : {len(users)}")

payload = {
    "ok": True,
    "loaded_at": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
    "source_dir": str(SEED_DIR),
    "services": services,
    "doctors": doctors,
    "rooms": rooms,
    "users": users,
}

# ---- Режим FS (по умолчанию) ----
mongo_url = os.getenv("MONGO_URL")
mongo_db = os.getenv("MONGO_DB")

if not mongo_url or not mongo_db:
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] dicts.json записан: {OUT_JSON}")
    sys.exit(0)

# ---- Режим MongoDB (если заданы переменные окружения) ----
try:
    from pymongo import MongoClient, ReplaceOne  # type: ignore
except Exception as e:
    print("[ERROR] pymongo не установлен. Установи: pip install pymongo")
    sys.exit(3)

client = MongoClient(mongo_url)
db = client[mongo_db]


def upsert_list(coll_name: str, items: List[Dict[str, Any]], key: str):
    coll = db[coll_name]
    ops = []
    for it in items:
        if key not in it or not it[key]:
            # генерим id на лету, чтобы апсерт прошёл
            it[key] = ensure_id(f"{coll_name}:{json.dumps(it, ensure_ascii=False, sort_keys=True)}")
        ops.append(ReplaceOne({key: it[key]}, it, upsert=True))
    if ops:
        result = coll.bulk_write(ops, ordered=False)
        return result.upserted_count, result.modified_count
    return 0, 0


ups, mods = upsert_list("services", services, "id")
print(f"[Mongo] services upserted={ups} modified={mods}")
ups, mods = upsert_list("doctors", doctors, "id")
print(f"[Mongo] doctors  upserted={ups} modified={mods}")
ups, mods = upsert_list("rooms", rooms, "id")
print(f"[Mongo] rooms    upserted={ups} modified={mods}")
ups, mods = upsert_list("users", users, "login")  # users — ключ по login
print(f"[Mongo] users    upserted={ups} modified={mods}")

print("[OK] Готово.")
