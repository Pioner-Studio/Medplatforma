# fix_encoding.py
with open('main.py', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Пытаемся восстановить кириллицу
try:
    # Преобразуем обратно: UTF-8 -> Latin-1 -> UTF-8
    fixed = content.encode('latin-1').decode('utf-8')
    
    with open('main_fixed.py', 'w', encoding='utf-8') as f:
        f.write(fixed)
    
    print("✅ Файл исправлен: main_fixed.py")
except Exception as e:
    print(f"❌ Ошибка: {e}")
