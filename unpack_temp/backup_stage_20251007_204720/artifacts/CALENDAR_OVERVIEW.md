
# Calendar — Overview

Generated: 2025-09-11 08:33:37
Source: .\templates\calendar.html

## Резюме
- Найдено фронт-вызовов API: 7
- Ключевые параметры: date, doctor_id, end, patient_id, patientid, room, service_id, start
- Полезные input/select: cabinetFilter, doctorFilter, patient, qm_doctor, qm_end, qm_patient, qm_room, qm_service, qm_start, serviceFilter

## API вызовы (method url @line)
- POST /api/appointments/update_time  @L1660
- GET /api/dicts  @L775
- POST /api/doctor_schedule  @L1127
- GET /api/events?  @L1226
- POST /api/patients  @L941
- POST /api/patients  @L1762
- GET /api/rooms/status_now  @L1486

## Блок формирования событий (FullCalendar)
```js
  .ps-free-hint,
  [data-free-hint] {
    pointer-events: auto;
  }
  [data-room],
  .ps-room,
  .room,
  .ps-rooms-item,
  [data-open-room] {
    cursor: pointer;
  }
</style>

<script>
  // --- простой toast ---
  function showToast(msg, type = "info", ms = 2200) {
    const stack = document.getElementById("toastStack");
    if (!stack) {
      alert(msg);
      return;
    }
    const el = document.createElement("div");
    el.textContent = msg;
    el.style.cssText = `
      background:${
        type === "error" ? "#fee2e2" : type === "ok" ? "#e6ffed" : "#eef2ff"
      };
      color:${
        type === "error" ? "#991b1b" : type === "ok" ? "#065f46" : "#1e40af"
      };
      border:1px solid ${
        type === "error" ? "#fecaca" : type === "ok" ? "#bbf7d0" : "#c7d2fe"
      };
      box-shadow:0 6px 18px rgba(0,0,0,.08);padding:10px 14px;border-radius:10px;font-weight:600;max-width:420px`;
    stack.appendChild(el);
    setTimeout(() => {
      el.style.transition = "opacity .25s";
      el.style.opacity = "0";
      setTimeout(() => el.remove(), 260);
    }, ms);
  }
</script>
<script>
  document.addEventListener("DOMContentLoaded", () => {
    // ---------- helpers ----------
    const $ = (s) => document.querySelector(s);
    const addMin = (d, m) => new Date(d.getTime() + m * 60000);
    const pad2 = (n) => String(n).padStart(2, "0");
    const fmtISO = (d) =>
      `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}T${pad2(
        d.getHours()
      )}:${pad2(d.getMinutes())}`;

```

## Соответствие backend (по снапшоту ROUTES_METHODS_FRONT_AND_TREE.md)
- .\main.py:L1433: POST /api/doctor_schedule
- .\main.py:L1852: GET /api/events
- .\main.py:L2008: GET /api/dicts
- .\main.py:L224: GET /api/patients/<id>
- .\main.py:L2259: POST /api/appointments/update_time
- .\main.py:L235: POST /api/patients/<id>/update
- .\main.py:L267: GET /api/patients/<id>/contacts
- .\main.py:L2832: POST /api/patients/<id>/update_info
- .\main.py:L2862: POST /api/patients/<id>/update_questionary
- .\main.py:L2886: POST /api/patients/<id>/generate_card_no
- .\main.py:L2905: GET /api/patients/<id>/full
- .\main.py:L3221: POST /api/patients
- .\main.py:L3408: GET /api/patients/search
- .\main.py:L353: GET /api/patients/min
- .\main.py:L433: GET /api/patients/<id>/min
- .\main.py:L928: GET /api/rooms/status_now
- .\templates\calendar.backup.html:L1050: POST /api/doctor_schedule
- .\templates\calendar.backup.html:L1133: GET /api/events?
- .\templates\calendar.backup.html:L1198: POST /api/appointments/update_time
- .\templates\calendar.backup.html:L724: GET /api/dicts
- .\templates\calendar.backup.html:L865: POST /api/patients
- .\templates\calendar.html:L1127: POST /api/doctor_schedule
- .\templates\calendar.html:L1226: GET /api/events?
- .\templates\calendar.html:L1486: GET /api/rooms/status_now
- .\templates\calendar.html:L1660: POST /api/appointments/update_time
- .\templates\calendar.html:L1762: POST /api/patients
- .\templates\calendar.html:L775: GET /api/dicts
- .\templates\calendar.html:L941: POST /api/patients

## Поток данных (кратко)
- Пользователь меняет фильтры/инпуты (patient_id, doctor_id, service_id, oom, date/start/end).
- JS формирует запрос к API (см. раздел *API вызовы*).
- Бэкенд возвращает события; календарь перерисовывает слоты.

