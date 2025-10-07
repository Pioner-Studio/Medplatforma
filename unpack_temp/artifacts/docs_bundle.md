<!-- GENERATED: 2025-09-08 09:33:56 -->
# MedPlatforma Documentation Bundle
Generated: 2025-09-08 09:33:56
Source folder: .\docs
Files: 11

---

=== BEGIN FILE: API_CONTRACTS.md ===

# API_CONTRACTS

## GET /api/rooms/busy

Params: room_id=ObjectId, date=YYYY-MM-DD
Response:
{
"ok": true,
"items": [
{"start": "10:00", "end": "10:30"},
{"start": "11:15", "end": "12:00"}
]
}

## POST /api/doctor_schedule

Body:
{ "doctor_id": "<ObjectId>" }
Response:
{
"ok": true,
"schedule": {
"0": {"start": "09:00", "end": "21:00"},
…,
"6": {"start": "09:00", "end": "21:00"}
}
}

=== END FILE: API_CONTRACTS.md ===


=== BEGIN FILE: CHANGELOG.md ===

# CHANGELOG

## 2025-09-07

- Создан /docs и базовые файлы шаблонов
- Зафиксирован контракт /api/rooms/busy и /api/doctor_schedule

// Формат записи: Дата, Commit (если есть), краткое описание

=== END FILE: CHANGELOG.md ===


=== BEGIN FILE: CHECKLIST.md ===

# Медплатформа — Чек-лист (полный)

> Версия файла: 2025-09-08 09:30:25
> Ответственный за приёмку: ассистент (я)

## Легенда статусов
- ✅ Принято (доказательства проверены)
- 🔍 На приёмке (жду/проверяю артефакты)
- 🧪 На тесте (готово, но не предъявлено к приёмке)
- 🛠️ В работе
- 📆 Запланировано / Бэклог

## Процедура приёмки (обязательно)
1) Для каждого пункта подготовить **доказательства** (см. ниже).
2) Я проверяю и перевожу пункт в **✅ Принято** (фиксирую дату и ссылку на артефакты).
3) В этом файле сохраняем **полную историю выполненного** (никогда не вырезаем сделанное).

**Допустимые доказательства (подходит любой набор):**
- Скриншот(ы) интерфейса с пояснениями (PNG/JPG).
- Network/Console: скрин/копия запроса/ответа (URL, метод, код, JSON).
- Команды и вывод: Invoke-RestMethod/curl (с фактом успешного ответа).
- Логи Backend (строки с таймштампом) — для серверной логики.
- Небольшое видео (webm/mp4) на tricky-кейсы (по желанию).

**Где хранить артефакты:** docs/evidence/<дата_папка>/<пункт>/... (либо вложить в чат и дать якорь).

---

## 1) Календарь / Записи

### 1.1 Рендер и базовые настройки FullCalendar
- Статус: 🔍 На приёмке  
- Что должно быть: initialView=week, RU-локаль, 15-мин слоты, часы 09:00–21:00, firstDay=1, перетаскивание/растягивание включено.
- Доказательства:  
  - Скрин календаря с русскими кнопками/подписями.  
  - Лог/скрин ventDrop/ventResize → POST /api/appointments/update_time (200/ok).

### 1.2 Загрузка событий с фильтрами (врач/услуга/кабинет/пациент)
- Статус: 🔍 На приёмке  
- Что должно быть: vents(fetchInfo) пробрасывает doctor_id, service_id, 
oom_name, patient_id.
- Доказательства:  
  - Network: GET /api/events?...patient_id=... (и другие параметры), JSON с отфильтрованными событиями.
  - Скрин календаря до/после установки фильтров.

### 1.3 Мини-поиск по пациентам (поле над календарём)
- Статус: 🔍 На приёмке  
- Что должно быть: дебаунс, выпадающий список, выбор на mousedown, «Сбросить» очищает и перезагружает события.
- Доказательства:  
  - Видео/скрин: набираем «ива» → 2–5 кандидатов → клик → календарь оставляет записи нужного пациента.  
  - Network: видно patient_id в запросе /api/events.

### 1.4 Модалка «Быстрая запись»
- Статус: 🔍 На приёмке  
- Что должно быть: создание/редактирование, кнопки +15/+30/+60, «на завтра», first-free-slot по кабинету, подсказка длительности, предупреждение «вне графика врача».
- Доказательства:  
  - Видео/скрин: открыть по клику на сетке → заполнить → «Сохранить» → запись появилась.  
  - Network:  
    - Create: успешный POST на один из эндпоинтов-кандидатов (см. 1.5).  
    - Update time: POST /api/appointments/update_time (200/ok).

### 1.5 Создание/Удаление (цепочка эндпоинтов-кандидатов)
- Статус: 🔍 На приёмке  
- Что должно быть:  
  - Create (по очереди): /api/appointments → /api/appointments/create → /schedule/api/create.  
  - Delete (кандидаты): /schedule/api/delete → /api/appointments/delete → DELETE /api/appointments/{id}.  
  - Обработка конфликтов: 409 либо {error:"room_conflict"} → тост «Кабинет/врач занят».
- Доказательства:  
  - Скрины Network по каждому успешному сценарию.  
  - Скрин с конфликтом/тостом.

### 1.6 Контакт-бар Tel/WA/TG/Max/Mail (в модалке)
- Статус: 🔍 На приёмке  
- Что должно быть: запрос /api/patients/{id}/contacts, построение корректных ссылок; подсказка с телефоном/почтой.
- Доказательства:  
  - Network GET /api/patients/<id>/contacts (ok, JSON).  
  - Скрин активных кнопок/подсказки.

### 1.7 Автосоздание пациента из модалки
- Статус: 🔍 На приёмке  
- Что должно быть: при заполнении блока «Новый пациент» → POST /api/patients → новый id подставляется в select, кэш обновлён.
- Доказательства:  
  - Network POST /api/patients → {ok:true,id:...}.  
  - Скрин: select «Пациент» после создания.

### 1.8 Rooms-bar (статусы кабинетов + ближайший слот)
- Статус: 🔍 На приёмке  
- Что должно быть: текущее состояние + «Ближайший» (время, услуга/пациент, мин до начала).
- Доказательства:  
  - Скрин панели, скрин расчёта «in_minutes».

---

## 2) Backend / API контракты (календарь)

### 2.1 Контракты (минимум)
- Статус: 🛠️ В работе  
- Список:  
  - GET /api/dicts → {doctors[], patients[], rooms[], services[] (duration_min)}  
  - GET /api/patients/min?q=&limit= → {items[]}  
  - GET /api/patients/{id}/contacts → {contacts,links?}  
  - GET /api/events?start=&end=&doctor_id?=&service_id?=&room_name?=&patient_id?= → []  
  - POST /api/appointments **или** /api/appointments/create **или** /schedule/api/create → {ok,id}  
  - POST /api/appointments/update_time → {ok}|{error:"room_conflict"}  
  - POST /api/appointments/{id}/update → {ok}|{error:"room_conflict"}  
  - POST /api/appointments/delete **или** POST /schedule/api/delete **или** DELETE /api/appointments/{id} → {ok}
  - POST /api/doctor_schedule (body:{doctor_id}) → {schedule:{0..6:{start,end}}}  
  - GET /api/rooms/busy?room_id=&date=YYYY-MM-DD → {items:[{start:"HH:MM",end:"HH:MM"}]}
- Доказательства:  
  - В папке docs/evidence/api/ — по одному JSON-примеру ответа на каждый маршрут.

---

## 3) Финансы (из плана 23.08)

### 3.1 Базовые вещи
- Статус: 🔍 На приёмке  
- Что должно быть:  
  - Раздел открывается (Blueprint/роут подключён, 404 нет).  
  - Форма «Внести» открывается.  
  - Услуги/суммы тянутся из прайса (жёстко на бэке).
- Доказательства:  
  - Скрин раздела и формы.  
  - Network/логи — успешное сохранение одной операции.

### 3.2 Запланировано
- 📆 Отчёт «Касса» по источникам (alpha/sber/cash).  
- 📆 Категории расходов (Аренда, Закупка, Маркетинг, Дивиденды).  
- 📆 Привязка операций к пациентам/врачам, «Долг/депозит», учёт выплат врачу.

---

## 4) Данные/Справочники

### 4.1 Кэш словарей на фронте (нормализация id/name/duration)
- Статус: 🔍 На приёмке  
- Доказательства:  
  - Скрин/фрагмент Network GET /api/dicts + скрин селектов (врач/услуга/кабинет/пациент).

---

## 5) UX/UI общие

### 5.1 Toast-система, дефолты select, защита от «битых» значений
- Статус: 🔍 На приёмке  
- Доказательства:  
  - Скрины тостов (ok/error), селекты с валидным значением по умолчанию.

---

## 6) Безопасность / Сессии

### 6.1 Редиректы на /login при неавторизованном доступе
- Статус: 🔍 На приёмке  
- Доказательства:  
  - Логи сервера (302 на /login) при попытке открыть /calendar без сессии.

---

## 7) Тесты/Демо-данные

### 7.1 Мини-набор для демонстрации
- Статус: 🛠️ В работе  
- Что нужно: 5–10 пациентов, 3–4 врача, 4–5 услуг (с разной длительностью), 3–5 записей на неделю.
- Доказательства:  
  - Скрин календаря (неделя), JSON GET /api/events.

---

## Бэклог (ключевое)
- 📆 Множественный выбор фильтров (врач/кабинет).  
- 📆 Экспорт видимой сетки календаря (PDF/PNG).  
- 📆 Карточка пациента: анкета, план лечения, напоминания ко ДР.  
- 📆 Чаты (пациент↔куратор, сотрудники).  
- 📆 ZTL/Лаборатория.  
- 📆 Склад (остатки/заказы).  
- 📆 Зубная формула.  
- 📆 Документация API (под каждую фичу) + автогенерация примеров.

---

## История изменений чек-листа
- YYYY-MM-DD: создана единая структура статусов, добавлена обязательная процедура приёмки.

=== END FILE: CHECKLIST.md ===


=== BEGIN FILE: DB_SCHEMA.md ===

# DB_SCHEMA (актуальная схема)

## collections.doctors

- \_id: ObjectId
- full_name: string
- room_id: ObjectId
- schedule: { "0": {start:"09:00", end:"21:00"}, …, "6": {…} }
- specialties: ["Терапия"|"Ортодонтия"|…]

## collections.patients

- \_id: ObjectId
- full_name: string
- birth_date: YYYY-MM-DD
- card_no: string
- allergies: [string]
- diseases: [string]
- surgeries: [string]

## collections.rooms

- \_id: ObjectId
- name: string ("Детский"|"Ортопедия"|…)
- code: string (например, R01)

## collections.events

- \_id: ObjectId
- start: ISODate
- end: ISODate
- doctor_id: ObjectId
- patient_id: ObjectId
- room_id: ObjectId
- status: string ("planned"|"done"|"cancelled")
- note: string
- source: string ("admin"|"web")

## collections.finance

- \_id: ObjectId
- type: string ("income"|"expense"|"deposit"|"purchase")
- amount: number
- category: string
- source: string
- comment: string
- created_at: ISODate

## Indexes (минимум)

- events: { doctor_id:1, start:1 }, { room_id:1, start:1 }
- finance: { created_at:-1 }, { category:1 }

=== END FILE: DB_SCHEMA.md ===


=== BEGIN FILE: PATCH_FORMAT.md ===

# PATCH_FORMAT

## Вариант A — Drop‑in replacement

Присылаю целый файл, который ты просто заменяешь 1:1.

## Вариант B — Патч‑вставка по якорям

Формат:

=== PATCH: templates/calendar.html ===
AFTER: <!-- quick-move buttons -->
INSERT:

<div class="btns">
<button id="plus15">+15</button>
<button id="plus30">+30</button>
</div>
=== END PATCH ===

Альтернатива по линиям:

=== PATCH: main.py ===
RANGE: L210-L248 (заменить целиком)
REPLACE_WITH:

# новый код здесь…

=== END PATCH ===

Правила:

- Каждый патч содержит ровно один файл.
- Якорь (AFTER/BEFORE) должен существовать в файле.
- Если якоря нет → сначала присылай актуальный файл.

=== END FILE: PATCH_FORMAT.md ===


=== BEGIN FILE: PROJECT_HEADER.md ===

# PROJECT_HEADER

## Runtime

- Python: 3.12.x
- Flask: <версия>
- Jinja2: <версия>
- FullCalendar: <версия>
- MongoDB: Atlas, кластер <имя/регион>

## App

- Entry: main.py
- Host/Port (dev): 127.0.0.1:5000
- DEBUG: on/off

## Front

- Templates path: /templates
- Static: /static (css, js, img)

## Notation

- Timezone: Europe/Amsterdam
- Locale: ru-RU

=== END FILE: PROJECT_HEADER.md ===


=== BEGIN FILE: REQUEST_TEMPLATE.md ===

# REQUEST_TEMPLATE (копируй в сообщение при новой задаче)

## 1) Цель

Коротко: что хотим получить (1–2 предложения).

## 2) Файлы, которые меняем

- <путь/к/файлу1>
- <путь/к/файлу2>

## 3) Где править (якоря/строки)

- Файл A: AFTER("<точный маркер>")
- Файл B: RANGE Lxxx-Lyyy

## 4) Данные/контракты

- Новые поля БД / новые эндпоинты / формат JSON (если есть)

## 5) Ожидаемый результат

- Что должно заработать на фронте/бэке

## 6) Прочее

- Скрин/лог/ошибка (если есть)

=== END FILE: REQUEST_TEMPLATE.md ===


=== BEGIN FILE: ROUTES_MAP.md ===

# ROUTES_MAP

| URL                  | Method | Handler (функция)     | Шаблон                  | Примечания                      |
| -------------------- | ------ | --------------------- | ----------------------- | ------------------------------- |
| /                    | GET    | index()               | templates/index.html    | Главная                         |
| /calendar            | GET    | calendar()            | templates/calendar.html | FullCalendar                    |
| /api/rooms/busy      | GET    | api_rooms_busy()      | —                       | Query: room_id, date=YYYY-MM-DD |
| /api/doctor_schedule | POST   | api_doctor_schedule() | —                       | Body: { doctor_id }             |
| …                    | …      | …                     | …                       | …                               |

=== END FILE: ROUTES_MAP.md ===


=== BEGIN FILE: ROUTES.md ===

# Flask routes map

_generated: 2025-09-08 00:33:39_


| Rule | Endpoint | Methods |
|------|----------|---------|
| `/` | `home` | `GET` |
| `/add_doctor` | `add_doctor` | `GET,POST` |
| `/add_event` | `add_event` | `GET,POST` |
| `/add_patient` | `add_patient` | `GET,POST` |
| `/add_room` | `add_room` | `GET,POST` |
| `/add_service` | `add_service` | `GET,POST` |
| `/add_task` | `add_task` | `POST` |
| `/add_ztl` | `add_ztl` | `GET,POST` |
| `/api/appointments/<id>` | `api_appointment_get` | `GET` |
| `/api/appointments/<id>` | `api_appointments_delete_by_id` | `DELETE` |
| `/api/appointments/<id>/update` | `api_appointment_update` | `POST` |
| `/api/appointments/delete` | `api_appointments_delete_post` | `POST` |
| `/api/appointments/update_time` | `api_appointments_update_time` | `POST` |
| `/api/busy_slots` | `api_busy_slots` | `POST` |
| `/api/chat/<id>/send` | `api_chat_send` | `POST` |
| `/api/dicts` | `api_dicts` | `GET` |
| `/api/doctor_schedule` | `doctor_schedule` | `POST` |
| `/api/events` | `api_events` | `GET` |
| `/api/finance/record` | `api_finance_record` | `POST` |
| `/api/free_slots` | `api_free_slots` | `POST` |
| `/api/patients/<id>` | `api_patient_get` | `GET` |
| `/api/patients/<id>/contacts` | `api_patient_contacts_min` | `GET` |
| `/api/patients/<id>/full` | `api_patient_full` | `GET` |
| `/api/patients/<id>/generate_card_no` | `api_patient_generate_card_no` | `POST` |
| `/api/patients/<id>/min` | `api_patient_min_by_id` | `GET` |
| `/api/patients/<id>/update` | `api_patient_update` | `POST` |
| `/api/patients/<id>/update_info` | `api_patient_update_info` | `POST` |
| `/api/patients/<id>/update_questionary` | `api_patient_update_questionary` | `POST` |
| `/api/patients/min` | `api_patients_min_list` | `GET` |
| `/api/rooms/busy` | `api_room_busy` | `GET` |
| `/api/rooms/status_now` | `api_rooms_status_now` | `GET` |
| `/api/rooms/today_details` | `api_rooms_today_details` | `GET` |
| `/api/services/<id>` | `api_service_get` | `GET` |
| `/api/services_min` | `api_services_min` | `GET` |
| `/api/visit_statuses_min` | `api_visit_statuses_min` | `GET` |
| `/backup` | `backup` | `GET` |
| `/busy_slots/<doctor_id>` | `busy_slots` | `GET` |
| `/cabinet/<cabinet_name>` | `cabinet_card` | `GET` |
| `/calendar` | `calendar_view` | `GET` |
| `/data_tools` | `data_tools` | `GET,POST` |
| `/delete_appointment/<id>` | `delete_appointment` | `POST` |
| `/delete_patient/<id>` | `delete_patient` | `POST` |
| `/delete_room/<id>` | `delete_room` | `POST` |
| `/delete_service/<id>` | `delete_service` | `POST` |
| `/doctor_busy_slots/<doctor_id>` | `doctor_busy_slots` | `GET` |
| `/doctor_card/<doctor_id>` | `doctor_card` | `GET` |
| `/doctors` | `doctors` | `GET` |
| `/edit_event/<event_id>` | `edit_event` | `GET,POST` |
| `/edit_patient/<id>` | `edit_patient` | `GET,POST` |
| `/edit_room/<id>` | `edit_room` | `GET,POST` |
| `/edit_service/<id>` | `edit_service` | `GET,POST` |
| `/export_calendar` | `export_calendar` | `GET` |
| `/export_data` | `export_data` | `GET` |
| `/favicon.ico` | `favicon` | `GET` |
| `/finance` | `finance.list_ops` | `GET` |
| `/finance/add` | `finance.add_get` | `GET` |
| `/finance/add` | `finance.add_post` | `POST` |
| `/finance/export/csv` | `finance.export_csv` | `GET` |
| `/finance/export/json` | `finance.export_json` | `GET` |
| `/finance/import/json` | `finance.import_json` | `POST` |
| `/finance/report/cashbox` | `finance.report_cashbox` | `GET` |
| `/finance_report` | `finance_report` | `GET` |
| `/finance_report/export` | `finance_report_export` | `GET` |
| `/import_data` | `import_data` | `POST` |
| `/login` | `login` | `GET,POST` |
| `/logout` | `logout` | `GET` |
| `/logs` | `logs` | `GET` |
| `/mark_task_done/<task_id>` | `mark_task_done` | `GET` |
| `/messages` | `messages` | `GET` |
| `/partners` | `partners` | `GET` |
| `/patient_card/<id>` | `patient_card` | `GET` |
| `/patients` | `patients_list` | `GET` |
| `/patients/<id>` | `patient_card_page` | `GET` |
| `/patients/<pid>` | `patient_view` | `GET` |
| `/patients/<pid>/edit` | `patient_edit_form` | `GET` |
| `/patients/<pid>/edit` | `patient_edit_save` | `POST` |
| `/patients/<pid>/questionnaire` | `questionnaire_form` | `GET` |
| `/patients/<pid>/questionnaire` | `questionnaire_save` | `POST` |
| `/profile` | `profile` | `GET` |
| `/roadmap` | `roadmap_view` | `GET` |
| `/rooms` | `rooms_list` | `GET` |
| `/schedule/` | `schedule.list_view` | `GET` |
| `/schedule/add` | `schedule.add_appointment` | `POST` |
| `/schedule/api/delete` | `schedule_api_delete_proxy` | `POST` |
| `/schedule/free_slots` | `schedule.free_slots` | `GET` |
| `/services` | `services_list` | `GET` |
| `/settings` | `settings` | `GET` |
| `/static/<path:filename>` | `static` | `GET` |
| `/task/<task_id>` | `task_card` | `GET` |
| `/tasks` | `tasks` | `GET` |
| `/update_event_time` | `update_event_time` | `POST` |
| `/ztl` | `ztl` | `GET` |

=== END FILE: ROUTES.md ===


=== BEGIN FILE: TEMPLATES_MAP.md ===

# TEMPLATES_MAP

| Шаблон                      | Описание/где используется | Ключевые блоки/якоря                          |
| --------------------------- | ------------------------- | --------------------------------------------- |
| templates/calendar.html     | Календарь расписания      | <!-- toolbar -->, <!-- quick-move buttons --> |
| templates/finance/list.html | Список операций           | <!-- filters -->, <!-- table -->              |
| …                           | …                         | …                                             |

=== END FILE: TEMPLATES_MAP.md ===


=== BEGIN FILE: WORKFLOW.md ===

## TL;DR — Золотые правила

1. **Всегда присылаем актуальные файлы целиком** (до изменений): только по ним даю правки (drop-in или патч-вставки). Никаких догадок.
2. **Формат ответа от меня** — либо «drop-in replacement» (полный файл), либо «патч-вставка» с точными якорями/строками.
3. **Единый источник правды — `/docs/`**: ROUTES_MAP, DB_SCHEMA, API_CONTRACTS, TEMPLATES_MAP, CHECKLIST, CHANGELOG. Любое изменение сначала фиксируем там.
4. **Каждая задача = мини-пакет**: цель → файлы для правки → якоря/строки → контракты/данные → ожидаемый результат.
5. **Никакой локальной магии**: если файла нет в сообщении/`/docs` — правки не выдаю, сначала получаю актуальный файл.

**Подтверждение выполнения (новое правило):** 6) В **CHECKLIST** отмечаем «сделано» **только при подтверждении**:

- либо **текстовая команда** с формулировкой «принято / работает»,
- либо **скриншот/краткое видео/лог**, подтверждающий результат.
  Без подтверждения — пункт остаётся в статусе «в работе».

Операционный порядок:

- Если правка затрагивает **API/БД** — сначала обновляем `API_CONTRACTS.md` / `DB_SCHEMA.md`.
- В ответах всегда даю точные якоря: `AFTER("<!-- marker -->")` или `RANGE L210–L248`.
- После применения патча — обновляем `CHANGELOG.md` и `CHECKLIST.md` (с подтверждением результата).

=== END FILE: WORKFLOW.md ===

