# constants.py

# Статусы планов лечения
PLAN_STATUS_DRAFT = "draft"
PLAN_STATUS_PENDING = "pending_approval"
PLAN_STATUS_APPROVED = "approved"
PLAN_STATUS_REJECTED = "rejected"

PLAN_STATUSES = {
    PLAN_STATUS_DRAFT: "Черновик",
    PLAN_STATUS_PENDING: "На согласовании",
    PLAN_STATUS_APPROVED: "Одобрен",
    PLAN_STATUS_REJECTED: "Отклонён",
}

# Статусы услуг в плане
SERVICE_STATUS_PLANNED = "planned"
SERVICE_STATUS_COMPLETED = "completed"

# Статусы долгов
DEBT_STATUS_UNPAID = "unpaid"
DEBT_STATUS_PARTIALLY_PAID = "partially_paid"
DEBT_STATUS_PAID = "paid"

DEBT_STATUSES = {
    DEBT_STATUS_UNPAID: "Не оплачен",
    DEBT_STATUS_PARTIALLY_PAID: "Частично оплачен",
    DEBT_STATUS_PAID: "Оплачен",
}

# Статусы платежей
PAYMENT_STATUS_COMPLETED = "completed"
PAYMENT_STATUS_PENDING = "pending_confirmation"

# Способы оплаты
PAYMENT_METHOD_CASH = "cash"
PAYMENT_METHOD_CARD = "card_terminal"
PAYMENT_METHOD_TRANSFER = "bank_transfer"
PAYMENT_METHOD_ADVANCE = "advance"
PAYMENT_METHOD_BONUS = "bonus"
PAYMENT_METHOD_COMBINED = "combined"

PAYMENT_METHODS = {
    PAYMENT_METHOD_CASH: "Наличные",
    PAYMENT_METHOD_CARD: "Карта (терминал)",
    PAYMENT_METHOD_TRANSFER: "Перевод на карту",
    PAYMENT_METHOD_ADVANCE: "Из аванса",
    PAYMENT_METHOD_BONUS: "Бонусами",
    PAYMENT_METHOD_COMBINED: "Комбинированная",
}

# Роли
ROLE_ADMIN = "admin"
ROLE_DOCTOR = "doctor"
ROLE_CHIEF_DOCTOR = "chief_doctor"

# Бонусы
BONUS_LEVEL_1_PERCENT = 10  # Первое поколение - 10%
BONUS_LEVEL_2_PERCENT = 3  # Второе поколение - 3%
MAX_REFERRAL_LEVELS = 3  # Максимум 3 поколения
