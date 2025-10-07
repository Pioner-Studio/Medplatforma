# create_role_templates.py
# Обновляем шаблоны для скрытия элементов по ролям


def update_base_template():
    with open("templates/base.html", "r", encoding="utf-8") as f:
        content = f.read()

    # Оборачиваем админские ссылки в проверку роли
    admin_sections = [
        ('href="/doctors"', "admin"),
        ('href="/services"', "admin"),
        ('href="/rooms"', "admin"),
        ('href="/data_tools"', "admin"),
        ('href="/backup"', "admin"),
    ]

    for link, role in admin_sections:
        if link in content:
            # Находим родительский элемент (обычно <li> или <a>)
            start = content.find(link)
            # Ищем начало тега
            tag_start = content.rfind("<", 0, start)
            # Ищем конец тега
            tag_end = content.find(">", content.find("</", start)) + 1

            old_element = content[tag_start:tag_end]
            new_element = f'{{% if session.user_role == "{role}" %}}\n{old_element}\n{{% endif %}}'
            content = content.replace(old_element, new_element)

    with open("templates/base.html", "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Шаблон base.html обновлен для ролей")


# Запускаем обновление
update_base_template()
