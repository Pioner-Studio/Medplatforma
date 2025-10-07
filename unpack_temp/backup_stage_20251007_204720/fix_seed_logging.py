# fix_seed_logging.py
# Делает 3 вещи в main.py:
#  1) меняет print("[init] ensure_rooms: done") -> app.logger.debug(...)
#  2) добавляет app.config.setdefault("SEED_ON_STARTUP", False) если нет
#  3) оборачивает прямой вызов ensure_rooms() в if app.config.get("SEED_ON_STARTUP", True):

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
mp = ROOT / "main.py"
assert mp.exists(), "main.py не найден рядом со скриптом"

src = mp.read_text(encoding="utf-8")
mp.with_suffix(".py.bak").write_text(src, encoding="utf-8")

changed = False

# 1) print -> app.logger.debug
src2 = re.sub(
    r"""(?m)^\s*print\(\s*["']\s*\[init\]\s*ensure_rooms:\s*done\s*["']\s*\)\s*$""",
    'from flask import current_app as app\napp.logger.debug("[init] ensure_rooms: done")',
    src,
)
if src2 != src:
    changed = True
    src = src2

# 2) ensure есть setdefault флагов в конфиге
# Вставим сразу после первой инициализации app = Flask(__name__)
pattern_app = re.compile(r"(?m)^(?P<prefix>\s*app\s*=\s*Flask\([^\n]*\)\s*\n)")
if not re.search(r"SEED_ON_STARTUP", src):

    def repl_app(m):
        return m.group("prefix") + 'app.config.setdefault("SEED_ON_STARTUP", False)\n'

    src2 = pattern_app.sub(repl_app, src, count=1)
    if src2 != src:
        changed = True
        src = src2

# 3) обернуть вызов ensure_rooms() флагом
# Варианты: ensure_rooms(), seed.ensure_rooms(), ensure_rooms(db) — завернём строки, где это на отдельной строке как вызов
call_pattern = re.compile(r"(?m)^\s*(?P<call>(?:\w+\.)?ensure_rooms\s*\([^)]*\)\s*)$")
if re.search(call_pattern, src):

    def wrap_call(m):
        indent = re.match(r"^\s*", m.group(0)).group(0)
        call = m.group("call").strip()
        wrapped = (
            f'{indent}if app.config.get("SEED_ON_STARTUP", True):\n'
            f"{indent}    try:\n"
            f"{indent}        {call}\n"
            f"{indent}    except Exception as e:\n"
            f"{indent}        from flask import current_app as app\n"
            f'{indent}        app.logger.exception("ensure_rooms failed: %s", e)\n'
        )
        return wrapped

    src2 = re.sub(call_pattern, wrap_call, src, count=1)
    if src2 != src:
        changed = True
        src = src2

if changed:
    mp.write_text(src, encoding="utf-8")
    print("[fix] main.py patched (backup: main.py.bak)")
else:
    print("[info] main.py уже в порядке — изменений не потребовалось.")
