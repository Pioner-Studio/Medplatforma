# START_SESSION.md (ШАБЛОН ЗАПУСКА СЕССИИ)
_Использовать в начале **каждого** нового чата с ChatGPT или Claude._

Проект: **Medplatforma** (Flask + MongoDB, Jinja2, FullCalendar).  
Протокол: **AI_WORK_PROTOCOL.md** (следуй всем правилам).  
Память/контекст: **docs_bundle.md** (обновляй только запрошенные секции).  
Среда: пользователь — новичок; работает в **Visual Studio Code** и **PowerShell (Windows)**.

**Проверь сразу:** загружен ли актуальный `docs_bundle.md`?  
Если нет — попроси вставить **секции**: `LOCAL_PLAN`, `BUGS`, `CHANGELOG` (и при необходимости `ROUTES_MAP`).

**Формат работы обязателен:**
- Готовые к вставке блоки кода с путём файла.
- Точно указывать «куда вставить» (после какой строки/блока).
- Обновлять **только** указанные разделы `docs_bundle.md` через Patch Grammar.

**Patch Grammar (пример):**
```
UPDATE:
- LOCAL_PLAN: отметить пункт X как выполненный.
- BUGS: добавить баг Y.
- CHANGELOG: добавить запись о фиксе Z.
```

**В конце сессии предложи:**
```
UPDATE SUMMARY:
- Sync Claude + ChatGPT context
- Update CHANGELOG and LOCAL_PLAN
```
(Это не командлет терминала; это просьба к ИИ обновить соответствующие разделы в `docs_bundle.md`.)
