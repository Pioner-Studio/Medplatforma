#!/usr/bin/env python3
"""
Скрипт для поиска и удаления дублирующей функции doctors
"""

import os
import re


def find_doctors_functions():
    """Поиск всех определений функции doctors"""
    print("🔍 ПОИСК ФУНКЦИЙ DOCTORS")
    print("=" * 30)

    main_py_path = "main.py"

    if not os.path.exists(main_py_path):
        print("❌ Файл main.py не найден!")
        return False

    # Читаем файл
    with open(main_py_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Ищем все определения функции doctors
    doctors_functions = []

    for i, line in enumerate(lines):
        if "def doctors(" in line:
            # Найдем начало функции (маршрут)
            route_line = None
            for j in range(max(0, i - 5), i):
                if "@app.route(" in lines[j] and "/doctors" in lines[j]:
                    route_line = j
                    break

            doctors_functions.append(
                {
                    "route_line": route_line,
                    "def_line": i,
                    "route_text": lines[route_line].strip() if route_line else "Не найден",
                    "def_text": line.strip(),
                }
            )

    print(f"📋 Найдено {len(doctors_functions)} определений функции doctors:")
    for idx, func in enumerate(doctors_functions):
        print(f"\n   {idx + 1}. Строка {func['def_line'] + 1}:")
        print(f"      Маршрут: {func['route_text']}")
        print(f"      Функция: {func['def_text']}")

    return doctors_functions


def remove_duplicate_doctors():
    """Удаление дублированных функций doctors"""
    print(f"\n🔧 УДАЛЕНИЕ ДУБЛИРОВАННОЙ ФУНКЦИИ DOCTORS")
    print("=" * 45)

    main_py_path = "main.py"

    # Читаем файл
    with open(main_py_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Создаем резервную копию
    backup_path = main_py_path + ".backup_doctors"
    with open(backup_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"💾 Создана резервная копия: {backup_path}")

    # Ищем все блоки с функцией doctors
    pattern = r"@app\.route\(\'/doctors\'\)[^\n]*\ndef doctors\(\):.*?(?=@app\.route|if __name__|$)"
    matches = list(re.finditer(pattern, content, re.DOTALL))

    print(f"📋 Найдено {len(matches)} блоков с функцией doctors")

    if len(matches) > 1:
        # Удаляем все, кроме первого
        for match in reversed(matches[1:]):
            print(f"❌ Удаляем дубликат на позиции {match.start()}-{match.end()}")
            content = content[: match.start()] + content[match.end() :]

        # Сохраняем очищенный файл
        with open(main_py_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"✅ Удалено {len(matches) - 1} дублирующих блоков")
    elif len(matches) == 1:
        print("✅ Найден только один блок - дубликатов нет")
    else:
        print("⚠️ Блоки с функцией doctors не найдены")

    return True


def remove_all_our_added_routes():
    """Удаление всех маршрутов, добавленных нашими скриптами"""
    print(f"\n🗑️ УДАЛЕНИЕ ВСЕХ ДОБАВЛЕННЫХ МАРШРУТОВ")
    print("=" * 45)

    main_py_path = "main.py"

    # Читаем файл
    with open(main_py_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Удаляем все маршруты, добавленные в конце файла после последнего оригинального маршрута
    # Находим последний оригинальный маршрут (обычно это что-то связанное с API)

    # Ищем место, где начинаются наши добавленные маршруты
    # Обычно они идут после всех оригинальных маршрутов

    # Простой способ - удалить все что после последнего @app.route с API
    lines = content.split("\n")

    # Найдем последний оригинальный маршрут (API маршруты обычно в конце оригинального кода)
    last_original_route = -1
    added_routes_start = -1

    for i, line in enumerate(lines):
        if "@app.route(" in line:
            if "/api/" in line or "api_" in lines[i + 1] if i + 1 < len(lines) else False:
                last_original_route = i
            elif any(
                route in line
                for route in ["/patients", "/services", "/doctors", "/rooms", "/reports"]
            ):
                if added_routes_start == -1:
                    added_routes_start = i

    if added_routes_start > last_original_route and added_routes_start != -1:
        print(f"📍 Найдены добавленные маршруты начиная со строки {added_routes_start + 1}")

        # Удаляем все от added_routes_start до if __name__
        main_block_start = -1
        for i, line in enumerate(lines):
            if "if __name__ ==" in line:
                main_block_start = i
                break

        if main_block_start != -1:
            # Оставляем только оригинальный код + главный блок
            new_lines = lines[:added_routes_start] + lines[main_block_start:]
            content = "\n".join(new_lines)

            # Сохраняем очищенный файл
            with open(main_py_path, "w", encoding="utf-8") as f:
                f.write(content)

            print(
                f"✅ Удалены все добавленные маршруты (строки {added_routes_start + 1}-{main_block_start})"
            )
        else:
            print("⚠️ Не удалось найти блок if __name__")
    else:
        print("⚠️ Не удалось определить границы добавленных маршрутов")

    return True


def check_remaining_routes():
    """Проверка оставшихся маршрутов"""
    print(f"\n📋 ПРОВЕРКА ОСТАВШИХСЯ МАРШРУТОВ")
    print("=" * 35)

    main_py_path = "main.py"

    with open(main_py_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Ищем все маршруты
    route_pattern = r'@app\.route\([\'"]([^\'"]+)[\'"].*?\)\s*\ndef\s+(\w+)'
    routes = re.findall(route_pattern, content, re.MULTILINE)

    print("📋 Оставшиеся маршруты:")
    for route_path, function_name in routes:
        if route_path in ["/patients", "/services", "/doctors", "/rooms", "/reports"]:
            print(f"   {route_path} → {function_name}()")

    # Проверяем дубликаты
    function_names = [func for route, func in routes]
    duplicates = {name for name in function_names if function_names.count(name) > 1}

    if duplicates:
        print(f"\n❌ Все еще есть дубликаты: {duplicates}")
        return False
    else:
        print(f"\n✅ Дубликатов не найдено")
        return True


def main():
    """Главная функция"""
    print("🔧 ИСПРАВЛЕНИЕ ПРОБЛЕМЫ С ФУНКЦИЕЙ DOCTORS")
    print("=" * 50)

    # 1. Находим все функции doctors
    doctors_funcs = find_doctors_functions()

    if not doctors_funcs:
        print("❌ Функции doctors не найдены")
        return

    if len(doctors_funcs) == 1:
        print("✅ Найдена только одна функция doctors - проблема может быть в другом")
        return

    # 2. Удаляем все добавленные нами маршруты
    remove_all_our_added_routes()

    # 3. Проверяем результат
    if check_remaining_routes():
        print("\n🎉 ПРОБЛЕМА РЕШЕНА!")
        print("\nТеперь попробуйте запустить сервер:")
        print("python main.py")
    else:
        print("\n❌ Проблема не решена полностью")
        print("Возможно, нужно ручное вмешательство")

        # Показываем последние строки файла для ручной проверки
        print("\n📝 Последние 20 строк main.py:")
        with open("main.py", "r", encoding="utf-8") as f:
            lines = f.readlines()

        for i, line in enumerate(lines[-20:], len(lines) - 19):
            print(f"{i:4d}: {line.rstrip()}")


if __name__ == "__main__":
    main()
