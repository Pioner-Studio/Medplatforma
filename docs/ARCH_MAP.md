# ARCH_MAP.md — карта маршрутов и шаблонов

Колонки:
- Route — URL маршрута
- Methods — HTTP методы
- Template — основной шаблон (если есть)
- Status — verified / pending / deprecated

| Route | Methods | Template | Status |
|------|---------|----------|--------|
| /calendar | GET | calendar.html | pending |
| /patients/<id> | GET | patient_card.html | pending |

> Обновлять из docs/routes.json (генерится arch_verify.py).
