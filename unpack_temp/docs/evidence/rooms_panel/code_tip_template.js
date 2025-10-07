{% extends "base.html" %} {% block content %}

<!-- Метрики и действия -->
<div
  style="
    display: flex;
    align-items: center;
    gap: 22px;
    padding: 6px 0 6px 12px;
    background: #fff;
    border-radius: 14px;
    box-shadow: 0 1px 8px #e3eaf9b7;
    margin-bottom: 10px;
  "
>
  <span title="Всего кабинетов">
    <i class="fa-solid fa-house-chimney-medical" style="color: #467fe3"></i>
    <b>{{ metrics.total_rooms }}</b>
  </span>
  <span title="Свободные">
    <i class="fa-solid fa-circle-check" style="color: #21ba45"></i>
    <b>{{ metrics.free_rooms }}</b>
  </span>
  <span style="margin-left: auto; display: flex; gap: 12px">
    <a
      href="{{ url_for('add_event') }}"
      class="btn-main"
      style="
        background: #1976d2;
        color: #fff;
        font-weight: 600;
        border-radius: 8px;
        padding: 8px 22px;
        font-size: 1.07em;
        display: flex;
        align-items: center;
        gap: 8px;
        text-decoration: none;
      "
    >
      <i class="fa-solid fa-plus"></i> Добавить запись
    </a>
    <a
      href="{{ url_for('export_calendar') }}"
      class="btn-main btn-export"
      style="
        background: #fff;
        color: #3185cb;
        border: 1.5px solid #dbeafd;
        font-weight: 600;
        border-radius: 8px;
        padding: 8px 18px;
        font-size: 1.07em;
        display: flex;
        align-items: center;
        gap: 8px;
        text-decoration: none;
      "
    >
      <i class="fa-solid fa-file-arrow-down"></i> Выгрузка
    </a>
  </span>
</div>

<!-- Кабинеты и их статус -->
<div
  id="roomsBar"
  style="display: flex; gap: 36px; margin: 14px 0 12px 8px; flex-wrap: wrap"
>
  {% for cab in cabinets %} {% set info = room_info.get(cab) if room_info else
  None %}
