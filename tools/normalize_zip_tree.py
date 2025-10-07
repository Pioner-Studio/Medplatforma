# tools/normalize_zip_tree.py
# Превращает файлы вида "templates\finance\add.html" в настоящие папки templates/finance/add.html

from pathlib import Path
import shutil

root = Path(".").resolve()  # текущая папка
moved = 0

for p in list(root.rglob("*")):
    if p.is_file() and ("\\" in p.name):
        parts = p.name.split("\\")
        target_dir = p.parent / "/".join(parts[:-1])
        target_dir.mkdir(parents=True, exist_ok=True)
        target_file = target_dir / parts[-1]
        print(f"Fix: {p}  ->  {target_file}")
        shutil.move(str(p), str(target_file))
        moved += 1

print(f"Converted files: {moved}")
