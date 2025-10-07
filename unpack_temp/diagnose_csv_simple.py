# diagnose_csv_simple.py
import csv
import os


def check_csv(filename):
    print(f"\n{'='*50}")
    print(f"Файл: {filename}")
    print("=" * 50)

    # Пробуем разные кодировки
    encodings = ["utf-8-sig", "utf-8", "cp1251", "windows-1251", "latin-1"]

    for encoding in encodings:
        try:
            with open(filename, "r", encoding=encoding) as f:
                content = f.read()
                f.seek(0)
                reader = csv.DictReader(f)
                headers = reader.fieldnames
                rows = list(reader)

                print(f"✓ Кодировка {encoding} работает")
                print(f"  Заголовки: {headers}")
                print(f"  Строк данных: {len(rows)}")

                if rows:
                    print(f"  Первая строка:")
                    for key, value in rows[0].items():
                        # Очищаем ключи от BOM и пробелов
                        clean_key = key.strip().replace("\ufeff", "")
                        print(f"    {repr(clean_key)}: {repr(value)}")

                # Проверяем, почему импорт может не работать
                if filename == "rooms.csv":
                    for row in rows:
                        name = row.get("name", "").strip()
                        if not name:
                            # Пробуем другие возможные имена колонок
                            for k in row.keys():
                                if "name" in k.lower() or "название" in k.lower():
                                    name = row[k]
                                    print(f"  ! Колонка с именем кабинета: {repr(k)}")
                                    break

                break

        except Exception as e:
            print(f"✗ Кодировка {encoding}: {e}")


# Проверяем все CSV
for file in ["rooms.csv", "users.csv", "doctors.csv", "services_price_dual.csv"]:
    if os.path.exists(file):
        check_csv(file)
