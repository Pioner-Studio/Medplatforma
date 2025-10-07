# Medplatforma — docs_bundle.md (ОПЕРАТИВНЫЙ ДОКУМЕНТ)
_Обновлено: 2025-10-07 10:45_


> Это **главный рабочий файл проекта**. Здесь: правила без-гадания, порядок инспекции, текущие планы (2–7 дней), баги/долги, ченджлог, и ссылки на архитектурные карты.
> Любые изменения — только через **Patch Grammar** и с подтверждением инспекцией.

---

## 0) Контекст проекта (кратко)
- Стек: **Flask + MongoDB**, фронт — Jinja2 + JS (FullCalendar).
- Роли:
  - **Владельцы:** Наконечный, Наконечная, Гогуева.
  - **Главврач:** Гогуева — отвечает за **финальный план лечения**.
  - **Финансист:** Наконечный — подтверждает все **финансовые потоки**.
  - **Наконечная:** владелец и **временно администратор**.
- Доступы и UI: врачи видят **цены, долги, оплаты**; из календаря переход в **карту пациента**.

---

## 1) SAFE_EDIT_PROTOCOL (никаких догадок)
- Любые правки **запрещены без инспекции** текущего состояния репозитория.
- Работа начинается с **INSPECTION MODE** → собираем артефакты (см. §2).
- Патчи выдаются **только как минимальные diffs по диапазонам строк** (например, `calendar.html L1980–2055`).
- Большие файлы (HTML/JS) присылаем **вырезками** или экспортом в `.txt`.
- После каждого патча обязательно:
  - локальная проверка (DevTools/консоль + curl),
  - обновление `CHANGELOG`,
  - при затрагивании маршрутов — обновление `ARCH_MAP.md` (статусы `planned/pending → verified`).

### Patch Grammar
```
UPDATE:
- <FILE>: <кратко что меняем> (L<from>–<to>)
- Причина: <root cause>
- Проверка: <команда/шаги>
```

---

## 2) INSPECTION MODE (всегда перед правками)
Попроси запустить команды ниже и приложить артефакты. Без этого **никаких правок**.

### 2.1 Команды инспекции (PowerShell)
```powershell
# Сканер маршрутов/шаблонов
python .\docs\arch_verify.py --root . --out .\docs\routes.json

# Все Flask-роуты
Get-ChildItem -Recurse -Include *.py | Select-String -Pattern '@\w+\.route\(' | Select Path,LineNumber,Line

# Где рендерятся шаблоны
Get-ChildItem -Recurse -Include *.py | Select-String -Pattern 'render_template\(' | Select Path,LineNumber,Line

# Вызовы API/переходы из JS/HTML
Get-ChildItem -Recurse -Include *.js,*.ts,*.html | Select-String -Pattern 'fetch\(|location\.href|window\.location\.href' | Select Path,LineNumber,Line

# Поиск функции/ошибки (пример: openStatusModal)
Get-ChildItem -Recurse -Include *.js,*.html | Select-String -Pattern 'openStatusModal' -SimpleMatch | Select Path,LineNumber,Line

# Проверка артефактов шаблона (лишние скобки)
Get-Content .\templates\calendar.html | Select-String -Pattern '}}}}|{{{{'

# Показать фрагмент с номерами строк
function Show-Lines($Path,$From,$To){
  $i=1; Get-Content $Path | ForEach-Object {
    if($i -ge $From -and $i -le $To) { "{0,6}: {1}" -f $i, $_ }
    $i++
  }
}
# Пример:
Show-Lines .\templates\calendar.html 1980 2055

# Экспорт большого HTML в .txt и на части
Get-Content -Raw .\templates\calendar.html | Set-Content .\docs\calendar.html.txt
$lines=Get-Content .\templates\calendar.html
$chunk=500;$i=0;$part=1
while($i -lt $lines.Count){
  $out=$lines[$i..([Math]::Min($i+$chunk-1,$lines.Count-1))]
  $out | Set-Content (".\docs\calendar.part{0:D2}.txt" -f $part)
  $i+=$chunk;$part++
}

# Быстрая проверка событий
curl http://127.0.0.1:5000/api/events
```

### 2.2 Что предоставить в чат после инспекции
- `docs/routes.json`
- grep-выводы (роуты, шаблоны, js-переходы)
- фрагменты `Show-Lines` по запросу (точные диапазоны)
- ответ `curl /api/events` (проверка `extendedProps`)

---

## 3) Route Summary (быстрые переходы)
- `/calendar` → модалка → `POST /appointments/<id>/complete` → **refetchEvents()**
- «Подробнее» в модалке → `GET /patients/<id>`
- «Записать повторно» → черновик записи (предзаполнение из `extendedProps`)
- Финансы: `POST /finance/add`, `POST /finance/transfer`
- Согласования: `GET /chief/pending-plans`

> Полная таблица маршрутов со статусами — **ARCH_MAP.md**. При изменениях — всегда обновлять.

---

## 4) Активные проблемы / TECH-DEBT
### P1 — Calendar click → модалка не открывается (критично)
- Симптом: `Uncaught ReferenceError: openStatusModal is not defined` (DevTools).
- Причина: гибрид `/calendar`↔`/schedule`, утрата JS-обработчика/подключения.
- Стратегия восстановления: см. `CLAUDE_MIGRATION_NOTES.md` (Track A).

### P2 — Дубли шаблонов/роутов после экспериментов
- Действие: единый маршрут `/calendar` + `calendar.html`; временный 302-редирект с `/schedule`; чистка дублей.

---

## 5) LOCAL_PLAN (2–7 дней)
**D0 (сегодня)**
- [ ] INSPECTION MODE: собрать артефакты (см. §2), приложить в чат.
- [ ] Объединить `schedule_view.html` → `calendar.html` (патч строго по строкам, после инспекции).
- [ ] Вернуть маршрут `/calendar`, добавить 302-редирект с `/schedule`.
- [ ] Восстановить JS-обработчики: `openStatusModal`, `viewDetails`, `repeatAppointment`, `refetchEvents`.

**D1 (завтра)**
- [ ] Проверить `/api/events` на наличие `extendedProps` (patient_id, doctor_id, service_id, status).
- [ ] Удалить временные маршруты и лишние подключения JS, очистить кеш браузера.
- [ ] Обновить `ARCH_MAP.md` (статусы → `verified`), `CHANGELOG`.

**D2–D3**
- [ ] Стабилизация календаря (цвета/бейджи, фильтры).
- [ ] Подготовка UI к **Интерактивной зубной формуле** (см. `DENTAL_CHART_SPEC.md`).
- [ ] Начало имплементации **Планов лечения 1.0** (CRUD + approve главврачом).

---

## 6) CHANGELOG (вписывать только фактические изменения)
- _YYYY‑MM‑DD hh:mm_ — [кто] — [что изменили кратко] — [файлы/строки] — [ссылка на инспекцию/артефакты]

Пример:
- 2025‑10‑07 13:20 — dev — Объединён календарь, восстановлены обработчики — `calendar.html L1980–2055`, `calendar_init.js L120–168` — инспекция A–E.

---

## 7) Документы проекта (обязательно держать актуальными)
- **ARCH_MAP.md** — карта маршрутов/шаблонов с метками `verified/pending/planned`.  
  Обновлять через `UPDATE:` и сканер `arch_verify.py` → `docs/routes.json`.
- **CLAUDE_MIGRATION_NOTES.md** — история проблем с календарём и план восстановления.
- **roadmap_master.md** — стратегия 3–12 мес (не переписывать, только дополнять).
- **DENTAL_CHART_SPEC.md** — полная спецификация «зубной формулы».

---

## 8) Session Template (как начинаем любую сессию в ChatGPT)
```
INSPECTION MODE:
- Run the inspection commands (see docs_bundle.md §2) and attach:
  - docs/routes.json
  - grep outputs (routes/templates/js calls)
  - requested Show-Lines snippets
  - curl /api/events output
Then provide: Root cause + Minimal patch plan (file + line ranges) for me (beginner). Ask for confirmation after each step.
```

---

## 9) Правила общения с ИИ (важно)
- Пользователь — **новичок**. Все инструкции давать **максимально развернутыми**, с примерами команд и проверок.
- После каждого шага спрашивать: **«Всё получилось? Что вывело?»** и ждать обратной связи.
- Никогда не предлагать «переписать файл целиком». Только **минимальные правки по строкам**.
- Если чего‑то не хватает — **запросить артефакты** по §2.

---

---

## Методика: Inspection‑First ChatOps (Command‑and‑Verify)
- Назначение: полностью исключить «гадание». Любые правки идут **после** инспекции кода.
- Инструменты дисциплины:
  1) **arch_verify.py** → `docs/routes.json` (фактические маршруты/шаблоны).
  2) **ARCH_MAP.md** → статусы `verified/pending/planned` + блоки `UPDATE:`.
  3) **GitHub Action Arch Guard** → блокирует PR без свежих `routes.json` и обновлённого `ARCH_MAP.md`.
- Процесс (каждый сеанс):
  1) INSPECTION MODE → собрать артефакты (см. §2).
  2) Диагноз + Мини‑патч (файл + диапазон строк).
  3) Верификация (DevTools/curl) → CHANGELOG → обновление ARCH_MAP при изменении маршрутов.
