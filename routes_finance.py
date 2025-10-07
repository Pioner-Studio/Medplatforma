from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    session,
    current_app,
)
from bson import ObjectId
from datetime import datetime
from production_auth import login_required, role_required
import io, csv, json

bp = Blueprint("finance", __name__, url_prefix="/finance")


def get_db():
    db = current_app.config.get("DB")
    if db is None:
        raise RuntimeError("DB not attached to app.config['DB']")
    return db


def update_cashbox_balance(db, source, amount, operation_type):
    """Обновляет баланс кассы при финансовой операции"""
    if not source or source not in ["alpha", "sber", "cash"]:
        return

    if operation_type in ["income", "deposit"]:
        db.cashboxes.update_one(
            {"_id": source},
            {"$inc": {"balance": amount}, "$set": {"updated_at": datetime.utcnow()}},
            upsert=True,
        )
    elif operation_type in ["expense", "purchase", "salary"]:
        db.cashboxes.update_one(
            {"_id": source},
            {"$inc": {"balance": -amount}, "$set": {"updated_at": datetime.utcnow()}},
            upsert=True,
        )


def format_source(op):
    """Форматирует источник для отображения"""
    source = op.get("source") or ""

    # Если комбинированная оплата
    if source == "split" and op.get("split_payments"):
        parts = []
        for split in op["split_payments"]:
            src_name = split["source"].upper()
            amt = split["amount"]
            parts.append(f"{src_name} ({amt}₽)")
        return " + ".join(parts)

    # Если оплата с бонусами
    if source == "mixed" and op.get("bonus_amount"):
        main_source = op.get("main_source", "unknown").upper()
        # Русские названия касс
        source_names = {
            "alpha": "Альфа-Банк",
            "sber": "Сбербанк",
            "cash": "Наличные",
            "split": "Комбинированная",
            "mixed": "Смешанная",
        }
        main_source_ru = source_names.get(main_source, main_source or "НЕИЗВЕСТНО")

        main_amount = int(op.get("amount", 0))
        bonus_amount = op.get("bonus_amount", 0)
        return f"{main_source_ru} ({main_amount}₽) + БОНУСЫ ({bonus_amount}₽)"

    return source.upper()


@bp.get("")
def list_ops():
    db = get_db()
    f_type = (request.args.get("type") or "").strip()
    f_source = (request.args.get("source") or "").strip()
    f_category = (request.args.get("category") or "").strip()

    q = {}
    if f_type:
        q["kind"] = f_type
    if f_source:
        q["source"] = f_source
    if f_category:
        q["category"] = f_category

    if not q:
        q["kind"] = {"$in": ["income", "expense", "deposit", "salary", "purchase"]}
    ops = list(db.ledger.find(q).sort("ts", -1).limit(500))

    # Имена услуг
    service_ids = [op.get("service_id") for op in ops if op.get("service_id")]
    svc_map = {}
    if service_ids:
        svc_map = {
            s["_id"]: s
            for s in db.services.find({"_id": {"$in": service_ids}}, {"name": 1, "price": 1})
        }

    income = sum(int(op.get("amount", 0) or 0) for op in ops if op.get("kind") == "income")
    expense = sum(
        int(op.get("amount", 0) or 0)
        for op in ops
        if op.get("kind") in ("expense", "salary", "purchase")
    )
    # Должники
    debtors = list(db.patients.find({"debt_balance": {"$gt": 0}}, {"debt_balance": 1}))
    debtors_count = len(debtors)
    debtors_sum = sum(p.get("debt_balance", 0) for p in debtors)

    by_source = {}
    for op in db.ledger.find({"kind": "income"}):
        src = (op.get("source") or "unknown").lower()
        by_source[src] = by_source.get(src, 0) + int(op.get("amount", 0) or 0)

    by_category = {}
    for op in db.ledger.find({"kind": {"$in": ["expense", "purchase"]}}):
        cat = op.get("category") or "other"
        by_category[cat] = by_category.get(cat, 0) + int(op.get("amount", 0) or 0)

    CASHIERS = {
        "68ceefb500a8dfe76f6f32b1": "Гогуева А.Т.",
        "68ceefb500a8dfe76f6f32b3": "Наконечная Е.И.",
        "68ceefb500a8dfe76f6f32b2": "Наконечный А.В.",
    }

    view = []
    for op in ops:
        svc = svc_map.get(op.get("service_id"))
        cashier_id = str(op.get("cashier_id", "")) if op.get("cashier_id") else ""
        view.append(
            {
                "id": str(op["_id"]),
                "ts": (op.get("ts") or datetime.utcnow()).strftime("%Y-%m-%d %H:%M"),
                "type": {
                    "income": "Доход",
                    "expense": "Расход",
                    "deposit": "Депозит",
                    "salary": "ЗП",
                    "purchase": "Закупка",
                    "service_charge": "Услуга",
                    "other": "Другие расходы",
                }.get(op.get("kind", ""), op.get("kind", "")),
                "source": format_source(op),
                "amount": int(op.get("amount", 0) or 0),
                "service_name": (svc or {}).get("name", ""),
                "category": op.get("category"),
                "note": op.get("note", ""),
                "cashier": CASHIERS.get(cashier_id, "—"),
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
        debtors_count=debtors_count,
        debtors_sum=debtors_sum,
    )


@bp.route("/add", methods=["GET"])
@login_required
@role_required(["admin", "owner"])
def add_get():
    # Очищаем старые flash-сообщения
    session.pop("_flashes", None)
    from datetime import date

    db = get_db()

    # Получаем текущего пользователя
    current_user = session.get("user", {})
    current_user_id = None

    if current_user.get("username"):
        user_doc = db.users.find_one({"username": current_user["username"]})
        if user_doc:
            current_user_id = str(user_doc["_id"])

    # Читаем appointment_id из query параметров
    appointment_id = request.args.get("appointment_id")
    appointment_data = None

    if appointment_id:
        try:
            appt = db.appointments.find_one({"_id": ObjectId(appointment_id)})
            if appt:
                # Загружаем связанные данные
                patient = (
                    db.patients.find_one({"_id": appt.get("patient_id")})
                    if appt.get("patient_id")
                    else None
                )
                service = (
                    db.services.find_one({"_id": appt.get("service_id")})
                    if appt.get("service_id")
                    else None
                )

                appointment_data = {
                    "patient_id": str(appt.get("patient_id", "")),
                    "patient_name": patient.get("full_name", "") if patient else "",
                    "service_id": str(appt.get("service_id", "")),
                    "service_name": service.get("name", "") if service else "",
                    "amount": service.get("price", 0) if service else 0,
                }
        except:
            pass

    services = list(db.services.find({"is_active": True}, {"name": 1, "price": 1}))
    patients = list(db.patients.find({}, {"full_name": 1, "card_no": 1}))

    # Загружаем список администраторов для выбора кассира
    admins = list(
        db.users.find({"role": {"$in": ["admin", "registrar"]}}, {"full_name": 1, "_id": 1})
    )

    return render_template(
        "finance/add.html",
        services=services,
        patients=patients,
        admins=admins,
        today=date.today().strftime("%Y-%m-%d"),
        appointment_data=appointment_data,
        current_cashier_id=current_user_id,
    )


@bp.route("/add", methods=["POST"])
@login_required
@role_required(["admin", "registrar"])
def add_post():
    db = get_db()
    kind = (request.form.get("type") or "").strip()
    source = (request.form.get("source") or "").strip()
    svc_id = (request.form.get("service_id") or "").strip()
    note = (request.form.get("comment") or "").strip()
    cashier_id_str = (request.form.get("cashier_id") or "").strip()
    patient_id_str = (request.form.get("patient_id") or "").strip()
    operation_date_str = (request.form.get("operation_date") or "").strip()

    print(f"DEBUG: cashier_id_str = '{cashier_id_str}'")
    print(f"DEBUG: form data = {dict(request.form)}")

    amount = 0
    svc_oid = None
    svc_name = None
    cashier_oid = None
    original_amount = 0

    # Инициализация кассира
    if cashier_id_str:
        try:
            cashier_oid = ObjectId(cashier_id_str)
        except:
            cashier_oid = None

    if kind == "income":
        if svc_id:
            try:
                svc_oid = ObjectId(svc_id)
            except:
                svc_oid = None

            svc = db.services.find_one(
                {"_id": svc_oid, "is_active": True}, {"name": 1, "price": 1, "employee_price": 1}
            )

            use_preferential = False
            if patient_id_str:
                try:
                    patient = db.patients.find_one(
                        {"_id": ObjectId(patient_id_str)}, {"use_preferential_pricing": 1}
                    )
                    use_preferential = (
                        patient.get("use_preferential_pricing", False) if patient else False
                    )
                except:
                    use_preferential = False

            if use_preferential and svc.get("employee_price"):
                amount = int(svc.get("employee_price", 0) or 0)
                original_amount = amount
                print(f"DEBUG: original_amount set to {original_amount} (from price)")
            else:
                amount = int(svc.get("price", 0) or 0)
                original_amount = amount
                print(f"DEBUG: original_amount set to {original_amount} (from price)")

            # Берем сумму из формы, если введена, иначе из прайса
            manual_amount = request.form.get("amount", "").strip()

            if manual_amount:
                amount = int(manual_amount)

            svc_name = (svc or {}).get("name", "")
    else:
        try:
            amount = int(request.form.get("amount", 0) or 0)
        except:
            amount = 0

    # ВАЛИДАЦИЯ
    errors = []
    if kind not in ("income", "expense", "deposit", "salary", "purchase"):
        errors.append("Некорректный тип операции.")
    if kind == "income" and not svc_oid:
        errors.append("Для дохода нужно выбрать услугу из прайса.")
    if amount <= 0:
        errors.append("Сумма должна быть больше 0.")
    print(f"DEBUG: cashier_oid = {cashier_oid}")
    print(f"DEBUG: errors before cashier check = {errors}")
    if not cashier_oid:
        errors.append("Обязательно выберите кассира.")
    # Для комбинированной оплаты источник не обязателен
    if kind == "income" and not source and not request.form.get("split_source_1"):
        errors.append("Обязательно выберите источник поступления.")

    print(f"DEBUG: Final errors list = {errors}")
    print(f"DEBUG: len(errors) = {len(errors)}")

    # ОБРАБОТКА ОШИБОК С СОХРАНЕНИЕМ ФОРМЫ
    if errors:
        # Очищаем старые flash сообщения
        session.pop("_flashes", None)
        for e in errors:
            flash(e, "danger")
        from datetime import date

        # Загружаем данные для формы
        services = list(db.services.find({"is_active": True}, {"name": 1, "price": 1}))
        patients = list(db.patients.find({}, {"full_name": 1, "card_no": 1}))

        return render_template(
            "finance/add.html",
            services=services,
            patients=patients,
            today=date.today().strftime("%Y-%m-%d"),
            # Сохраняем данные формы при ошибке
            selected_patient_id=patient_id_str,
            selected_service_id=svc_id,
            selected_cashier_id=cashier_id_str,
            selected_source=source,
            form_note=note,
            form_amount=request.form.get("amount", ""),
            form_bonus_amount=request.form.get("bonus_amount", ""),
            form_operation_date=request.form.get("operation_date", ""),
            form_type=request.form.get("type", "income"),
        )

    # ОБРАБОТКА БОНУСНОЙ ОПЛАТЫ
    use_bonus = (
        request.form.get("use_bonus") == "on" or int(request.form.get("bonus_amount", 0) or 0) > 0
    )
    bonus_amount = 0

    if use_bonus and patient_id_str and kind == "income":
        try:
            bonus_amount = int(request.form.get("bonus_amount", 0) or 0)
            if bonus_amount > 0:
                # Проверяем баланс пациента
                patient = db.patients.find_one(
                    {"_id": ObjectId(patient_id_str)}, {"bonus_balance": 1}
                )
                patient_bonus_balance = patient.get("bonus_balance", 0) if patient else 0

                if bonus_amount > patient_bonus_balance:
                    errors.append(f"Недостаточно бонусов. У пациента: {patient_bonus_balance}₽")

                if bonus_amount > amount:
                    errors.append(f"Бонусы не могут превышать стоимость услуги: {amount}₽")

                # Уменьшаем основную сумму на размер бонусов
                amount = amount - bonus_amount

        except ValueError:
            bonus_amount = 0

    # Проверка суммы после вычета бонусов
    if amount < 0:
        errors.append("Сумма оплаты не может быть отрицательной после вычета бонусов")

    if errors:
        # Показываем ошибки (повторяем логику из строк 313-337)
        session.pop("_flashes", None)
        for e in errors:
            flash(e, "danger")
        from datetime import date

        services = list(db.services.find({"is_active": True}, {"name": 1, "price": 1}))
        patients = list(db.patients.find({}, {"full_name": 1, "card_no": 1}))
        return render_template(
            "finance/add.html",
            services=services,
            patients=patients,
            today=date.today().strftime("%Y-%m-%d"),
        )

    # Определение категории
    category = None
    if kind == "purchase":
        category = "purchase"
    elif kind == "expense":
        category = (request.form.get("category") or "").strip() or None

    # Обработка даты
    try:
        if operation_date_str:
            operation_date = datetime.strptime(operation_date_str, "%Y-%m-%d")
        else:
            operation_date = datetime.utcnow()
    except:
        operation_date = datetime.utcnow()

    # Создание документа операции
    doc = {
        "kind": kind,
        "amount": amount,
        "source": source,
        "ts": operation_date,
        "service_id": (svc_oid if kind == "income" else None),
        "patient_id": ObjectId(patient_id_str) if patient_id_str else None,
        "category": category,
        "note": note,
        "description": "",
        "cashier_id": cashier_oid if cashier_oid else None,
        "original_amount": original_amount if kind == "income" else None,
    }

    # Добавляем информацию о бонусах
    if bonus_amount > 0:
        doc["bonus_amount"] = bonus_amount
        doc["original_amount"] = original_amount
        doc["main_source"] = source
        doc["source"] = "mixed"  # Помечаем как смешанная оплата

    # Формирование описания
    if kind == "income" and svc_name:
        if bonus_amount > 0:
            doc["description"] = f"Услуга: {svc_name} (частично бонусами: {bonus_amount}₽)"
        else:
            doc["description"] = f"Услуга: {svc_name}"
    elif kind == "expense" and category:
        cat_names = {
            "rent": "Аренда",
            "purchase": "Закупка",
            "marketing": "Маркетинг",
            "salary": "ЗП",
            "dividends": "Дивиденды",
        }
        doc["description"] = f"Расход: {cat_names.get(category, category)}"

    # Обработка разделенных платежей
    split_payment_data = []
    if kind == "income" and request.form.get("split_source_1"):
        for i in range(1, 5):  # до 4 источников
            src = request.form.get(f"split_source_{i}", "").strip()
            amt = request.form.get(f"split_amount_{i}", "0").strip()
            if src and amt:
                try:
                    split_payment_data.append({"source": src, "amount": int(amt)})
                except ValueError:
                    continue

        if split_payment_data:
            doc["split_payments"] = split_payment_data
            doc["source"] = "split"  # Помечаем как комбинированную оплату

    # Сохраняем основную операцию
    result = db.ledger.insert_one(doc)

    # СОЗДАНИЕ ЗАПИСИ СПИСАНИЯ БОНУСОВ
    if bonus_amount > 0 and patient_id_str:
        try:
            patient_oid = ObjectId(patient_id_str)

            # Списываем бонусы у пациента
            db.patients.update_one({"_id": patient_oid}, {"$inc": {"bonus_balance": -bonus_amount}})

            # Создаем запись в историю бонусов
            bonus_doc = {
                "patient_id": patient_oid,
                "operation": "withdraw",
                "amount": bonus_amount,
                "related_ledger_id": result.inserted_id,
                "ts": operation_date,
                "description": f"Оплата услуги: {svc_name}",
            }
            db.bonus_history.insert_one(bonus_doc)

            write_log(
                action="bonus_withdraw",
                obj_type="patient",
                comment=f"Списано {bonus_amount}₽ бонусов для оплаты услуги",
            )

        except Exception as e:
            print(f"Ошибка при списании бонусов: {e}")

    # АВТОНАЧИСЛЕНИЕ БОНУСОВ РЕФЕРАЛУ
    if kind == "income" and patient_id_str:
        try:
            patient_oid = ObjectId(patient_id_str)
            patient = db.patients.find_one({"_id": patient_oid}, {"referred_by_patient_id": 1})

            if patient and patient.get("referred_by_patient_id"):
                referrer_id = patient["referred_by_patient_id"]
                referral_bonus_amount = int(original_amount * 0.1)

                if referral_bonus_amount > 0:
                    # Начисляем бонусы рефералу
                    db.patients.update_one(
                        {"_id": referrer_id}, {"$inc": {"bonus_balance": referral_bonus_amount}}
                    )

                    # Записываем в историю бонусов
                    referral_bonus_doc = {
                        "patient_id": referrer_id,
                        "operation": "referral_bonus",
                        "amount": referral_bonus_amount,
                        "related_patient_id": patient_oid,
                        "related_ledger_id": result.inserted_id,
                        "ts": operation_date,
                        "description": f"Реферальный бонус за приведенного пациента",
                    }
                    db.bonus_history.insert_one(referral_bonus_doc)

        except Exception as e:
            print(f"Ошибка при начислении реферальных бонусов: {e}")

    # СИСТЕМА ДОЛГОВ И ДЕПОЗИТОВ
    if kind == "income" and patient_id_str:
        try:
            total_paid = 0

            # Рассчитываем общую сумму оплаты
            if split_payment_data:
                total_paid = sum(split["amount"] for split in split_payment_data)
            else:
                total_paid = amount

            # Добавляем бонусы к общей сумме оплаты
            total_paid += bonus_amount

            # Сравниваем с изначальной стоимостью услуги
            if original_amount > total_paid:
                # Недоплата - создаем долг
                debt = original_amount - total_paid
                db.patients.update_one(
                    {"_id": ObjectId(patient_id_str)}, {"$inc": {"debt_balance": debt}}
                )
                flash(f"У пациента остался долг: {debt}₽", "warning")

            elif total_paid > original_amount:
                # Переплата - создаем депозит
                deposit = total_paid - original_amount
                db.patients.update_one(
                    {"_id": ObjectId(patient_id_str)}, {"$inc": {"deposit_balance": deposit}}
                )
                flash(f"Переплата зачислена на депозит: {deposit}₽", "info")

        except Exception as e:
            print(f"Ошибка при обработке долгов/депозитов: {e}")

    # Обновляем балансы касс
    if not split_payment_data and amount > 0:
        update_cashbox_balance(db, source, amount, kind)
    if bonus_amount > 0:
        flash(f"Операция сохранена. Списано {bonus_amount}₽ бонусов.", "success")

    from main import write_audit_log

    write_audit_log(
        action="create_finance_operation",
        obj_type="finance",
        obj_id=str(result.inserted_id),
        comment=f"Создана операция: {kind} {amount}₽",
    )

    # Очищаем старые flash перед редиректом
    session.pop("_flashes", None)

    # Сообщения о результате
    if bonus_amount > 0:
        flash(f"Операция сохранена. Списано {bonus_amount}₽ бонусов.", "success")

    flash("Операция успешно сохранена", "success")

    return redirect(url_for("finance.list_ops"))


@bp.get("/report/cashbox")
@login_required
@role_required(["admin", "owner"])
def report_cashbox():
    db = get_db()

    cashboxes = list(db.cashboxes.find({}, {"name": 1, "balance": 1, "updated_at": 1}))

    income = sum(int(x.get("amount", 0) or 0) for x in db.ledger.find({"kind": "income"}))
    deposit = sum(int(x.get("amount", 0) or 0) for x in db.ledger.find({"kind": "deposit"}))
    expense = sum(
        int(x.get("amount", 0) or 0)
        for x in db.ledger.find({"kind": {"$in": ["expense", "salary", "purchase"]}})
    )

    by_source = {}
    for op in db.ledger.find({"kind": "income"}):
        src = (op.get("source") or "unknown").lower()
        by_source[src] = by_source.get(src, 0) + int(op.get("amount", 0) or 0)

    by_category = {}
    for op in db.ledger.find({"kind": {"$in": ["expense", "purchase"]}}):
        cat = op.get("category") or "other"
        by_category[cat] = by_category.get(cat, 0) + int(op.get("amount", 0) or 0)

    return render_template(
        "finance/cashbox.html",
        cashboxes=cashboxes,
        income=income + deposit,
        expense=expense,
        by_source=by_source,
        by_category=by_category,
    )


@bp.route("/delete/<operation_id>", methods=["GET", "POST"])
@login_required
@role_required(["admin", "owner"])
def delete_operation(operation_id):
    from main import write_audit_log

    db = get_db()

    try:
        op_oid = ObjectId(operation_id)
    except:
        flash("Некорректный ID операции", "danger")
        return redirect(url_for("finance.list_ops"))

    operation = db.ledger.find_one({"_id": op_oid})
    if not operation:
        flash("Операция не найдена", "danger")
        return redirect(url_for("finance.list_ops"))

    if operation.get("appointment_id"):
        flash("Нельзя удалить автоматическую операцию от записи", "danger")
        return redirect(url_for("finance.list_ops"))

    kind = operation.get("kind")
    amount = int(operation.get("amount", 0) or 0)
    source = operation.get("source")

    if operation.get("split_payments"):
        for split in operation["split_payments"]:
            split_source = split["source"]
            split_amount = int(split["amount"])
            reverse_kind = "expense" if kind == "income" else "income"
            update_cashbox_balance(db, split_source, split_amount, reverse_kind)
    else:
        if source and source not in ["bonus", "mixed"]:
            reverse_kind = "expense" if kind == "income" else "income"
            update_cashbox_balance(db, source, amount, reverse_kind)

    if operation.get("bonus_amount") and operation.get("patient_id"):
        try:
            bonus_amount = int(operation.get("bonus_amount", 0))
            db.patients.update_one(
                {"_id": operation["patient_id"]}, {"$inc": {"bonus_balance": bonus_amount}}
            )

            db.ledger.delete_one({"related_ledger_id": op_oid, "kind": "bonus_payment"})

            db.bonus_history.insert_one(
                {
                    "patient_id": operation["patient_id"],
                    "operation": "refund",
                    "amount": bonus_amount,
                    "comment": f"Возврат бонусов после удаления операции",
                    "ts": datetime.utcnow(),
                }
            )

        except Exception as e:
            print(f"Ошибка при возврате бонусов: {e}")

    db.ledger.delete_one({"_id": op_oid})

    # ОТКАТ ДОЛГОВ И ДЕПОЗИТОВ
    if operation.get("patient_id") and kind == "income":
        try:
            patient_id = operation["patient_id"]
            original_amount = operation.get("original_amount", amount)

            # Если была переплата (депозит) - откатываем
            if amount > original_amount:
                deposit_amount = amount - original_amount
                db.patients.update_one(
                    {"_id": patient_id}, {"$inc": {"deposit_balance": -deposit_amount}}
                )

            # Если была недоплата (долг) - откатываем
            elif amount < original_amount:
                debt_amount = original_amount - amount
                db.patients.update_one(
                    {"_id": patient_id}, {"$inc": {"debt_balance": -debt_amount}}
                )

            print(f"Откат долга/депозита для пациента {patient_id}")
        except Exception as e:
            print(f"Ошибка при откате долга/депозита: {e}")

    from main import write_audit_log

    write_audit_log(
        action="delete_operation",
        obj_type="finance_operation",
        comment=f"Удалена операция: {kind} {amount}₽ из {source or 'неизвестно'}",
        details={
            "operation_id": str(op_oid),
            "kind": kind,
            "amount": amount,
            "source": source,
            "reversed_balance": True,
        },
    )

    flash(f"Операция удалена. Баланс кассы откатан на {amount}₽", "success")
    return redirect(url_for("finance.list_ops"))


def _query_from_args():
    f_type = (request.args.get("type") or "").strip()
    f_source = (request.args.get("source") or "").strip()
    f_category = (request.args.get("category") or "").strip()
    q = {}
    if f_type:
        q["kind"] = f_type
    if f_source:
        q["source"] = f_source
    if f_category:
        q["category"] = f_category
    return q


@bp.get("/export/csv")
@login_required
@role_required(["admin", "owner"])
def export_csv():
    db = get_db()
    q = _query_from_args()
    rows = list(db.ledger.find(q).sort("ts", -1))
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=";")
    w.writerow(["ts", "kind", "source", "amount", "category", "service_id", "note"])
    for r in rows:
        w.writerow(
            [
                (r.get("ts") or datetime.utcnow()).strftime("%Y-%m-%d %H:%M"),
                r.get("kind", ""),
                r.get("source", ""),
                int(r.get("amount", 0) or 0),
                r.get("category", ""),
                str(r.get("service_id") or ""),
                r.get("note", ""),
            ]
        )
    data = buf.getvalue().encode("utf-8-sig")
    return Response(
        data,
        headers={
            "Content-Disposition": "attachment; filename=finance_export.csv",
            "Content-Type": "text/csv; charset=utf-8",
        },
    )


@bp.get("/export/json")
@login_required
@role_required(["admin", "owner"])
def export_json():
    db = get_db()
    q = _query_from_args()
    rows = list(db.ledger.find(q).sort("ts", -1))
    for r in rows:
        r["_id"] = str(r["_id"])
        if r.get("service_id"):
            r["service_id"] = str(r["service_id"])
        if r.get("ts"):
            r["ts"] = r["ts"].strftime("%Y-%m-%d %H:%M")
    return Response(
        json.dumps(rows, ensure_ascii=False, indent=2),
        headers={
            "Content-Disposition": "attachment; filename=finance_export.json",
            "Content-Type": "application/json; charset=utf-8",
        },
    )


@bp.post("/import/json")
@login_required
@role_required(["admin", "owner"])
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
            ts_val = datetime.utcnow()
            if r.get("ts"):
                try:
                    ts_val = datetime.strptime(r["ts"], "%Y-%m-%d %H:%M")
                except:
                    pass

            doc = {
                "ts": ts_val,
                "ts_iso": ts_val.strftime("%Y-%m-%d %H:%M"),
                "kind": r.get("kind") or r.get("type"),
                "source": r.get("source"),
                "amount": int(r.get("amount", 0) or 0),
                "category": r.get("category") or None,
                "service_id": ObjectId(r["service_id"]) if r.get("service_id") else None,
                "note": r.get("note", ""),
                "status": r.get("status", "completed"),
            }
            if (
                doc["kind"] in ("income", "expense", "deposit", "salary", "purchase")
                and doc["amount"] > 0
            ):
                db.ledger.insert_one(doc)
                added += 1
        flash(f"Импортировано записей: {added}", "success")
    except Exception as e:
        flash(f"Ошибка импорта: {e}", "danger")
    return redirect(url_for("finance.list_ops"))
