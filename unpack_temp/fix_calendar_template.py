# fix_calendar_template.py
# Исправляем шаблон calendar.html для отображения услуг

with open("templates/calendar.html", "r", encoding="utf-8") as f:
    content = f.read()

# Ищем пустой select для услуг и заменяем его
old_services_select = """<select id="serviceFilter" class="filter-select">
    <option value="">Все услуги</option>
  </select>"""

new_services_select = """<select id="serviceFilter" class="filter-select">
    <option value="">Все услуги</option>
    {% for service in services %}
    <option value="{{ service._id }}">{{ service.name }}</option>
    {% endfor %}
  </select>"""

# Заменяем
content = content.replace(old_services_select, new_services_select)

# Сохраняем
with open("templates/calendar.html", "w", encoding="utf-8") as f:
    f.write(content)

print("✅ Шаблон calendar.html исправлен - добавлен цикл для услуг!")
