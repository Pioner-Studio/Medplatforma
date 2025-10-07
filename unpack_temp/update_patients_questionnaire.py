#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Добавление полей медицинской анкеты к существующим пациентам
"""

from main import db
from datetime import datetime


def add_questionnaire_fields():
    """Добавляет поля медицинской анкеты всем существующим пациентам"""

    # Структура минимальной медицинской анкеты
    default_questionnaire = {
        "allergies": {"has_allergies": False, "details": ""},
        "heart_conditions": {"has_conditions": False, "details": ""},
        "chronic_diseases": {"diabetes": False, "asthma": False, "oncology": False},
        "pregnancy": False,
        "dental_trauma": {"has_trauma": False, "when": "", "details": ""},
        "smoking": {"smokes": False, "duration": ""},
    }

    # Обновляем всех пациентов, у которых нет поля medical_questionnaire
    filter_query = {"medical_questionnaire": {"$exists": False}}
    update_query = {
        "$set": {
            "medical_questionnaire": default_questionnaire,
            "questionnaire_filled": False,
            "questionnaire_date": None,
            "questionnaire_signature": "",
        }
    }

    result = db.patients.update_many(filter_query, update_query)

    print(f"Обновлено пациентов: {result.modified_count}")

    # Проверяем результат
    total_patients = db.patients.count_documents({})
    patients_with_questionnaire = db.patients.count_documents(
        {"medical_questionnaire": {"$exists": True}}
    )

    print(f"Всего пациентов: {total_patients}")
    print(f"С анкетой: {patients_with_questionnaire}")

    # Показываем пример обновленного пациента
    sample = db.patients.find_one({"medical_questionnaire": {"$exists": True}})
    if sample:
        print("\nПример обновленного пациента:")
        print(f"- ФИО: {sample.get('full_name', 'Н/Д')}")
        print(f"- Анкета заполнена: {sample.get('questionnaire_filled', False)}")
        print(f"- Поля анкеты: {list(sample.get('medical_questionnaire', {}).keys())}")


if __name__ == "__main__":
    add_questionnaire_fields()
