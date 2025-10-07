# diagnose_csv.py
import csv
import chardet


def check_csv(filename):
    print(f"\n{'='*50}")
    print(f"Файл: {filename}")
    print("=" * 50)

    # Определяем кодировку
    with open(filename, "rb") as f:
        raw = f.read()
        result = chardet.detect(raw)
        encoding = result["encoding"]
        print(f"Кодировка: {encoding}")

    # Читаем с правильной кодировкой
    try:
        with open(filename, "r", encoding=encoding) as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            print(f"Заголовки: {headers}")

            rows = list(reader)
            print(f"Количество строк: {len(rows)}")

            if rows:
                print(f"Первая строка:")
                for key, value in rows[0].items():
                    print(f"  {repr(key)}: {repr(value)}")
    except Exception as e:
        print(f"Ошибка чтения: {e}")


# Проверяем все CSV
for file in ["rooms.csv", "users.csv", "doctors.csv", "services_price_dual.csv"]:
    check_csv(file)
