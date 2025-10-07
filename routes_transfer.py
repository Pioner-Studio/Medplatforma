from flask import Blueprint, render_template, request, flash, redirect, url_for
from datetime import datetime
from bson import ObjectId
from production_auth import login_required, role_required

# Создаём Blueprint
transfer_bp = Blueprint("transfer", __name__, url_prefix="/finance")

# Источники денег
SOURCES = {"alpha": "Альфа-Банк", "sber": "Сбербанк", "cash": "Наличные"}


@transfer_bp.route("/transfer", methods=["GET"])
@login_required
@role_required(["admin"])
def transfer_page():
    """Страница переводов между кассами"""
    from main import db
    from datetime import datetime

    # Получаем текущие балансы всех касс
    cashboxes = {}
    for source_id, source_name in SOURCES.items():
        cashbox = db.cashboxes.find_one({"_id": source_id})
        if cashbox:
            cashboxes[source_id] = {"name": source_name, "balance": cashbox.get("balance", 0)}
        else:
            cashboxes[source_id] = {"name": source_name, "balance": 0}

    return render_template(
        "finance/transfer.html",
        sources=SOURCES,
        cashboxes=cashboxes,
        today=datetime.now().strftime("%Y-%m-%d"),
    )


@transfer_bp.route("/transfer", methods=["POST"])
@login_required
@role_required(["admin"])
def transfer_execute():
    """Выполнение перевода между кассами"""
    from main import db, write_audit_log

    from_source = request.form.get("from_source", "").strip()
    to_source = request.form.get("to_source", "").strip()
    amount_str = request.form.get("amount", "").strip()
    comment = request.form.get("comment", "").strip()
    operation_date_str = request.form.get("operation_date", "").strip()

    # Валидация
    errors = []

    if not from_source or from_source not in SOURCES:
        errors.append("Выберите кассу-источник")

    if not to_source or to_source not in SOURCES:
        errors.append("Выберите кассу-назначение")

    if from_source == to_source:
        errors.append("Нельзя перевести деньги в ту же кассу")

    try:
        amount = float(amount_str)
        if amount <= 0:
            errors.append("Сумма должна быть больше 0")
    except (ValueError, TypeError):
        errors.append("Введите корректную сумму")
        amount = 0

    # Парсинг даты операции
    if operation_date_str:
        try:
            operation_date = datetime.strptime(operation_date_str, "%Y-%m-%d")
        except ValueError:
            errors.append("Некорректная дата операции")
            operation_date = datetime.utcnow()
    else:
        operation_date = datetime.utcnow()

    if errors:
        for error in errors:
            flash(error, "danger")
        return redirect(url_for("transfer.transfer_page"))

    # Проверка достаточности средств
    source_cashbox = db.cashboxes.find_one({"_id": from_source})
    if not source_cashbox or source_cashbox.get("balance", 0) < amount:
        flash(f"Недостаточно средств в кассе {SOURCES[from_source]}", "danger")
        return redirect(url_for("transfer.transfer_page"))

    # Создаём запись о переводе в ledger
    transfer_doc = {
        "kind": "transfer",
        "from_source": from_source,
        "to_source": to_source,
        "amount": amount,
        "comment": comment or f"Перевод {SOURCES[from_source]} → {SOURCES[to_source]}",
        "ts": operation_date,
        "created_at": datetime.utcnow(),
        "status": "completed",
    }

    # Сохраняем в ledger
    result = db.ledger.insert_one(transfer_doc)
    transfer_id = result.inserted_id

    # Обновляем балансы касс
    db.cashboxes.update_one(
        {"_id": from_source},
        {"$inc": {"balance": -amount}, "$set": {"updated_at": datetime.utcnow()}},
    )

    db.cashboxes.update_one(
        {"_id": to_source}, {"$inc": {"balance": amount}, "$set": {"updated_at": datetime.utcnow()}}
    )

    # Логируем в журнал действий
    write_audit_log(
        action="transfer_money",
        obj_type="cashbox",
        obj_id=str(transfer_id),
        comment=f"Перевод {amount}₽: {SOURCES[from_source]} → {SOURCES[to_source]}",
        details={
            "from": from_source,
            "to": to_source,
            "amount": amount,
            "date": operation_date.strftime("%Y-%m-%d"),
        },
    )

    flash(
        f"Перевод выполнен: {amount}₽ из {SOURCES[from_source]} в {SOURCES[to_source]}", "success"
    )
    return redirect(url_for("transfer.transfer_page"))


@transfer_bp.route("/transfer/history", methods=["GET"])
@login_required
@role_required(["admin"])
def transfer_history():
    """История переводов"""
    from main import db

    # Получаем все переводы
    transfers = list(db.ledger.find({"kind": "transfer"}).sort("ts", -1).limit(100))

    # Добавляем читаемые названия источников
    for t in transfers:
        t["from_source_name"] = SOURCES.get(t.get("from_source"), "Неизвестно")
        t["to_source_name"] = SOURCES.get(t.get("to_source"), "Неизвестно")

    return render_template("finance/transfer_history.html", transfers=transfers, sources=SOURCES)


@transfer_bp.route("/transfer/delete/<id>", methods=["POST"])
@login_required
@role_required(["admin"])
def transfer_delete(id):
    """Удаление перевода с откатом балансов"""
    from main import db, write_audit_log

    try:
        transfer = db.ledger.find_one({"_id": ObjectId(id), "kind": "transfer"})

        if not transfer:
            flash("Перевод не найден", "danger")
            return redirect(url_for("transfer.transfer_history"))

        # Откатываем балансы (обратная операция)
        from_source = transfer.get("from_source")
        to_source = transfer.get("to_source")
        amount = transfer.get("amount", 0)

        # Возвращаем деньги в источник
        db.cashboxes.update_one(
            {"_id": from_source},
            {"$inc": {"balance": amount}, "$set": {"updated_at": datetime.utcnow()}},
        )

        # Убираем деньги из назначения
        db.cashboxes.update_one(
            {"_id": to_source},
            {"$inc": {"balance": -amount}, "$set": {"updated_at": datetime.utcnow()}},
        )

        # Удаляем запись о переводе
        db.ledger.delete_one({"_id": ObjectId(id)})

        # Логируем удаление
        write_audit_log(
            action="delete_transfer",
            obj_type="cashbox",
            obj_id=str(id),
            comment=f"Удалён перевод {amount}₽: {SOURCES.get(from_source)} → {SOURCES.get(to_source)}",
            details={"from": from_source, "to": to_source, "amount": amount, "reversed": True},
        )

        flash(f"Перевод удалён, балансы восстановлены", "success")

    except Exception as e:
        flash(f"Ошибка при удалении: {str(e)}", "danger")

    return redirect(url_for("transfer.transfer_history"))
