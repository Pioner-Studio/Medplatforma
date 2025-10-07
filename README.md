# Medplatforma

A production‑grade dental clinic web app built with **Flask + MongoDB + Jinja2 + FullCalendar**.

> This README describes how to run the project locally, our quality gates (pre‑commit), the architecture map workflow, and the minimal routes/templates set we keep in the repo going forward.

---

## 1) Quick start (Windows / PowerShell)

```powershell
git clone <YOUR_REPO_URL> medplatforma
cd medplatforma

python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Run dev server
flask --app main run --no-reload
# App: http://127.0.0.1:5000/
```

If `FLASK_DEBUG` or env variables are needed, create a local `.env` (not committed) and load it in `main.py` or via your shell profile.

---

## 2) Project layout (kept & supported)

```
medplatforma/
│
├─ main.py                          # main Flask app (routes, views)
├─ routes_finance.py                # finance module (cashboxes, operations, reports)
├─ routes_schedule.py               # schedule module & calendar endpoints
├─ production_auth.py               # login/logout, current user, change password
├─ static/
│   └─ js/
│       └─ calendar_init.js         # FullCalendar init & handlers (eventClick etc.)
├─ templates/                       # Jinja2 templates
│   ├─ calendar.html
│   ├─ patient_card.html
│   ├─ finance/*.html
│   ├─ schedule/*.html
│   └─ ... (doctors.html, rooms.html, services.html, etc.)
├─ docs/
│   ├─ docs_bundle.md               # operational SSOT (update only requested blocks)
│   ├─ roadmap_master.md            # long‑term strategy (3–12 months)
│   ├─ ARCH_MAP.md                  # routes/templates map (+ status verified/pending)
│   ├─ ARCH_VERIFY.md               # how to run the map verifier
│   ├─ DENTAL_CHART_SPEC.md         # interactive dental chart spec
│   └─ CLAUDE_MIGRATION_NOTES.md    # calendar migration notes & hotfix plan
├─ arch_verify.py                   # fast scanner: routes/templates/JS calls → routes.json
├─ update_routes.py                 # helper to sync ARCH_MAP.md from routes.json
├─ .gitattributes                   # normalized line endings, LF/CRLF policy
├─ .pre-commit-config.yaml          # formatters/linters/hooks
└─ requirements.txt
```

> Everything not listed above is considered **temporary** or **legacy**. See *Repository cleanup* below.

---

## 3) Quality gates (mandatory)

### 3.1 Pre‑commit
Install and run before committing:
```powershell
pre-commit install
pre-commit run --all-files
```

Typical hooks we run:
- Python formatting (e.g., black/isort/ruff if configured)
- LF/CRLF normalization (via `.gitattributes`)
- Docs sync check (optional): ensure `ARCH_MAP.md` is up to date

### 3.2 Architecture map verification
Keep routes/templates in sync with the docs:
```powershell
python arch_verify.py --root . --out routes.json
# then update docs:
git add routes.json docs/ARCH_MAP.md
git commit -m "chore(arch): sync routes map"
```

---

## 4) Calendar — required JS handlers

Make sure `static/js/calendar_init.js` defines (and is loaded on calendar page):
```js
function openStatusModal(event) { /* open modal and fill fields */ }
function viewDetails(event)     { /* go to /patients/<id> */ }
function repeatAppointment(event){ /* prefill and create next visit */ }
function refetchEvents()        { /* calendar.refetchEvents() after POST */ }
```

**Backend** must supply `extendedProps` for events (`patient_id`, `doctor_id`, `service_id`, `status`), and the `eventClick` handler should call `openStatusModal(info.event)`.

---

## 5) Minimal acceptance tests (smoke)

- `/schedule` (or `/calendar`) renders events; click opens modal; “Details” goes to `/patients/<id>`.
- Completing a visit posts to `/appointments/<id>/complete` and refreshes events.
- `/finance` shows operations; deleting a manual op creates a reversal entry.
- `/chief/pending-plans` lists plans; approving changes status and permits booking.
- Dental chart API responds: `GET /api/patients/<id>/dental-chart`.

---

## 6) Repository cleanup (one‑time maintenance)

**Goal:** keep only production code & docs, remove one‑off scripts and backups.

### 6.1 KEEP list (examples)
- `main.py`, `routes_*.py`, `production_auth.py`
- `templates/**` (only pages actually used in nav and flows)
- `static/js/calendar_init.js`, bundled assets
- `docs/**` (files from this README’s layout)
- `arch_verify.py`, `update_routes.py`, `.pre-commit-config.yaml`, `.gitattributes`, `requirements.txt`

### 6.2 REMOVE patterns (examples)
- Backups & temp:
  - `**/*backup*.*`, `**/backups/**`, `**/*_bak.*`, `**/*_old.*`, `**/*_tmp.*`, `**/*.tmp`
  - `**/*scratch*.*`, `**/*playground*.*`
- Ad‑hoc fix scripts that are already merged:
  - `**/*fix*.*`, `**/*patch*.*`, `**/debug_*.*`, `**/test_*.*`
- Duplicated mains/routers:
  - `**/main_clean.py`, `**/main_backup_*.py`, `**/*routes*_copy*.*`
- Demo/seed once‑off (if not part of production init):
  - `**/seed*.py` (except the single canonical seeder if you keep one)
- Artifact files:
  - `routes.json` (keep tracked, but regenerate), logs, `.DS_Store`, `Thumbs.db`

> Carefully review deletions. If unsure, move candidates to `attic/` first, commit, then remove after a week.

### 6.3 PowerShell helper (save as `tools/cleanup_project.ps1`)
```powershell
Param(
  [switch]$DryRun = $true
)

$patterns = @(
  '*backup*.*','*_*backup*.*','*_bak.*','*_old.*','*_tmp.*','*.tmp',
  '*scratch*.*','*playground*.*',
  '*fix*.*','*patch*.*','debug_*.*','test_*.*',
  'main_clean.py','main_backup_*.py','*routes*_copy*.*',
  'seed*.py'
)

$keepRoots = @('templates','static','docs')
$keepFiles = @(
  'main.py','routes_schedule.py','routes_finance.py','routes_transfer.py',
  'production_auth.py','arch_verify.py','update_routes.py',
  '.pre-commit-config.yaml','.gitattributes','requirements.txt','README.md'
)

Write-Host "=== DRY RUN:" $DryRun
Get-ChildItem -Recurse | ForEach-Object {
  $path = $_.FullName
  $name = $_.Name

  # Keep folders
  foreach($k in $keepRoots){ if($path -match "\\$k(\\|$)") { return } }
  # Keep key files
  if($keepFiles -contains $name){ return }

  $match = $false
  foreach($p in $patterns){
    if($name -like $p){ $match = $true; break }
  }

  if($match){
    if($DryRun){ Write-Host "[would remove]" $path }
    else { Remove-Item -Force $path }
  }
}
```

Run:
```powershell
# Preview
powershell -ExecutionPolicy Bypass -File tools/cleanup_project.ps1 -DryRun

# Actual delete
powershell -ExecutionPolicy Bypass -File tools/cleanup_project.ps1 -DryRun:$false
```

---

## 7) Branching & PR rules

- `main` = stable; `dev` = integration; feature branches `feature/<scope>`.
- Any route/template change ⇒ run `arch_verify.py`, update `ARCH_MAP.md`, include `routes.json` in PR.
- PR checklist: pre‑commit clean; routes map synced; README untouched except doc changes.

---

## 8) Troubleshooting

- **Calendar click does nothing** → ensure `openStatusModal()` is defined and `calendar_init.js` is loaded once; check for stray `}}` in template.
- **Events miss patient_id** → backend `/api/events` must return `extendedProps`.
- **Stale JS/CSS** → add cache‑busting query param: `?v={{ BUILD_ID }}`.
- **Role/visibility issues** → confirm role middleware and menu guards.

---

## 9) License

Private / internal use for the Medplatforma clinic project.
