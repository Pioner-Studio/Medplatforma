# quick_fix_ui.py
from pathlib import Path
import re, shutil

ROOT = Path(__file__).parent


def patch_file(path, repls):
    text = path.read_text(encoding="utf-8")
    bak = path.with_suffix(path.suffix + ".bak")
    bak.write_text(text, encoding="utf-8")
    for pattern, replacement, flags in repls:
        text = re.sub(pattern, replacement, text, flags=flags)
    path.write_text(text, encoding="utf-8")
    print(f"[fix] {path.name} (backup: {bak.name})")


# --- base.html ---
base = ROOT / "templates" / "base.html"
if base.exists():
    txt = base.read_text(encoding="utf-8")

    # 1) заменить нижний блок на безопасный (по ключу 'Переключение темы')
    safe_block = """
<script>
// Меню профиля (safe)
(function(){
  const toggle = () => {
    const menu = document.getElementById('profileMenu');
    if (!menu) return;
    menu.style.display = (menu.style.display === 'flex' ? 'none' : 'flex');
  };
  window.toggleProfileMenu = toggle;
  window.addEventListener('click', (e) => {
    const menu = document.getElementById('profileMenu');
    if (!menu) return;
    if (!e.target.closest('.profile-block') && !e.target.closest('.profile-menu')) {
      menu.style.display = 'none';
    }
  });
})();
document.addEventListener('DOMContentLoaded', function() {
  const themeBtn = document.getElementById('themeToggleBtn');
  if (!themeBtn) return;
  const sunIcon = document.querySelector('.theme-sun');
  const moonIcon = document.querySelector('.theme-moon');
  if (localStorage.getItem('theme') === 'dark') {
    document.body.classList.add('dark-theme');
    if (sunIcon)  sunIcon.style.display = 'none';
    if (moonIcon) moonIcon.style.display = 'inline';
  }
  themeBtn.addEventListener('click', function() {
    const dark = document.body.classList.toggle('dark-theme');
    if (sunIcon)  sunIcon.style.display  = dark ? 'none'   : 'inline';
    if (moonIcon) moonIcon.style.display = dark ? 'inline' : 'none';
    localStorage.setItem('theme', dark ? 'dark' : 'light');
  });
});
</script>
""".strip()

    # грубо: заменим второй сценарный блок от комментария до </script>
    txt = re.sub(
        r"(?s)<script>\s*function toggleProfileMenu\([\s\S]*?</script>", safe_block, txt, count=1
    )
    # убрать двойные закрывающие теги
    txt = re.sub(r"(</body>\s*</html>)(\s*</body>\s*</html>\s*)$", r"\1", txt)
    base.with_suffix(".html.patched").write_text(txt, encoding="utf-8")
    base.write_text(txt, encoding="utf-8")
    print("[fix] base.html patched")

# --- production_auth.py ---
auth = ROOT / "production_auth.py"
if auth.exists():
    text = auth.read_text(encoding="utf-8")
    bak = auth.with_suffix(".py.bak")
    bak.write_text(text, encoding="utf-8")

    # default avatar -> default.png
    text = re.sub(
        r'("avatar"\s*:\s*user\.get\(\s*[\'"]avatar[\'"]\s*\)\s*or\s*)[\'"]default\.jpg[\'"]',
        r'\1"default.png"',
        text,
    )
    auth.write_text(text, encoding="utf-8")
    print("[fix] production_auth.py default avatar -> default.png")

# --- remove investor avatar file ---
ava = ROOT / "static" / "avatars" / "investor_avatar.png"
if ava.exists():
    ava.unlink()
    print("[rm] static/avatars/investor_avatar.png removed")

print("DONE. Перезапусти Flask и Ctrl+F5 страницу пациента.")
