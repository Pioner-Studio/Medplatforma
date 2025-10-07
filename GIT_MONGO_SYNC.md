# GIT_MONGO_SYNC.md — Инструкция по работе на 3 ПК (GitHub + MongoDB Atlas)
_Обновлено: 2025-10-07 06:35_

## 🎯 Цель
Безопасно работать над проектом **Medplatforma** на трёх компьютерах, не затирая изменения.
Код хранится в **GitHub**, данные — в **MongoDB Atlas**.

---

## 1) Предварительные требования
- Аккаунт GitHub, доступ к репозиторию `medplatforma`.
- Установлены Git и VS Code на всех ПК.
- Доступ к кластеру MongoDB Atlas и **одинаковая строка подключения** на всех ПК.
- Файл `.env` **не коммитится** в Git (добавить в `.gitignore`).

Пример `.env` (каждый ПК хранит локально):
```
FLASK_ENV=development
MONGO_URI=mongodb+srv://medadmin:medpass123@medplatforma.cnv7fbo.mongodb.net/
DB_NAME=medplatforma_dev
```

---

## 2) Первичная настройка Git на ПК
```powershell
git config --global user.name "Ваше Имя"
git config --global user.email your@email.com
git config --global pull.ff only      # запрещаем merge-ветки при pull
git config --global core.autocrlf true
```

Клонирование:
```powershell
git clone https://github.com/<ваш_аккаунт>/medplatforma.git
cd medplatforma
```

---

## 3) Базовый рабочий цикл (один ПК)
**Перед началом работы:**
```powershell
git fetch origin
git status
git pull --ff-only
```

**Работаете, тестируете…**  
**Сохранение:**
```powershell
git add .
git commit -m "Фикс календаря: ресурсная ось, dragend"
git push origin main
```

> `--ff-only` гарантирует, что вы не создадите «лишний merge». Если ветка разошлась — команда прервётся, и вы не перезапишете чужие изменения.

---

## 4) Переход с ПК‑1 на ПК‑2 (как не затереть код)
**На ПК‑1 (перед уходом):**
```powershell
git add .
git commit -m "Завершил часть задач D0"
git push origin main
```
**На ПК‑2 (перед началом):**
```powershell
git fetch origin
git status
git pull --ff-only
```
Теперь у вас самая свежая версия. Работайте и пушьте изменения.

**Никогда не начинайте на ПК‑2 без `git pull --ff-only`** — так вы избежите перезаписи новой версии старым кодом.

---

## 5) Ветки (безопаснее, чем прямо в main)
Рекомендуемый подход — делать работу в фиче‑ветках:
```powershell
git switch -c feature/cal-resource-view
# ... правки ...
git add .
git commit -m "resource view: кабинеты по оси"
git push -u origin feature/cal-resource-view
```
Затем создайте Pull Request в GitHub и смержьте через веб‑интерфейс.  
На другом ПК просто:
```powershell
git fetch origin
git switch feature/cal-resource-view
git pull --ff-only
```

---

## 6) Проверка расхождений и конфликты
Посмотреть историю компактно:
```powershell
git log --oneline --graph --decorate --all -n 20
```
Сравнить локальную и удалённую ветку:
```powershell
git rev-list --left-right --count origin/main...HEAD
```
Если конфликт при pull — VS Code покажет «Current/Incoming». Выберите нужные блоки, сохраните, затем:
```powershell
git add .
git commit -m "Resolve merge conflict"
git push origin main
```

**Никогда не используйте `--force` без крайней необходимости.**  
Если запутались:
```powershell
git reset --hard origin/main
git clean -fd
```
(Предупреждение: команда удалит локальные неотслеживаемые файлы.)

---

## 7) MongoDB Atlas (единая база для всех ПК)
- Используйте **один и тот же кластер** и пользователя.
- В Atlas в разделе **Network Access** добавьте IP всех трёх ПК или временно `0.0.0.0/0` (небезопасно).
- Желательно разделить базы: `medplatforma_dev` и `medplatforma_prod`.
- Пара индексов (пример):
```javascript
db.events.createIndex({ room_id: 1, start: 1, end: 1 })
db.patients.createIndex({ phone: 1 })
```
- Бэкапы (по желанию):
```powershell
mongodump --uri "%MONGO_URI%" --db medplatforma_dev --out backups/mongodump_%DATE%
```

---

## 8) Частые ошибки и как избежать
- **Затёр старым кодом новую версию:** всегда делайте `git pull --ff-only` перед началом.
- **Коммитнул секреты:** держите `.env` вне Git, добавьте в `.gitignore`.
- **Разные версии зависимостей:** фиксируйте `requirements.txt`, запускайте
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## 9) Чек‑лист перед выключением ПК
- `git status` — чисто?
- `git add . && git commit` — изменения сохранены?
- `git push origin <ветка>` — выгружено в GitHub?
- `docs_bundle.md` — обновлены `LOCAL_PLAN`/`CHANGELOG`?
- Бэкап `main.py` и `calendar.html` создан?

Готово. На другом ПК начинаем с `git pull --ff-only`.
