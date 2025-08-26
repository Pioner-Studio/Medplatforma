# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterable

from bson import ObjectId
from flask import (
    Blueprint,
    Response,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
    flash,
)
import json

# -----------------------------
#  Blueprint «Финансы»
# -----------------------------
bp = Blueprint("finance", __name__, url_prefix="/finance")

# Человеческие подписи категорий (RU)
CAT_LABELS = {
    "purchase": "Закупка",
    "rent": "Аренда",
    "marketing": "Маркетинг",
    "dividends": "Дивиденды",
}


# -----------------------------
#  Доступ к БД (PyMongo db в app.config["DB"])
# -----------------------------
def get_db():
    db = current_app.config.get("DB")
    if db is None:
        raise RuntimeError("DB not attached to app.config['DB']")
    return db


# ============================================================
#  Список операций: /finance  (таблица + фильтры)
# ============================================================
@bp.get("")
def list_ops():
    """
    Поддерживаемые query:
      ?type=income|expense|deposit|salary|purchase
      ?source=alpha|sber|cash
      ?category=purchase|rent|marketing|dividends
    """
    db = get_db()

    # --- фильтры из querystring ---
    f_type = (request.args.get("type") or "").strip()
    f_source = (request.args.get("source") or "").strip()
    f_category = (request.args.get("category") or "").strip()

    # --- запрос к БД ---
    q: Dict[str, Any] = {}
    if f_type:
        q["type"] = f_type
    if f_source:
        q["source"] = f_source
    if f_category:
        q["category"] = f_category

    # Сами операции
    ops = list(db.finance_ops.find(q).sort("created_at", -1).limit(500))

    # Подтягиваем имена услуг
    service_ids = [op.get("service_id") for op in ops if op.get("service_id")]
    svc_map: Dict[ObjectId, Dict[str, Any]] = {}
    if service_ids:
        svc_map = {
            s["_id"]: s
            for s in db.services.find({"_id": {"$in": service_ids}}, {"name": 1, "price": 1})
        }

    # Сводные суммы по текущей выборке
    income = sum(int(op.get("amount", 0) or 0) for op in ops if op.get("type") == "income")
    expense = sum(
        int(op.get("amount", 0) or 0)
        for op in ops
        if op.get("type") in ("expense", "salary", "purchase")
    )

    # Поступления по источникам — считаем по всей базе (как у нас в дизайне)
    by_source: Dict[str, int] = {}
    for op in db.finance_ops.find({"type": "income"}):
        src = (op.get("source") or "unknown").lower()
        by_source[src] = by_source.get(src, 0) + int(op.get("amount", 0) or 0)

    # Расходы по категориям — по всей базе
    by_category: Dict[str, int] = {}
    for op in db.finance_ops.find({"type": {"$in": ["expense", "purchase"]}}):
        cat = op.get("category") or "other"
        by_category[cat] = by_category.get(cat, 0) + int(op.get("amount", 0) or 0)

    # Подготовка для шаблона
    view = []
    for op in ops:
        svc = svc_map.get(op.get("service_id"))
        cat = op.get("category")
        view.append(
            {
                "id": str(op["_id"]),
                "ts": (op.get("created_at") or datetime.utcnow()).strftime("%Y-%m-%d %H:%M"),
                "type": op.get("type", ""),
                "source": op.get("source", ""),
                "amount": int(op.get("amount", 0) or 0),
                "service_name": (svc or {}).get("name", ""),
                "category": cat,
                "category_ru": CAT_LABELS.get(cat or "", "—") if cat else "—",
                "note": op.get("note", ""),
            }
        )

    return render_template(
        "finance/list.html",
        items=view,
        income=income,
        expense=expense,
        by_source=by_source,
        by_category=by_category,
        f_type=f_type,
        f_source=f_source,
        f_category=f_category,
        cat_labels=CAT_LABELS,
    )


# ============================================================
#  Форма «Внести» (GET): /finance/add
# ============================================================
@bp.get("/add")
def add_get():
    db = get_db()
    services = list(db.services.find({"is_active": True}, {"name": 1, "price": 1}).sort("name", 1))

    # пресеты из querystring (для быстрых ссылок)
    preset_type = (request.args.get("type") or "").strip()
    preset_category = (request.args.get("category") or "").strip()

    return render_template(
        "finance/add.html",
        services=services,
        preset_type=preset_type,
        preset_category=preset_category,
    )


# ============================================================
#  Форма «Внести» (POST): /finance/add
# ============================================================
@bp.post("/add")
def add_post():
    db = get_db()

    kind = (request.form.get("type") or "").strip()  # income|expense|deposit|salary|purchase
    source = (request.form.get("source") or "").strip()  # alpha|sber|cash
    svc_id = (request.form.get("service_id") or "").strip()
    note = (request.form.get("note") or "").strip()

    # Для expense категория прилетает из скрытого поля (быстрые ссылки)
    category_form = (request.form.get("category") or "").strip()

    amount = 0
    svc_oid = None

    if kind == "income":
        # Доход: только из прайса
        if svc_id:
            try:
                svc_oid = ObjectId(svc_id)
            except Exception:
                svc_oid = None
        if svc_oid:
            svc = db.services.find_one({"_id": svc_oid}, {"price": 1})
            amount = int((svc or {}).get("price", 0) or 0)
    else:
        # expense/purchase/deposit/salary — сумма вручную
        try:
            amount = int(request.form.get("amount", 0) or 0)
        except ValueError:
            amount = 0

    # Валидация
    errors = []
    if kind not in ("income", "expense", "deposit", "salary", "purchase"):
        errors.append("Некорректный тип операции.")
    if kind == "income" and not svc_oid:
        errors.append("Для дохода нужно выбрать услугу из прайса.")
    if amount <= 0:
        errors.append("Сумма должна быть больше 0.")

    if errors:
        for e in errors:
            flash(e, "danger")
        return redirect(url_for("finance.add_get"))

    # Категория расходов:
    #  - для purchase всегда "purchase"
    #  - для expense — берем из формы (быстрые ссылки)
    #  - для income/deposit/salary — категории нет
    category = None
    if kind == "purchase":
        category = "purchase"
    elif kind == "expense":
        category = category_form or None
    else:
        category = None

    # Документ к сохранению
    doc: Dict[str, Any] = {
        "type": kind,
        "source": source or None,
        "service_id": (svc_oid if kind == "income" else None),
        "amount": amount,
        "note": note,
        "created_at": datetime.utcnow(),
    }
    if category:
        doc["category"] = category

    db.finance_ops.insert_one(doc)

    flash("Операция сохранена.", "success")
    return redirect(url_for("finance.list_ops"))


# ============================================================
#  API: список услуг для JS: /finance/api/services
# ============================================================
@bp.get("/api/services")
def api_services():
    db = get_db()
    items = []
    for s in db.services.find({"is_active": True}, {"name": 1, "price": 1}).sort("name", 1):
        items.append({"id": str(s["_id"]), "name": s["name"], "price": int(s.get("price", 0) or 0)})
    return jsonify({"ok": True, "items": items})


# ============================================================
#  Отчёт «Касса»: /finance/report/cashbox
# ============================================================
@bp.get("/report/cashbox")
def report_cashbox():
    db = get_db()

    # Сводные суммы по всей базе
    income = sum(int(x.get("amount", 0) or 0) for x in db.finance_ops.find({"type": "income"}))
    deposit = sum(int(x.get("amount", 0) or 0) for x in db.finance_ops.find({"type": "deposit"}))
    expense = sum(
        int(x.get("amount", 0) or 0)
        for x in db.finance_ops.find({"type": {"$in": ["expense", "salary", "purchase"]}})
    )

    # Источники доходов
    by_source: Dict[str, int] = {}
    for op in db.finance_ops.find({"type": "income"}):
        src = (op.get("source") or "unknown").lower()
        by_source[src] = by_source.get(src, 0) + int(op.get("amount", 0) or 0)

    # Расходы по категориям
    by_category: Dict[str, int] = {}
    for op in db.finance_ops.find({"type": {"$in": ["expense", "purchase"]}}):
        cat = op.get("category") or "other"
        by_category[cat] = by_category.get(cat, 0) + int(op.get("amount", 0) or 0)

    return render_template(
        "finance/cashbox.html",
        income=income + deposit,  # как обсуждали, депозит плюсуем к доходам
        expense=expense,
        by_source=by_source,
        by_category=by_category,
        cat_labels=CAT_LABELS,
    )


# ============================================================
#  Экспорт / Импорт (резервные выгрузки)
# ============================================================


def _serialize(op: Dict[str, Any]) -> Dict[str, Any]:
    """Готовим документ к выгрузке (строки/ISO вместо ObjectId/дат)."""
    out = dict(op)
    out["_id"] = str(op.get("_id"))
    if op.get("service_id"):
        out["service_id"] = str(op.get("service_id"))
    dt = op.get("created_at")
    if isinstance(dt, datetime):
        out["created_at"] = dt.isoformat()
    return out


@bp.get("/export.json")
def export_json():
    """Выгрузка всех операций одним JSON-файлом (массив)."""
    db = get_db()
    ops = [_serialize(x) for x in db.finance_ops.find().sort("created_at", -1)]
    payload = json.dumps({"items": ops}, ensure_ascii=False)
    return Response(
        payload,
        mimetype="application/json; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="finance_export.json"'},
    )


@bp.get("/export.jsonl")
def export_jsonl():
    """Выгрузка JSON Lines (по одной записи в строке). Удобно для больших объёмов."""
    db = get_db()

    def generate() -> Iterable[bytes]:
        for x in db.finance_ops.find().sort("created_at", -1):
            yield (json.dumps(_serialize(x), ensure_ascii=False) + "\n").encode("utf-8")

    return Response(
        generate(),
        mimetype="application/x-ndjson; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="finance_export.jsonl"'},
    )


@bp.post("/import.jsonl")
def import_jsonl():
    """
    Импорт JSON Lines (каждая строка — валидный JSON).
    Безопасно: игнорируем _id, пытаемся распарсить created_at и service_id.
    """
    db = get_db()
    raw = request.get_data(as_text=True) or ""
    lines = [ln for ln in raw.splitlines() if ln.strip()]
    docs = []
    for ln in lines:
        try:
            obj = json.loads(ln)
        except Exception:
            continue
        obj.pop("_id", None)
        # service_id
        sid = obj.get("service_id")
        if sid:
            try:
                obj["service_id"] = ObjectId(sid)
            except Exception:
                obj["service_id"] = None
        # created_at
        ca = obj.get("created_at")
        if isinstance(ca, str):
            try:
                obj["created_at"] = datetime.fromisoformat(ca)
            except Exception:
                obj["created_at"] = datetime.utcnow()
        else:
            obj["created_at"] = datetime.utcnow()
        docs.append(obj)

    inserted = 0
    if docs:
        res = db.finance_ops.insert_many(docs)
        inserted = len(res.inserted_ids)

    return jsonify({"ok": True, "inserted": inserted, "lines": len(lines)})
