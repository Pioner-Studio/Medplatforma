# Flask routes map

_generated: 2025-08-26 16:05:41_

| Rule | Endpoint | Methods |
|------|----------|---------|
| `/` | `home` | `GET` |
| `/add_doctor` | `add_doctor` | `GET,POST` |
| `/add_event` | `add_event` | `GET,POST` |
| `/add_patient` | `add_patient` | `GET,POST` |
| `/add_room` | `add_room` | `GET,POST` |
| `/add_service` | `add_service` | `GET,POST` |
| `/add_task` | `add_task` | `POST` |
| `/add_ztl` | `add_ztl` | `GET,POST` |
| `/api/appointments/<id>` | `api_appointment_get` | `GET` |
| `/api/appointments/<id>/update` | `api_appointment_update` | `POST` |
| `/api/appointments/update_time` | `api_appointments_update_time` | `POST` |
| `/api/busy_slots` | `api_busy_slots` | `POST` |
| `/api/chat/<id>/send` | `api_chat_send` | `POST` |
| `/api/dicts` | `api_dicts` | `GET` |
| `/api/doctor_schedule` | `doctor_schedule` | `POST` |
| `/api/events` | `api_events` | `GET` |
| `/api/finance/record` | `api_finance_record` | `POST` |
| `/api/free_slots` | `api_free_slots` | `POST` |
| `/api/patients/<id>/full` | `api_patient_full` | `GET` |
| `/api/patients/<id>/generate_card_no` | `api_patient_generate_card_no` | `POST` |
| `/api/patients/<id>/update_info` | `api_patient_update_info` | `POST` |
| `/api/patients/<id>/update_questionary` | `api_patient_update_questionary` | `POST` |
| `/api/rooms/busy` | `api_room_busy` | `GET` |
| `/api/rooms/status_now` | `api_rooms_status_now` | `GET` |
| `/api/rooms/today_details` | `api_rooms_today_details` | `GET` |
| `/api/services/<id>` | `api_service_get` | `GET` |
| `/api/services_min` | `api_services_min` | `GET` |
| `/api/visit_statuses_min` | `api_visit_statuses_min` | `GET` |
| `/backup` | `backup` | `GET` |
| `/busy_slots/<doctor_id>` | `busy_slots` | `GET` |
| `/cabinet/<cabinet_name>` | `cabinet_card` | `GET` |
| `/calendar` | `calendar_view` | `GET` |
| `/data_tools` | `data_tools` | `GET,POST` |
| `/delete_appointment/<id>` | `delete_appointment` | `POST` |
| `/delete_patient/<id>` | `delete_patient` | `POST` |
| `/delete_room/<id>` | `delete_room` | `POST` |
| `/delete_service/<id>` | `delete_service` | `POST` |
| `/doctor_busy_slots/<doctor_id>` | `doctor_busy_slots` | `GET` |
| `/doctor_card/<doctor_id>` | `doctor_card` | `GET` |
| `/doctors` | `doctors` | `GET` |
| `/edit_event/<event_id>` | `edit_event` | `GET,POST` |
| `/edit_patient/<id>` | `edit_patient` | `GET,POST` |
| `/edit_room/<id>` | `edit_room` | `GET,POST` |
| `/edit_service/<id>` | `edit_service` | `GET,POST` |
| `/export_calendar` | `export_calendar` | `GET` |
| `/export_data` | `export_data` | `GET` |
| `/finance` | `finance.list_ops` | `GET` |
| `/finance/add` | `finance.add_get` | `GET` |
| `/finance/add` | `finance.add_post` | `POST` |
| `/finance/export/csv` | `finance.export_csv` | `GET` |
| `/finance/export/json` | `finance.export_json` | `GET` |
| `/finance/import/json` | `finance.import_json` | `POST` |
| `/finance/report/cashbox` | `finance.report_cashbox` | `GET` |
| `/finance_report` | `finance_report` | `GET` |
| `/finance_report/export` | `finance_report_export` | `GET` |
| `/healthz` | `healthz` | `GET` |
| `/import_data` | `import_data` | `POST` |
| `/login` | `login` | `GET,POST` |
| `/logout` | `logout` | `GET` |
| `/logs` | `logs` | `GET` |
| `/mark_task_done/<task_id>` | `mark_task_done` | `GET` |
| `/messages` | `messages` | `GET` |
| `/partners` | `partners` | `GET` |
| `/patient_card/<id>` | `patient_card` | `GET` |
| `/patients` | `patients_list` | `GET` |
| `/profile` | `profile` | `GET` |
| `/roadmap` | `roadmap_view` | `GET` |
| `/rooms` | `rooms_list` | `GET` |
| `/schedule/` | `schedule.list_view` | `GET` |
| `/schedule/add` | `schedule.add_appointment` | `POST` |
| `/schedule/free_slots` | `schedule.free_slots` | `GET` |
| `/services` | `services_list` | `GET` |
| `/settings` | `settings` | `GET` |
| `/static/<path:filename>` | `static` | `GET` |
| `/task/<task_id>` | `task_card` | `GET` |
| `/tasks` | `tasks` | `GET` |
| `/update_event_time` | `update_event_time` | `POST` |
| `/ztl` | `ztl` | `GET` |

---

### `/`
- endpoint: `home`
- methods: `GET`

### `/add_doctor`
- endpoint: `add_doctor`
- methods: `GET,POST`

### `/add_event`
- endpoint: `add_event`
- methods: `GET,POST`

### `/add_patient`
- endpoint: `add_patient`
- methods: `GET,POST`

### `/add_room`
- endpoint: `add_room`
- methods: `GET,POST`

### `/add_service`
- endpoint: `add_service`
- methods: `GET,POST`

### `/add_task`
- endpoint: `add_task`
- methods: `POST`

### `/add_ztl`
- endpoint: `add_ztl`
- methods: `GET,POST`

### `/api/appointments/<id>`
- endpoint: `api_appointment_get`
- methods: `GET`

### `/api/appointments/<id>/update`
- endpoint: `api_appointment_update`
- methods: `POST`

### `/api/appointments/update_time`
- endpoint: `api_appointments_update_time`
- methods: `POST`

### `/api/busy_slots`
- endpoint: `api_busy_slots`
- methods: `POST`

### `/api/chat/<id>/send`
- endpoint: `api_chat_send`
- methods: `POST`

### `/api/dicts`
- endpoint: `api_dicts`
- methods: `GET`

### `/api/doctor_schedule`
- endpoint: `doctor_schedule`
- methods: `POST`

### `/api/events`
- endpoint: `api_events`
- methods: `GET`

### `/api/finance/record`
- endpoint: `api_finance_record`
- methods: `POST`

### `/api/free_slots`
- endpoint: `api_free_slots`
- methods: `POST`

### `/api/patients/<id>/full`
- endpoint: `api_patient_full`
- methods: `GET`

### `/api/patients/<id>/generate_card_no`
- endpoint: `api_patient_generate_card_no`
- methods: `POST`

### `/api/patients/<id>/update_info`
- endpoint: `api_patient_update_info`
- methods: `POST`

### `/api/patients/<id>/update_questionary`
- endpoint: `api_patient_update_questionary`
- methods: `POST`

### `/api/rooms/busy`
- endpoint: `api_room_busy`
- methods: `GET`

### `/api/rooms/status_now`
- endpoint: `api_rooms_status_now`
- methods: `GET`

### `/api/rooms/today_details`
- endpoint: `api_rooms_today_details`
- methods: `GET`

### `/api/services/<id>`
- endpoint: `api_service_get`
- methods: `GET`

### `/api/services_min`
- endpoint: `api_services_min`
- methods: `GET`

### `/api/visit_statuses_min`
- endpoint: `api_visit_statuses_min`
- methods: `GET`

### `/backup`
- endpoint: `backup`
- methods: `GET`

### `/busy_slots/<doctor_id>`
- endpoint: `busy_slots`
- methods: `GET`

### `/cabinet/<cabinet_name>`
- endpoint: `cabinet_card`
- methods: `GET`

### `/calendar`
- endpoint: `calendar_view`
- methods: `GET`

### `/data_tools`
- endpoint: `data_tools`
- methods: `GET,POST`

### `/delete_appointment/<id>`
- endpoint: `delete_appointment`
- methods: `POST`

### `/delete_patient/<id>`
- endpoint: `delete_patient`
- methods: `POST`

### `/delete_room/<id>`
- endpoint: `delete_room`
- methods: `POST`

### `/delete_service/<id>`
- endpoint: `delete_service`
- methods: `POST`

### `/doctor_busy_slots/<doctor_id>`
- endpoint: `doctor_busy_slots`
- methods: `GET`

### `/doctor_card/<doctor_id>`
- endpoint: `doctor_card`
- methods: `GET`

### `/doctors`
- endpoint: `doctors`
- methods: `GET`

### `/edit_event/<event_id>`
- endpoint: `edit_event`
- methods: `GET,POST`

### `/edit_patient/<id>`
- endpoint: `edit_patient`
- methods: `GET,POST`

### `/edit_room/<id>`
- endpoint: `edit_room`
- methods: `GET,POST`

### `/edit_service/<id>`
- endpoint: `edit_service`
- methods: `GET,POST`

### `/export_calendar`
- endpoint: `export_calendar`
- methods: `GET`

### `/export_data`
- endpoint: `export_data`
- methods: `GET`

### `/finance`
- endpoint: `finance.list_ops`
- methods: `GET`

### `/finance/add`
- endpoint: `finance.add_get`
- methods: `GET`

### `/finance/add`
- endpoint: `finance.add_post`
- methods: `POST`

### `/finance/export/csv`
- endpoint: `finance.export_csv`
- methods: `GET`

### `/finance/export/json`
- endpoint: `finance.export_json`
- methods: `GET`

### `/finance/import/json`
- endpoint: `finance.import_json`
- methods: `POST`

### `/finance/report/cashbox`
- endpoint: `finance.report_cashbox`
- methods: `GET`

### `/finance_report`
- endpoint: `finance_report`
- methods: `GET`

### `/finance_report/export`
- endpoint: `finance_report_export`
- methods: `GET`

### `/healthz`
- endpoint: `healthz`
- methods: `GET`

### `/import_data`
- endpoint: `import_data`
- methods: `POST`

### `/login`
- endpoint: `login`
- methods: `GET,POST`

### `/logout`
- endpoint: `logout`
- methods: `GET`

### `/logs`
- endpoint: `logs`
- methods: `GET`

### `/mark_task_done/<task_id>`
- endpoint: `mark_task_done`
- methods: `GET`

### `/messages`
- endpoint: `messages`
- methods: `GET`

### `/partners`
- endpoint: `partners`
- methods: `GET`

### `/patient_card/<id>`
- endpoint: `patient_card`
- methods: `GET`

### `/patients`
- endpoint: `patients_list`
- methods: `GET`

### `/profile`
- endpoint: `profile`
- methods: `GET`

### `/roadmap`
- endpoint: `roadmap_view`
- methods: `GET`

### `/rooms`
- endpoint: `rooms_list`
- methods: `GET`

### `/schedule/`
- endpoint: `schedule.list_view`
- methods: `GET`

### `/schedule/add`
- endpoint: `schedule.add_appointment`
- methods: `POST`

### `/schedule/free_slots`
- endpoint: `schedule.free_slots`
- methods: `GET`

### `/services`
- endpoint: `services_list`
- methods: `GET`

### `/settings`
- endpoint: `settings`
- methods: `GET`

### `/static/<path:filename>`
- endpoint: `static`
- methods: `GET`

### `/task/<task_id>`
- endpoint: `task_card`
- methods: `GET`

### `/tasks`
- endpoint: `tasks`
- methods: `GET`

### `/update_event_time`
- endpoint: `update_event_time`
- methods: `POST`

### `/ztl`
- endpoint: `ztl`
- methods: `GET`
