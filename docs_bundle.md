# docs_bundle.md (РУССКАЯ ВЕРСИЯ)
_Обновлено: 2025-10-07 06:35_

> **Единый источник правды (SSOT) для проекта Medplatforma.**
> Любая сессия ChatGPT/Claude берёт контекст из этого файла.
> Обновлять **только то**, что реально сделано (см. Patch Grammar в AI_WORK_PROTOCOL.md).

---

## 1) ОБЩИЙ ПЛАН (GLOBAL_ROADMAP, квартал)
- [ ] P1 Расписание (кабинеты, врачи, ресурсная ось)
- [ ] P1 Пациенты (карточка, CRUD, поиск)
- [ ] P1 Финансы (касса, счета, отчёты)
- [ ] P2 Роли и права (admin/doctor/operator)
- [ ] P2 Склад и каталог услуг
- [ ] P3 Отчёты и дашборды

---

## 2) ЛОКАЛЬНЫЙ ПЛАН (на 2–3 дня)
**D0 (сегодня):**
- [ ] Исправить ресурсную ось FullCalendar (кабинеты по оси)
- [ ] Валидировать payload API событий (schema v1.2)
- [ ] Добавить проверку конфликтов по кабинетам

**D1 (завтра):**
- [ ] Модалка «быстрая запись» (мини‑поиск пациента)
- [ ] Drag&drop обновление → PATCH /events/<id>

**D2:**
- [ ] Финансы: модель счёта + эндпоинт GET/POST /invoices

---

## 3) ЖУРНАЛ ИЗМЕНЕНИЙ (CHANGELOG)
-

---

## 4) БАГИ / ТЕХ.ДОЛГ (BUGS / TECH-DEBT)
- [ ] FullCalendar resourceTimeGridDay не рендерится (несоответствие плагина)
- [ ] calendar.html: сдвиг таймзоны vs серверный now()
- [ ] Seed: уникальный индекс (room_id + start_time)

---

## 5) КАРТА МАРШРУТОВ (ROUTES_MAP)
| Роут | Файл | Описание |
|------|------|----------|
| /calendar | templates/calendar.html | Главная страница календаря, статусы и модалки |
| /api/events | app.py | API событий |
| /appointments/<id>/complete | app.py | Завершение приёма |
| /finance/add | templates/finance/add.html | Добавление платежа |
| /patients/<id> | templates/patient_card.html | Карточка пациента |

---

## 6) СВЯЗИ ФАЙЛОВ (FILE_DEPENDENCY)
- main.py ↔ templates/calendar.html ↔ static/js/calendar_init.js
- Роуты в app.py зависят от коллекций MongoDB Atlas
- patient_card.html использует partials из /templates/patients/

---

## 7) МОДЕЛИ ДАННЫХ (Mongo)
- events: {_id, start, end, room_id, doctor_id, patient_id, status, notes}
- patients: {_id, name, phone, dob}
- invoices: {_id, patient_id, items[], total, status}

---

## 8) ПЛАН ТЕСТОВ (TESTS_PLAN)
- API /api/events возвращает 200 и непустой список для засеянного дня
- Создание пересекающейся записи в одном кабинете возвращает 409
- Мини‑поиск пациента в модалке показывает выпадающий список
- Фильтр по кабинетам скрывает/показывает события

---

## 9) ДОЛГОСРОЧНЫЕ ЗАДАЧИ (LONG_TERM_TASKS)
- [ ] Голосовой ассистент: «Запиши Петрова к врачу Иванову завтра 17:00»
- [ ] ИИ‑модуль оценки кариеса по рентгенам (подсветка областей)
- [ ] Экспорт в XLSX
- [ ] SMS‑напоминания
