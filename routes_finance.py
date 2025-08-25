# routes_finance.py
from __future__ import annotations
from flask import Blueprint, current_app, render_template, request, redirect, url_for, flash, jsonify
from bson import ObjectId
from datetime import datetime

# Blueprint для финансов
bp = Blueprint("finance", __name__, url_prefix="/finance")


# Унифицированный доступ к БД (кладём PyMongo db в app.config["DB"])
def get_db():
    db = current_app.config.get("DB")
    if db is None:
        raise RuntimeError("DB not attached to app.config['DB']")
    return db


# -------------------------
# Список операций /finance
# -------------------------
@bp.get("")
def list_ops():
    db = get_db()

    # --- фильтры из querystring ---
    f_type     = (request.args.get("type") or "").strip()      # income|expense|deposit|salary|purchase
    f_source   = (request.args.get("source") or "").strip()    # alpha|sber|cash
    f_category = (request.args.get("category") or "").strip()  # purchase|rent|marketing|dividends

    # --- запрос к БД по фильтрам ---
    q = {}
    if f_type:
        q["type"] = f_type
    if f_source:
        q["source"] = f_source
    if f_category:
        q["category"] = f_category

    ops = list(db.finance_ops.find(q).sort("created_at", -1).limit(500))

    # --- имена услуг для отображения ---
    service_ids = [op.get("service_id") for op in ops if op.get("service_id")]
    svc_map = {}
    if service_ids:
        cur = db.services.find({"_id": {"$in": service_ids}}, {"name": 1, "price": 1})
        svc_map = {s["_id"]: s for s in cur}

    # --- сводные суммы по текущей выборке ---
    income  = sum(int(op.get("amount", 0) or 0) for op in ops if op.get("type") == "income")
    expense = sum(int(op.get("amount", 0) or 0) for op in ops if op.get("type") in ("expense", "salary", "purchase"))

    # --- карточка «Поступления по источникам» (всегда по всем доходам) ---
    by_source = {}
    for op in db.finance_ops.find({"type": "income"}):
        src = (op.get("source") or "unknown").lower()
        by_source[src] = by_source.get(src, 0) + int(op.get("amount", 0) or 0)

    # --- карточка «Расходы по категориям» (всегда по всем расходам) ---
    by_category = {}
    for op in db.finance_ops.find({"type": {"$in": ["expense", "purchase"]}}):
        cat = op.get("category") or "other"
        by_category[cat] = by_category.get(cat, 0) + int(op.get("amount", 0) or 0)

    # --- подготовка к шаблону ---
    view = []
    for op in ops:
        svc = svc_map.get(op.get("service_id"))
        view.append({
            "id": str(op["_id"]),
            "ts": (op.get("created_at") or datetime.utcnow()).strftime("%Y-%m-%d %H:%M"),
            "type": op.get("type", ""),
            "source": op.get("source", ""),
            "amount": int(op.get("amount", 0) or 0),
            "service_name": (svc or {}).get("name", ""),
            "category": op.get("category"),
            "note": op.get("note", "")
        })

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
    )

# -------------------------
# Форма «Внести» (GET)
# -------------------------
@bp.get("/add")
def add_get():
    db = get_db()
    services = list(
        db.services.find({"is_active": True}, {"name": 1, "price": 1}).sort("name", 1)
    )

    # пресеты из querystring (для быстрых ссылок)
    preset_type = (request.args.get("type") or "").strip()
    preset_category = (request.args.get("category") or "").strip()

    return render_template(
        "finance/add.html",
        services=services,
        preset_type=preset_type,
        preset_category=preset_category,
    )

# -------------------------
# Форма «Внести» (POST)
# -------------------------
@bp.post("/add")
def add_post():
    db = get_db()

    kind   = (request.form.get("type") or "").strip()      # income|expense|deposit|salary|purchase
    source = (request.form.get("source") or "").strip()    # alpha|sber|cash
    svc_id = (request.form.get("service_id") or "").strip()
    note   = (request.form.get("note") or "").strip()

    # категория приходит скрытым полем с формы add.html (быстрые ссылки её подставляют)
    form_category = (request.form.get("category") or "").strip()

    amount = 0
    svc_oid = None

    if kind == "income":
        # доход: сумма строго из прайса по выбранной услуге
        if svc_id:
            try:
                svc_oid = ObjectId(svc_id)
            except Exception:
                svc_oid = None
        if svc_oid:
            svc = db.services.find_one({"_id": svc_oid}, {"price": 1})
            amount = int((svc or {}).get("price", 0) or 0)
    else:
        # не доход: сумма вручную
        try:
            amount = int(request.form.get("amount", 0) or 0)
        except ValueError:
            amount = 0

    # базовая валидация
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

    # вычисляем итоговую категорию
    category = None
    if kind == "purchase":
        category = "purchase"
    elif kind == "expense":
        category = form_category or None  # (rent|marketing|dividends|...)

    # итоговый документ
    doc = {
        "type": kind,
        "source": source or None,
        "service_id": (svc_oid if kind == "income" else None),
        "amount": amount,
        "category": category,   # только для expense/purchase; для остальных — None
        "note": note,
        "created_at": datetime.utcnow(),
    }

    db.finance_ops.insert_one(doc)
    flash("Операция сохранена.", "success")
    return redirect(url_for("finance.list_ops"))

# -------------------------
# API: список услуг (для JS)
# -------------------------
@bp.get("/api/services")
def api_services():
    db = get_db()
    items = []
    for s in db.services.find({"is_active": True}, {"name": 1, "price": 1}).sort("name", 1):
        items.append({"id": str(s["_id"]), "name": s["name"], "price": int(s.get("price", 0) or 0)})
    return jsonify({"ok": True, "items": items})


# --------------------------------------
# Отчёт «Сколько денег в кассе» /cashbox
# --------------------------------------
@bp.get("/report/cashbox")
def report_cashbox():
    db = get_db()

    # Сводные суммы
    income  = sum(int(x.get("amount",0) or 0) for x in db.finance_ops.find({"type":"income"}))
    deposit = sum(int(x.get("amount",0) or 0) for x in db.finance_ops.find({"type":"deposit"}))
    expense = sum(int(x.get("amount",0) or 0) for x in db.finance_ops.find({"type":{"$in":["expense","salary","purchase"]}}))

    # Источники доходов (как у тебя)
    by_source = {}
    for op in db.finance_ops.find({"type":"income"}):
        src = (op.get("source") or "unknown").lower()
        by_source[src] = by_source.get(src, 0) + int(op.get("amount",0) or 0)

    # ⬇️ НОВОЕ: расходы по категориям
    by_category = {}
    for op in db.finance_ops.find({"type":{"$in":["expense","purchase"]}}):
        cat = op.get("category") or "other"
        by_category[cat] = by_category.get(cat, 0) + int(op.get("amount",0) or 0)

    return render_template(
        "finance/cashbox.html",
        income=income + deposit,
        expense=expense,
        by_source=by_source,
        by_category=by_category,
    )


