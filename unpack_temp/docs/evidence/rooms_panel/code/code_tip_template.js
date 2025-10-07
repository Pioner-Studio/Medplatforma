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
  <span
    data-room-name="{{ cab }}"
    style="font-size: 1.12em; font-weight: 600; cursor: default"
  >
    {{ cab }} —
    <b
      class="room-status-text"
      style="color:{{ info.color if info else 'inherit' }}"
    >
      {{ info.text if info else '—' }}
    </b>
    <span
      class="room-next"
      style="opacity: 0.7; font-weight: 500; margin-left: 8px"
    >
      {% if info and info.state == 'available' and info.next %} {% set t =
      info.next.start.split('T')[1] if info.next.start else '' %} Ближайший: {{
      t }} {% if info.next.in_minutes is not none %} (через {% if
      info.next.in_minutes < 0 %}0 мин {% elif info.next.in_minutes < 60 %}{{
      info.next.in_minutes }} мин {% else %}{{ (info.next.in_minutes // 60)|int
      }} ч {{ (info.next.in_minutes % 60)|int }} мин {% endif %} ) {% endif %}
      {% if info.next.service or info.next.patient %} • {{ info.next.service
      }}{% if info.next.service and info.next.patient %} — {% endif %}{{
      info.next.patient }} {% endif %} {% endif %}
    </span>
  </span>
  {% endfor %}
</div>

<!-- Легенда/фильтры -->
<div
  style="
    display: flex;
    gap: 30px;
    align-items: center;
    font-size: 1.01em;
    margin-bottom: 12px;
    margin-left: 8px;
  "
>
  <span
    ><span
      style="
        background: #a2c6fa;
        border: 1.5px solid #dde7f7;
        width: 18px;
        height: 18px;
        display: inline-block;
        border-radius: 4px;
