
<!-- GENERATED: 2025-09-09 07:58:38 -->
# Routes (methods) + Frontend API calls

# Flask routes with methods
~~~text
.\main.py:L1034: POST /update_event_time
.\main.py:L1045: GET /export_calendar
.\main.py:L1102: GET /add_event
.\main.py:L1102: POST /add_event
.\main.py:L1216: GET /edit_event/<event_id>
.\main.py:L1216: POST /edit_event/<event_id>
.\main.py:L1336: POST /api/busy_slots
.\main.py:L1352: GET /busy_slots/<doctor_id>
.\main.py:L1373: GET /doctors
.\main.py:L1383: GET /add_doctor
.\main.py:L1383: POST /add_doctor
.\main.py:L1402: GET /doctor_card/<doctor_id>
.\main.py:L1411: GET /doctor_busy_slots/<doctor_id>
.\main.py:L1433: POST /api/doctor_schedule
.\main.py:L1453: GET /finance_report
.\main.py:L1552: GET /finance_report/export
.\main.py:L1599: GET /tasks
.\main.py:L1624: POST /add_task
.\main.py:L1639: GET /mark_task_done/<task_id>
.\main.py:L1646: GET /task/<task_id>
.\main.py:L1668: GET /messages
.\main.py:L1675: GET /ztl
.\main.py:L1690: GET /add_ztl
.\main.py:L1690: POST /add_ztl
.\main.py:L1719: GET /partners
.\main.py:L1741: GET /logs
.\main.py:L1748: GET /backup
.\main.py:L1755: GET /profile
.\main.py:L1760: GET /settings
.\main.py:L1765: GET /data_tools
.\main.py:L1765: POST /data_tools
.\main.py:L1772: GET /export_data
.\main.py:L1805: POST /import_data
.\main.py:L1842: GET /cabinet/<cabinet_name>
.\main.py:L1852: GET /api/events
.\main.py:L1984: GET /api/services/<id>
.\main.py:L2008: GET /api/dicts
.\main.py:L2056: GET /api/rooms/busy
.\main.py:L2110: POST /delete_appointment/<id>
.\main.py:L2136: GET /api/appointments/<id>
.\main.py:L2174: POST /api/appointments/<id>/update
.\main.py:L224: GET /api/patients/<id>
.\main.py:L2259: POST /api/appointments/update_time
.\main.py:L2312: DELETE /api/appointments/<id>
.\main.py:L2321: POST /api/appointments/delete
.\main.py:L2327: POST /schedule/api/delete
.\main.py:L2333: GET /api/services_min
.\main.py:L2343: GET /api/visit_statuses_min
.\main.py:L235: POST /api/patients/<id>/update
.\main.py:L2351: POST /api/finance/record
.\main.py:L2403: POST /api/chat/<id>/send
.\main.py:L2468: GET /services
.\main.py:L2481: GET /add_service
.\main.py:L2481: POST /add_service
.\main.py:L2504: GET /edit_service/<id>
.\main.py:L2504: POST /edit_service/<id>
.\main.py:L2532: POST /delete_service/<id>
.\main.py:L2574: GET /rooms
.\main.py:L2582: GET /add_room
.\main.py:L2582: POST /add_room
.\main.py:L2610: GET /edit_room/<id>
.\main.py:L2610: POST /edit_room/<id>
.\main.py:L2641: POST /delete_room/<id>
.\main.py:L267: GET /api/patients/<id>/contacts
.\main.py:L2693: GET /patients
.\main.py:L2748: GET /add_patient
.\main.py:L2748: POST /add_patient
.\main.py:L2764: GET /edit_patient/<id>
.\main.py:L2764: POST /edit_patient/<id>
.\main.py:L2787: POST /delete_patient/<id>
.\main.py:L2795: GET /patient_card/<id>
.\main.py:L2832: POST /api/patients/<id>/update_info
.\main.py:L2862: POST /api/patients/<id>/update_questionary
.\main.py:L2886: POST /api/patients/<id>/generate_card_no
.\main.py:L2905: GET /api/patients/<id>/full
.\main.py:L3095: GET /patients/<pid>
.\main.py:L3103: GET /patients/<pid>/edit
.\main.py:L3111: POST /patients/<pid>/edit
.\main.py:L3168: GET /patients/<pid>/questionnaire
.\main.py:L3177: POST /patients/<pid>/questionnaire
.\main.py:L3221: POST /api/patients
.\main.py:L3276: POST /api/appointments/create_core
.\main.py:L3387: POST /api/appointments
.\main.py:L3388: POST /api/appointments/create
.\main.py:L3389: POST /schedule/api/create
.\main.py:L3397: GET /healthz
.\main.py:L3408: GET /api/patients/search
.\main.py:L353: GET /api/patients/min
.\main.py:L433: GET /api/patients/<id>/min
.\main.py:L458: GET /patients/<id>
.\main.py:L737: GET /roadmap
.\main.py:L753: POST /api/free_slots
.\main.py:L826: GET /login
.\main.py:L826: POST /login
.\main.py:L841: GET /logout
.\main.py:L849: GET /
.\main.py:L854: GET /favicon.ico
.\main.py:L864: GET /calendar
.\main.py:L928: GET /api/rooms/status_now
.\main.py:L970: GET /api/rooms/today_details
.\routes_finance.py:L108: GET /add
.\routes_finance.py:L122: POST /add
.\routes_finance.py:L184: GET /report/cashbox
.\routes_finance.py:L231: GET /export/csv
.\routes_finance.py:L261: GET /export/json
.\routes_finance.py:L284: POST /import/json
.\routes_schedule.py:L111: GET /free_slots
.\routes_schedule.py:L38: GET /
.\routes_schedule.py:L47: POST /add
.\routes\routes_finance.py:L14: GET /services
.\routes\routes_finance.py:L20: POST /services
~~~

---

# Routes summary by method
~~~text
GET: 67
POST: 43
PUT: 0
PATCH: 0
DELETE: 1
OPTIONS: 0
HEAD: 0
~~~

---

# Frontend API calls (fetch/axios/jQuery)
~~~text
.\templates\calendar.backup.html:L724: GET /api/dicts
.\templates\calendar.backup.html:L865: POST /api/patients
.\templates\calendar.backup.html:L1050: POST /api/doctor_schedule
.\templates\calendar.backup.html:L1133: GET /api/events?
.\templates\calendar.backup.html:L1198: POST /api/appointments/update_time
.\templates\calendar.html:L751: GET /api/dicts
.\templates\calendar.html:L917: POST /api/patients
.\templates\calendar.html:L1103: POST /api/doctor_schedule
.\templates\calendar.html:L1202: GET /api/events?
.\templates\calendar.html:L1327: POST /api/free_slots
.\templates\calendar.html:L1409: GET /api/rooms/status_now
.\templates\calendar.html:L1452: GET /api/rooms/today_details?room=
.\templates\calendar.html:L1487: POST /api/appointments/update_time
.\templates\calendar.html:L1589: POST /api/patients
~~~

---

