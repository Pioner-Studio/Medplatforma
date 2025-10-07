#!/usr/bin/env python3
"""
Скрипт для исправления пустого блока if в main.py на строке 2459
"""

import os


def fix_empty_if_block():
    print("🔧 ИСПРАВЛЕНИЕ ПУСТОГО БЛОКА IF")
    print("=" * 40)

    main_py_path = "main.py"

    if not os.path.exists(main_py_path):
        print("❌ Файл main.py не найден!")
        return False

    # Читаем файл
    with open(main_py_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    print(f"📄 Обрабатываем файл: {len(lines)} строк")

    # Создаем резервную копию
    backup_path = main_py_path + ".backup_syntax"
    with open(backup_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"💾 Создана резервная копия: {backup_path}")

    # Исправляем проблемные строки
    fixed_lines = []

    for i, line in enumerate(lines):
        line_num = i + 1

        # Показываем область вокруг проблемы
        if 2455 <= line_num <= 2475:
            print(f"{line_num:4d}: {repr(line)}")

        # Исправляем строку 2459 - добавляем тело для if
        if line_num == 2459 and line.strip() == "if not kind or amount <= 0:":
            fixed_lines.append(line)
            # Добавляем тело if - возврат ошибки
            fixed_lines.append(
                '        return {"ok": False, "error": "Некорректные данные: вид операции и сумма обязательны"}\n'
            )
            print(f"✅ Исправлена строка {line_num}: добавлено тело для if")
            continue

        # Убираем пустые строки после if
        if line_num == 2460 and line.strip() == "":
            # Пропускаем пустую строку
            print(f"✅ Удалена пустая строка {line_num}")
            continue

        if line_num == 2461 and line.strip() == "":
            # Пропускаем еще одну пустую строку
            print(f"✅ Удалена пустая строка {line_num}")
            continue

        fixed_lines.append(line)

    # Сохраняем исправленный файл
    with open(main_py_path, "w", encoding="utf-8") as f:
        f.writelines(fixed_lines)

    print(f"\n✅ Файл исправлен!")
    return True


def verify_fix():
    """Проверка исправления"""
    print(f"\n🧪 ПРОВЕРКА ИСПРАВЛЕНИЯ")
    print("=" * 30)

    try:
        import ast

        with open("main.py", "r", encoding="utf-8") as f:
            content = f.read()

        # Пытаемся скомпилировать
        ast.parse(content)
        print("✅ Синтаксис корректен!")

        # Показываем исправленную область
        lines = content.split("\n")
        print("\n📝 Исправленная область:")
        for i in range(2458, 2468):
            if i < len(lines):
                print(f"{i+1:4d}: {lines[i]}")

        return True

    except SyntaxError as e:
        print(f"❌ Синтаксическая ошибка все еще есть:")
        print(f"   Строка {e.lineno}: {e.text.strip() if e.text else 'неизвестно'}")
        print(f"   Ошибка: {e.msg}")
        return False
    except Exception as e:
        print(f"❌ Ошибка при проверке: {e}")
        return False


def main():
    """Главная функция"""
    print("🔧 ИСПРАВЛЕНИЕ СИНТАКСИЧЕСКОЙ ОШИБКИ MAIN.PY")
    print("=" * 50)

    # 1. Исправляем пустой блок if
    if not fix_empty_if_block():
        print("❌ Не удалось исправить файл")
        return

    # 2. Проверяем результат
    if verify_fix():
        print("\n🚀 ИСПРАВЛЕНИЕ ЗАВЕРШЕНО!")
        print("\nТеперь можно запустить сервер:")
        print("python main.py")
        print("\nили")
        print("flask --app main run --no-reload")
    else:
        print("\n❌ Требуется дополнительное исправление")
        print("Проверьте вывод выше")


if __name__ == "__main__":
    main()
