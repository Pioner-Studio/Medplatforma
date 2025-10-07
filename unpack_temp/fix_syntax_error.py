#!/usr/bin/env python3
"""
Скрипт для исправления синтаксической ошибки в main.py
"""

import os
import re


def fix_syntax_error():
    print("🔧 ИСПРАВЛЕНИЕ СИНТАКСИЧЕСКОЙ ОШИБКИ")
    print("=" * 50)

    main_py_path = "main.py"

    if not os.path.exists(main_py_path):
        print("❌ Файл main.py не найден!")
        return False

    # Читаем файл
    with open(main_py_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    print(f"📄 Читаем файл: {len(lines)} строк")

    # Ищем проблемную область вокруг строки 2463
    error_line = 2463
    start_line = max(0, error_line - 10)
    end_line = min(len(lines), error_line + 10)

    print(f"\n🔍 Анализируем строки {start_line}-{end_line}:")

    fixed_lines = []
    issues_fixed = 0

    for i, line in enumerate(lines):
        line_num = i + 1

        # Показываем проблемную область
        if start_line <= line_num <= end_line:
            print(f"{line_num:4d}: {repr(line)}")

        # Исправляем типичные проблемы с отступами
        if line_num == error_line:
            # Проверяем, есть ли правильный отступ
            if line.strip().startswith('if kind == "payment"'):
                # Если строка не имеет отступа, добавляем его
                if not line.startswith("    "):
                    line = "    " + line.lstrip()
                    issues_fixed += 1
                    print(f"✅ Исправлен отступ в строке {line_num}")

        # Проверяем следующую строку после if
        if line_num == error_line + 1:
            if line.strip() and not line.startswith("        "):
                # Добавляем отступ для тела if
                line = "        " + line.lstrip()
                issues_fixed += 1
                print(f"✅ Исправлен отступ в строке {line_num}")

        # Исправляем пустые блоки if/for/while
        if line.strip().endswith(":") and line_num < len(lines):
            next_line = lines[i + 1] if i + 1 < len(lines) else ""
            # Если после двоеточия нет отступа или пустая строка
            if not next_line.strip() or not next_line.startswith("    "):
                # Добавляем pass или правильный отступ
                if line_num == error_line - 1:
                    fixed_lines.append(line)
                    fixed_lines.append("    pass  # TODO: добавить логику\n")
                    issues_fixed += 1
                    print(f"✅ Добавлен pass в строке {line_num + 1}")
                    continue

        fixed_lines.append(line)

    # Дополнительные проверки и исправления
    print(f"\n🔧 Применяем дополнительные исправления...")

    content = "".join(fixed_lines)

    # Исправляем общие проблемы с отступами
    fixes = [
        # Исправляем if без тела
        (r"if (.+):\s*\n(\s*)if ", r"if \1:\n\2    pass\n\2if "),
        # Исправляем пустые функции
        (r"def (.+):\s*\n(\s*)def ", r"def \1:\n\2    pass\n\2def "),
        # Исправляем пустые классы
        (r"class (.+):\s*\n(\s*)class ", r"class \1:\n\2    pass\n\2class "),
    ]

    for pattern, replacement in fixes:
        old_content = content
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        if content != old_content:
            issues_fixed += 1
            print(f"✅ Применено исправление: {pattern[:30]}...")

    # Сохраняем исправленный файл
    if issues_fixed > 0:
        # Создаем резервную копию
        backup_path = main_py_path + ".backup"
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write("".join(lines))
        print(f"💾 Создана резервная копия: {backup_path}")

        # Сохраняем исправленный файл
        with open(main_py_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"✅ Файл исправлен! Применено {issues_fixed} исправлений")
    else:
        print("ℹ️ Исправления не требуются")

    return True


def check_syntax():
    """Проверка синтаксиса Python файла"""
    print(f"\n🧪 ПРОВЕРКА СИНТАКСИСА")
    print("=" * 30)

    try:
        import ast

        with open("main.py", "r", encoding="utf-8") as f:
            content = f.read()

        # Пытаемся скомпилировать
        ast.parse(content)
        print("✅ Синтаксис корректен!")
        return True

    except SyntaxError as e:
        print(f"❌ Синтаксическая ошибка:")
        print(f"   Строка {e.lineno}: {e.text.strip() if e.text else 'неизвестно'}")
        print(f"   Ошибка: {e.msg}")
        return False
    except Exception as e:
        print(f"❌ Ошибка при проверке: {e}")
        return False


def main():
    """Главная функция"""
    print("🔧 ИСПРАВЛЕНИЕ MAIN.PY")
    print("=" * 40)

    # 1. Исправляем синтаксические ошибки
    if not fix_syntax_error():
        print("❌ Не удалось исправить ошибки")
        return

    # 2. Проверяем синтаксис
    if check_syntax():
        print("\n🚀 ГОТОВО К ЗАПУСКУ!")
        print("Теперь можно запустить сервер:")
        print("python main.py")
        print("или")
        print("flask --app main run --no-reload")
    else:
        print("\n⚠️ ТРЕБУЕТСЯ РУЧНОЕ ИСПРАВЛЕНИЕ")
        print("Проверьте ошибки выше и исправьте их вручно")


if __name__ == "__main__":
    main()
