# routes_finance.py
from __future__ import annotations
from flask import Blueprint, current_app, render_template, request, redirect, url_for, flash, jsonify
from bson import ObjectId
from datetime import datetime

bp = Blueprint("finance", __name__, url_prefix="/finance")

def get_db():
    db = current_app.config.get("DB")
    if db is None:  # ← ВАЖНО: проверяем именно на None
        raise RuntimeError("DB not attached to app.config['DB']")
    return db

# -------------------------
# Страница списка операций
# -------------------------
@bp.get("")
def list_ops():
    db = get_db()

    # фильтры (пока простые)
    f_type   = (request.args.get("type")   or "").strip()  # income|expense|deposit|salary|purchase
    f_source = (request.args.get("source") or "").strip()  # alpha|sber|cash

    q = {}
    if f_type:
        q["type"] = f_type
    if f_source:
        q["source"] = f_source

    ops = list(db.finance_ops.find(q).sort("created_at", -1).limit(500))

    # для отображения подтянем имена услуг
    service_ids = [op.get("service_id") for op in ops if op.get("service_id")]
    svc_map = {}
    if service_ids:
        svc_map = { s["_id"]: s for s in db.services.find({"_id": {"$in": service_ids}}, {"name":1,"price":1}) }

    # базовые суммы
    income  = sum(int(op.get("amount", 0) or 0) for op in ops if op.get("type") in ("income",))
    expense = sum(int(op.get("amount", 0) or 0) for op in ops if op.get("type") in ("expense","salary","purchase"))

    # подготовим представление
    view = []
    for op in ops:
        svc = svc_map.get(op.get("service_id"))
        view.append({
            "id": str(op["_id"]),
            "ts": (op.get("created_at") or datetime.utcnow()).strftime("%Y-%m-%d %H:%M"),
            "type": op.get("type",""),
            "source": op.get("source",""),
            "amount": int(op.get("amount",0) or 0),
            "patient_id": str(op.get("patient_id") or "") or "",
            "service_name": (svc or {}).get("name",""),
            "note": op.get("note","")
        })

    return render_template(
        "finance/list.html",
        items=view,
        income=income,
        expense=expense,
        f_type=f_type,
        f_source=f_source
    )

# -------------------------
# Форма «Внести»
# -------------------------
@bp.get("/add")
def add_get():
    db = get_db()
    services = list(db.services.find({"is_active": True}, {"name":1,"price":1}).sort("name",1))
    # patients/ doctors можно добавить позже; сейчас фокус на услуге и источнике
    return render_template("finance/add.html", services=services)

@bp.post("/add")
def add_post():
    db = get_db()

    kind   = (request.form.get("type") or "").strip()          # income | expense | deposit | salary | purchase
    source = (request.form.get("source") or "").strip()        # alpha | sber | cash
    svc_id = (request.form.get("service_id") or "").strip()    # строго из справочника
    note   = (request.form.get("note") or "").strip()

    # ВАЖНО: жёсткая блокировка ручной цены — цену берём из services
    svc_oid = None
    if svc_id:
        try:
            svc_oid = ObjectId(svc_id)
        except Exception:
            svc_oid = None

    price = 0
    if svc_oid:
        svc = db.services.find_one({"_id": svc_oid}, {"price":1})
        price = int((svc or {}).get("price", 0) or 0)

    # Валидация
    errors = []
    if kind not in ("income","expense","deposit","salary","purchase"):
        errors.append("Некорректный тип операции.")
    if kind == "income" and not svc_oid:
        errors.append("Для дохода нужно выбрать услугу из прайса.")
    if kind in ("income","expense") and price <= 0:
        errors.append("Цена услуги не задана в прайсе.")

    if errors:
        for e in errors:
            flash(e, "danger")
        return redirect(url_for("finance.add_get"))

    doc = {
        "type": kind,
        "source": source or None,
        "service_id": svc_oid,
        "amount": price,                     # только из прайса!
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
    for s in db.services.find({"is_active": True}, {"name":1,"price":1}).sort("name",1):
        items.append({"id": str(s["_id"]), "name": s["name"], "price": int(s.get("price",0) or 0)})
    return jsonify({"ok": True, "items": items})

# -------------------------
# Отчёт: «Сколько денег в кассе»
# -------------------------
@bp.get("/report/cashbox")
def report_cashbox():
    db = get_db()
    income  = sum(int(x.get("amount",0) or 0) for x in db.finance_ops.find({"type":"income"}))
    deposit = sum(int(x.get("amount",0) or 0) for x in db.finance_ops.find({"type":"deposit"}))
    expense = sum(int(x.get("amount",0) or 0) for x in db.finance_ops.find({"type":{"$in":["expense","salary","purchase"]}}))

    # Источники поступлений
    by_source = {}
    for op in ops:
        if op.get("type") == "income":
            src = op.get("source") or "unknown"
            by_source[src] = by_source.get(src, 0) + int(op.get("amount",0) or 0)

    return render_template(
        "finance/list.html",
        items=[],
        income=income + deposit,
        expense=expense,
        by_source=by_source,
        f_type="",
        f_source=""
    )
