
# Calendar report

Generated: 2025-09-15 15:27:04
Source: .\templates\calendar.html

## Frontend API calls (method url @line)
- POST /api/appointments/update_time  @L1760
- GET /api/dicts  @L797
- POST /api/doctor_schedule  @L1149
- GET /api/events?  @L1248
- POST /api/patients  @L963
- POST /api/patients  @L1862
- GET /api/rooms/status_now  @L1569

## Likely query parameters
- date
- doctor_id
- end
- patient_id
- patientid
- room
- service_id
- start

## UI inputs/selects (key hints)
- cabinetFilter
- doctorFilter
- patient
- qm_doctor
- qm_patient
- qm_room
- qm_service
- serviceFilter

## FullCalendar events block (context)
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
```

## Backend matches (from ROUTES_METHODS_FRONT_AND_TREE.md)
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
