#!/usr/bin/env python3
"""
Окончательное удаление дублированной функции doctors
"""

import os


def remove_duplicate_doctors_function():
    """Удаление дублированной функции doctors на строке 3721"""
    print("🔧 УДАЛЕНИЕ ДУБЛИРОВАННОЙ ФУНКЦИИ DOCTORS")
    print("=" * 45)

    main_py_path = "main.py"

    if not os.path.exists(main_py_path):
        print("❌ Файл main.py не найден!")
        return False

    # Читаем файл
    with open(main_py_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    print(f"📄 Обрабатываем файл: {len(lines)} строк")

    # Создаем резервную копию
    backup_path = main_py_path + ".backup_final"
    with open(backup_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"💾 Создана резервная копия: {backup_path}")

    # Ищем и удаляем дублированную функцию doctors начиная со строки ~3720
    new_lines = []
    skip_lines = False
    doctors_found = 0

    for i, line in enumerate(lines):
        line_num = i + 1

        # Проверяем, это ли строка с @app.route('/doctors')
        if "@app.route('/doctors')" in line or '@app.route("/doctors")' in line:
            doctors_found += 1
            print(f"📍 Найден маршрут doctors на строке {line_num}: {line.strip()}")

            # Если это второй раз, то начинаем пропускать
            if doctors_found > 1:
                print(f"❌ Удаляем дублированный маршрут doctors (строка {line_num})")
                skip_lines = True
                continue

        # Если мы пропускаем строки после второго @app.route('/doctors')
        if skip_lines:
            # Пропускаем до следующего @app.route или if __name__
            if (
                line.strip().startswith("@app.route") and "/doctors" not in line
            ) or "if __name__" in line:
                print(f"✅ Прекращаем пропускать на строке {line_num}: {line.strip()}")
                skip_lines = False
                new_lines.append(line)
            else:
                print(f"🗑️ Пропускаем строку {line_num}: {line.strip()[:50]}...")
                continue
        else:
            new_lines.append(line)

    # Сохраняем очищенный файл
    with open(main_py_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    removed_lines = len(lines) - len(new_lines)
    print(f"✅ Удалено {removed_lines} строк")
    print(f"📊 Было: {len(lines)} строк, стало: {len(new_lines)} строк")

    return True


def verify_no_duplicates():
    """Проверка отсутствия дубликатов"""
    print(f"\n🧪 ПРОВЕРКА ОТСУТСТВИЯ ДУБЛИКАТОВ")
    print("=" * 35)

    main_py_path = "main.py"

    with open(main_py_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Ищем все определения функции doctors
    doctors_count = content.count("def doctors(")
    doctors_routes = content.count("@app.route('/doctors')") + content.count(
        '@app.route("/doctors")'
    )

    print(f"📋 Найдено определений функции doctors: {doctors_count}")
    print(f"📋 Найдено маршрутов /doctors: {doctors_routes}")

    if doctors_count == 1 and doctors_routes == 1:
        print("✅ Дубликатов нет!")
        return True
    else:
        print("❌ Все еще есть дубликаты!")

        # Покажем где они находятся
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if "def doctors(" in line:
                print(f"   def doctors() на строке {i+1}: {line.strip()}")
            if "@app.route(" in line and "doctors" in line:
                print(f"   маршрут doctors на строке {i+1}: {line.strip()}")

        return False


def check_syntax():
    """Проверка синтаксиса"""
    print(f"\n🧪 ПРОВЕРКА СИНТАКСИСА")
    print("=" * 25)

    try:
        import ast

        with open("main.py", "r", encoding="utf-8") as f:
            content = f.read()

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
    print("🔧 ФИНАЛЬНОЕ ИСПРАВЛЕНИЕ ДУБЛИРОВАННОЙ ФУНКЦИИ DOCTORS")
    print("=" * 60)

    # 1. Удаляем дублированную функцию
    if not remove_duplicate_doctors_function():
        print("❌ Ошибка при удалении функции")
        return

    # 2. Проверяем отсутствие дубликатов
    if not verify_no_duplicates():
        print("❌ Дубликаты все еще присутствуют")
        return

    # 3. Проверяем синтаксис
    if not check_syntax():
        print("❌ Проблемы с синтаксисом")
        return

    print("\n🎉 ПРОБЛЕМА ПОЛНОСТЬЮ РЕШЕНА!")
    print("\n🚀 Теперь можно запустить сервер:")
    print("python main.py")
    print("\nПосле запуска все ссылки в левом меню должны работать:")
    print("- Расписание")
    print("- Пациенты")
    print("- Врачи")
    print("- Услуги")
    print("- Кабинеты")
    print("- Финансы")


if __name__ == "__main__":
    main()
