# fix_auth_urls.py
# Запустите этот скрипт в корне проекта для исправления всех ссылок

import os
import re


def fix_auth_urls():
    """Исправляет все url_for('login') и url_for('logout') на auth.login и auth.logout"""

    templates_dir = "templates"
    fixed_files = []

    # Паттерны для поиска и замены
    replacements = [
        (r"url_for\(['\"]logout['\"]\)", "url_for('auth.logout')"),
        (r"url_for\(['\"]login['\"]\)", "url_for('auth.login')"),
    ]

    # Проходим по всем HTML файлам в templates
    for root, dirs, files in os.walk(templates_dir):
        for filename in files:
            if filename.endswith(".html"):
                filepath = os.path.join(root, filename)

                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()

                original_content = content

                # Применяем все замены
                for pattern, replacement in replacements:
                    content = re.sub(pattern, replacement, content)

                # Если файл изменился, сохраняем
                if content != original_content:
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(content)
                    fixed_files.append(filepath)
                    print(f"✅ Исправлен: {filepath}")

    if fixed_files:
        print(f"\n✨ Исправлено файлов: {len(fixed_files)}")
    else:
        print("✨ Все файлы уже корректны!")

    return fixed_files


if __name__ == "__main__":
    print("🔧 Исправляем auth URL в шаблонах...")
    fix_auth_urls()
    print("\n✅ Готово! Теперь перезапустите приложение.")
