# tools/dump_routes.py
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from datetime import datetime

# --- импортируем приложение ---
# если твой входной модуль называется "main.py" и в нём создан app = Flask(__name__)
from main import app

OUT_DIR = os.path.join("docs")
os.makedirs(OUT_DIR, exist_ok=True)
out_md = os.path.join(OUT_DIR, "ROUTES.md")

with app.app_context():
    rules = sorted(app.url_map.iter_rules(), key=lambda r: r.rule)

lines = []
lines.append(f"# Flask routes map\n")
lines.append(f"_generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_\n")
lines.append("| Rule | Endpoint | Methods |")
lines.append("|------|----------|---------|")

for r in rules:
    methods = ",".join(sorted(m for m in r.methods if m not in {"HEAD", "OPTIONS"}))
    lines.append(f"| `{r.rule}` | `{r.endpoint}` | `{methods}` |")

# детальный блок с одним правилом на абзац (удобно глазами искать)
lines.append("\n---\n")
for r in rules:
    methods = ",".join(sorted(m for m in r.methods if m not in {"HEAD", "OPTIONS"}))
    lines.append(f"### `{r.rule}`")
    lines.append(f"- endpoint: `{r.endpoint}`")
    lines.append(f"- methods: `{methods}`\n")

with open(out_md, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"[OK] routes dumped to {out_md}")
