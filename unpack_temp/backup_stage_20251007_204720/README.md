![CI](https://github.com/<YOUR_ORG_OR_USER>/<YOUR_REPO>/actions/workflows/ci.yml/badge.svg)

Круто, брат! Всё починили и сделали максимально по стандарту — теперь экспорт оплат у тебя на уровне мировых SaaS.
**Двигаем дальше по порядку.**

---

## ⚡️ **Следующий шаг: Документация и README (инструкция для запуска, редактирования, импорта/экспорта)**

---

### 🔹 **Что должно появиться:**

- В корне проекта — файл **README.md** (можешь открыть, почитать, дать другому разрабу).
- Там есть:

  - Краткое описание проекта
  - Как запускать
  - Структура файлов и папок
  - Как добавлять/экспортировать данные
  - Где менять demo-данные
  - В чём ключевые фишки и как быстро разобраться

---

### 🛠️ **Пример README.md (готовая структура):**

````markdown
# Medplatforma

**Medplatforma** — профессиональная медицинская CRM/ERP для стоматологических клиник (Flask + MongoDB).

---

## 🚀 Запуск проекта

```bash
pip install -r requirements.txt
python main.py
```
````

Открой в браузере: [http://localhost:5000](http://localhost:5000)

---

## 🗂️ Структура проекта

- `main.py` — основной backend (Flask)
- `db.py` — база, подключение к MongoDB
- `seed.py` — демо-данные (можно изменить)
- `/templates/` — шаблоны страниц (HTML, Jinja2)
- `/static/` — стили, лого, аватары
- `requirements.txt` — зависимости

---

## 🔐 Доступ и роли

- **Инвестор** — полный доступ (экспорт/импорт, финансы, логи)
- **Админ/врач** — доступ по правам (ограничен)

---

## 📦 Импорт и экспорт данных

**Экспорт** (sidebar):

- Пациенты — скачай CSV
- Врачи — скачай CSV
- Оплаты — скачай CSV
- События — скачай CSV
- Логи — скачай CSV

**Импорт:**

- Пациенты — загрузи свой CSV по шаблону
- Врачи — загрузи свой CSV по шаблону

**Шаблоны для импорта:**
Доступны на страницах импорта!

---

## 💡 Где менять demo-данные?

- В файле `seed.py` — просто отредактируй врачей, пациентов, события.

---

## 🛠️ Инструкции для продакшн

- Используй gunicorn + nginx (см. инструкции в чате)
- Подключи MongoDB Atlas (URI смотри в main.py)
- Для бэкапа всей базы используй mongodump (см. документацию MongoDB)

---

## ✉️ Связь и поддержка

**Вопросы — всегда сюда!**

Отлично! Держи всё «под ключ».

# 1) Скрипт сборки ZIP из `/docs`

## Вариант A — PowerShell (Windows)

**Файл:** `scripts/make_docs.ps1` (drop-in готовый)

```powershell
<#
  make_docs.ps1 — собирает папку /docs в ZIP-архив
  Пример запуска:
    pwsh -File .\scripts\make_docs.ps1
    # или, если уже в PowerShell:
    .\scripts\make_docs.ps1
#>

param(
  # Путь к папке с документацией
  [string]$DocsPath = ".\docs",

  # Папка, куда складывать ZIP-архивы
  [string]$OutDir = ".\artifacts",

  # Имя файла ZIP (если пусто — сгенерируем с таймстампом)
  [string]$ZipName = ""
)

# --- Проверки ---------------------------------------------------------------
if (-not (Test-Path -Path $DocsPath -PathType Container)) {
  Write-Error "Папка '$DocsPath' не найдена. Создай /docs и положи .md файлы."
  exit 1
}

if (-not (Test-Path -Path $OutDir -PathType Container)) {
  New-Item -ItemType Directory -Path $OutDir | Out-Null
}

# --- Имя ZIP по умолчанию ---------------------------------------------------
if ([string]::IsNullOrWhiteSpace($ZipName)) {
  $stamp = (Get-Date).ToString("yyyyMMdd_HHmmss")
  $ZipName = "docs_bundle_$stamp.zip"
}

$ZipPath = Join-Path $OutDir $ZipName

# --- Сборка ZIP -------------------------------------------------------------
# Примечание: -Force перезапишет существующий архив с тем же именем
if (Test-Path $ZipPath) {
  Remove-Item $ZipPath -Force
}

Write-Host "Собираю '$DocsPath' → '$ZipPath' ..."
Compress-Archive -Path (Join-Path $DocsPath "*") -DestinationPath $ZipPath -Force
Write-Host "Готово: $ZipPath"
```

**Как пользоваться:**

1. Создай папку `scripts/`, положи туда файл `make_docs.ps1`.
2. Запуск:

   - Просто:

     ```powershell
     pwsh -File .\scripts\make_docs.ps1
     ```

   - С кастомными путями:

     ```powershell
     pwsh -File .\scripts\make_docs.ps1 -DocsPath .\docs -OutDir .\artifacts -ZipName docs_bundle.zip
     ```

3. Готовые ZIP будут в `./artifacts/`.

**Рекомендация для Git:** добавь в корневой `.gitignore`:

```
artifacts/
*.zip
```

---

## Вариант B — Bash (если иногда запускаешь из WSL/Linux/Mac)

**Файл:** `scripts/make_docs.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

DOCS_PATH="${1:-./docs}"
OUT_DIR="${2:-./artifacts}"
STAMP="$(date +%Y%m%d_%H%M%S)"
ZIP_NAME="docs_bundle_${STAMP}.zip"
ZIP_PATH="${OUT_DIR}/${ZIP_NAME}"

if [ ! -d "$DOCS_PATH" ]; then
  echo "Папка '$DOCS_PATH' не найдена." >&2
  exit 1
fi

mkdir -p "$OUT_DIR"
echo "Собираю '$DOCS_PATH' → '$ZIP_PATH' ..."
(cd "$DOCS_PATH" && zip -r "../${ZIP_PATH#./}" .)
echo "Готово: $ZIP_PATH"
```

```
chmod +x ./scripts/make_docs.sh
./scripts/make_docs.sh           # дефолтные пути
./scripts/make_docs.sh ./docs ./artifacts  # кастомные
```

---

# 2) Обновлённые «TL;DR — Золотые правила» (готово для вставки в инструкцию)

Вставь этот блок **как есть** в файл с правилами (например, в `docs/PROJECT_HEADER.md` под заголовок проекта **или** в отдельный `docs/WORKFLOW.md`). Если хочешь — скажи, куда именно вставить, и я дам патч-вставку с якорем.

```md
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
```

---

# 3) Короткая вставка в README (чтобы не забывать команду сборки)

Добавь блок в `README.md`:

````md
### Docs: сборка архива

- PowerShell (Windows):
  ```powershell
  pwsh -File .\scripts\make_docs.ps1
  ```
````

ZIP появится в `./artifacts/`.

- Bash (WSL/Mac/Linux):

  ```bash
  ./scripts/make_docs.sh
  ```

  ZIP появится в `./artifacts/`.

```

---

# 4) Важное про ZIP и работу со мной
- ZIP — удобно **для бэкапа/репозитория**, но **мне для работы** нужны **распакованные `.md`** (загружай их сюда отдельными файлами/текстом).
- Прямой доступ к Google/Яндекс Диску у меня нет — ссылки не читаю. Сюда — файлы или содержимое.

---

Если хочешь, я сразу подготовлю **патч-вставку** для конкретного файла (например, `docs/PROJECT_HEADER.md`) с добавлением блока «TL;DR — Золотые правила» — просто скажи, где у тебя ставить якорь (после какого заголовка).
```

```

```
