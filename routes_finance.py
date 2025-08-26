# -*- coding: utf-8 -*-
from __future__ import annotations
from flask import (
    Blueprint,
    current_app,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    Response,
)
from bson import ObjectId
from datetime import datetime
import io, csv, json

bp = Blueprint("finance", __name__, url_prefix="/finance")


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
    f_type = (request.args.get("type") or "").strip()
    f_source = (request.args.get("source") or "").strip()
    f_category = (request.args.get("category") or "").strip()

    q = {}
    if f_type:
        q["type"] = f_type
    if f_source:
        q["source"] = f_source
    if f_category:
        q["category"] = f_category

    ops = list(db.finance_ops.find(q).sort("created_at", -1).limit(500))

    # Имена услуг
    service_ids = [op.get("service_id") for op in ops if op.get("service_id")]
    svc_map = {}
    if service_ids:
        svc_map = {
            s["_id"]: s
            for s in db.services.find({"_id": {"$in": service_ids}}, {"name": 1, "price": 1})
        }

    income = sum(int(op.get("amount", 0) or 0) for op in ops if op.get("type") == "income")
    expense = sum(
        int(op.get("amount", 0) or 0)
        for op in ops
        if op.get("type") in ("expense", "salary", "purchase")
    )

    # Карточка «Поступления по источникам» (все доходы)
    by_source = {}
    for op in db.finance_ops.find({"type": "income"}):
        src = (op.get("source") or "unknown").lower()
        by_source[src] = by_source.get(src, 0) + int(op.get("amount", 0) or 0)

    # Карточка «Расходы по категориям» (все расходы)
    by_category = {}
    for op in db.finance_ops.find({"type": {"$in": ["expense", "purchase"]}}):
        cat = op.get("category") or "other"
        by_category[cat] = by_category.get(cat, 0) + int(op.get("amount", 0) or 0)

    view = []
    for op in ops:
        svc = svc_map.get(op.get("service_id"))
        view.append(
            {
                "id": str(op["_id"]),
                "ts": (op.get("created_at") or datetime.utcnow()).strftime("%Y-%m-%d %H:%M"),
                "type": op.get("type", ""),
                "source": op.get("source", ""),
                "amount": int(op.get("amount", 0) or 0),
                "service_name": (svc or {}).get("name", ""),
                "category": op.get("category"),
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
    )


# -------------------------
# Форма «Внести»
# -------------------------
@bp.get("/add")
def add_get():
    db = get_db()
    services = list(db.services.find({"is_active": True}, {"name": 1, "price": 1}).sort("name", 1))
    preset_type = (request.args.get("type") or "").strip()
    preset_category = (request.args.get("category") or "").strip()
    return render_template(
        "finance/add.html",
        services=services,
        preset_type=preset_type,
        preset_category=preset_category,
    )


@bp.post("/add")
def add_post():
    db = get_db()
    kind = (request.form.get("type") or "").strip()
    source = (request.form.get("source") or "").strip()
    svc_id = (request.form.get("service_id") or "").strip()
    note = (request.form.get("note") or "").strip()

    amount = 0
    svc_oid = None

    if kind == "income":
        if svc_id:
            try:
                svc_oid = ObjectId(svc_id)
            except Exception:
                svc_oid = None
        if svc_oid:
            svc = db.services.find_one({"_id": svc_oid}, {"price": 1})
            amount = int((svc or {}).get("price", 0) or 0)
    else:
        try:
            amount = int(request.form.get("amount", 0) or 0)
        except ValueError:
            amount = 0

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

    # Категория для расходов/закупки
    category = None
    if kind == "purchase":
        category = "purchase"
    elif kind == "expense":
        category = (request.form.get("category") or "").strip() or None

    doc = {
        "type": kind,
        "source": source or None,
        "service_id": (svc_oid if kind == "income" else None),
        "amount": amount,
        "category": category,
        "note": note,
        "created_at": datetime.utcnow(),
    }
    db.finance_ops.insert_one(doc)
    flash("Операция сохранена.", "success")
    return redirect(url_for("finance.list_ops"))


# -------------------------
# Отчёт «Сколько денег в кассе»
# -------------------------
@bp.get("/report/cashbox")
def report_cashbox():
    db = get_db()

    income = sum(int(x.get("amount", 0) or 0) for x in db.finance_ops.find({"type": "income"}))
    deposit = sum(int(x.get("amount", 0) or 0) for x in db.finance_ops.find({"type": "deposit"}))
    expense = sum(
        int(x.get("amount", 0) or 0)
        for x in db.finance_ops.find({"type": {"$in": ["expense", "salary", "purchase"]}})
    )

    by_source = {}
    for op in db.finance_ops.find({"type": "income"}):
        src = (op.get("source") or "unknown").lower()
        by_source[src] = by_source.get(src, 0) + int(op.get("amount", 0) or 0)

    by_category = {}
    for op in db.finance_ops.find({"type": {"$in": ["expense", "purchase"]}}):
        cat = op.get("category") or "other"
        by_category[cat] = by_category.get(cat, 0) + int(op.get("amount", 0) or 0)

    return render_template(
        "finance/cashbox.html",
        income=income + deposit,
        expense=expense,
        by_source=by_source,
        by_category=by_category,
    )


# -------------------------
# Экспорт CSV/JSON
# -------------------------
def _query_from_args():
    f_type = (request.args.get("type") or "").strip()
    f_source = (request.args.get("source") or "").strip()
    f_category = (request.args.get("category") or "").strip()
    q = {}
    if f_type:
        q["type"] = f_type
    if f_source:
        q["source"] = f_source
    if f_category:
        q["category"] = f_category
    return q


@bp.get("/export/csv")
def export_csv():
    db = get_db()
    q = _query_from_args()
    rows = list(db.finance_ops.find(q).sort("created_at", -1))
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=";")
    w.writerow(["created_at", "type", "source", "amount", "category", "service_id", "note"])
    for r in rows:
        w.writerow(
            [
                (r.get("created_at") or datetime.utcnow()).strftime("%Y-%m-%d %H:%M"),
                r.get("type", ""),
                r.get("source", ""),
                int(r.get("amount", 0) or 0),
                r.get("category", ""),
                str(r.get("service_id") or ""),
                r.get("note", ""),
            ]
        )
    data = buf.getvalue().encode("utf-8-sig")  # BOM для Excel
    return Response(
        data,
        headers={
            "Content-Disposition": "attachment; filename=finance_export.csv",
            "Content-Type": "text/csv; charset=utf-8",
        },
    )


@bp.get("/export/json")
def export_json():
    db = get_db()
    q = _query_from_args()
    rows = list(db.finance_ops.find(q).sort("created_at", -1))
    for r in rows:
        r["_id"] = str(r["_id"])
        if r.get("service_id"):
            r["service_id"] = str(r["service_id"])
        if r.get("created_at"):
            r["created_at"] = r["created_at"].strftime("%Y-%m-%d %H:%M")
    return Response(
        json.dumps(rows, ensure_ascii=False, indent=2),
        headers={
            "Content-Disposition": "attachment; filename=finance_export.json",
            "Content-Type": "application/json; charset=utf-8",
        },
    )


# -------------------------
# Импорт JSON (массив объектов)
# -------------------------
@bp.post("/import/json")
def import_json():
    db = get_db()
    f = request.files.get("file")
    if not f:
        flash("Файл не выбран", "danger")
        return redirect(url_for("finance.list_ops"))
    try:
        payload = json.load(f.stream)
        added = 0
        for r in payload:
            doc = {
                "type": r.get("type"),
                "source": r.get("source"),
                "amount": int(r.get("amount", 0) or 0),
                "category": r.get("category") or None,
                "service_id": ObjectId(r["service_id"]) if r.get("service_id") else None,
                "note": r.get("note", ""),
                "created_at": (
                    datetime.strptime(r["created_at"], "%Y-%m-%d %H:%M")
                    if r.get("created_at")
                    else datetime.utcnow()
                ),
            }
            if (
                doc["type"] in ("income", "expense", "deposit", "salary", "purchase")
                and doc["amount"] > 0
            ):
                db.finance_ops.insert_one(doc)
                added += 1
        flash(f"Импортировано записей: {added}", "success")
    except Exception as e:
        flash(f"Ошибка импорта: {e}", "danger")
    return redirect(url_for("finance.list_ops"))
