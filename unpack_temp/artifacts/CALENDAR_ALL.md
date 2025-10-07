
<!-- GENERATED: 2025-09-12 13:03:09 -->
# Calendar — ALL-IN-ONE report

Source: .\templates\calendar.html

## Summary

- API calls detected: 7
- UPPER_CASE constants: 1
- Key inputs/selects: 10

## ALL constants (UPPER_CASE)

- ROUTES

## Key blocks

### events:  (@L698)
~~~js
  /* PATCH: кликабельность и поведение подсказок */
  .ps-room-clickable {
    cursor: pointer;
  }
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
~~~

### FullCalendar init  (@L1168)
~~~js
    }

    // ---------- FullCalendar ----------
    // глобальное состояние фильтра по пациенту (мини-поиск наверху)
    window.psSelectedPatientId = window.psSelectedPatientId || "";
    const calEl = document.getElementById("calendar");
    const calendar = new FullCalendar.Calendar(calEl, {
      initialView: "timeGridWeek",
      locale: "ru",
      buttonText: {
        today: "сегодня",
        month: "месяц",
        week: "неделя",
        day: "день",
      },
      allDayText: "Весь день",
      timeZone: "local",
      firstDay: 1,
      height: "auto",
      headerToolbar: {
        left: "prev,next today",
        center: "title",
        right: "dayGridMonth,timeGridWeek,timeGridDay",
      },
      slotDuration: "00:15:00",
      snapDuration: "00:15:00",
      slotMinTime: "09:00:00",
      slotMaxTime: "21:00:00",
      businessHours: {
        daysOfWeek: [1, 2, 3, 4, 5, 6],
        startTime: "09:00",
        endTime: "21:00",
      },

      editable: true,
      eventDurationEditable: true,
      eventStartEditable: true,
      eventOverlap: true,

      // ЗАГРУЗКА СОБЫТИЙ
      events: (fetchInfo, success, failure) => {
        const params = new URLSearchParams({
          start: fetchInfo.startStr,
          end: fetchInfo.endStr,
        });

        const doctorSel = document.querySelector("#doctorFilter");
~~~

## Frontend API calls (method url @line)

- POST /api/appointments/update_time  @L1683
- GET /api/dicts  @L775
- POST /api/doctor_schedule  @L1127
- GET /api/events?  @L1226
- POST /api/patients  @L941
- POST /api/patients  @L1785
- GET /api/rooms/status_now  @L1492

## Likely query parameters

- date
- doctor_id
- end
- patient_id
- patientid
- room
- service_id
- start

## UI inputs/selects (id/name hints)

- cabinetFilter
- doctorFilter
- patient
- qm_doctor
- qm_end
- qm_patient
- qm_room
- qm_service
- qm_start
- serviceFilter

## Backend matches (by snapshot)

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
