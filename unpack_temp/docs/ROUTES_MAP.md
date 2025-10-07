# ROUTES_MAP

| URL                  | Method | Handler (функция)     | Шаблон                  | Примечания                      |
| -------------------- | ------ | --------------------- | ----------------------- | ------------------------------- |
| /                    | GET    | index()               | templates/index.html    | Главная                         |
| /calendar            | GET    | calendar()            | templates/calendar.html | FullCalendar                    |
| /api/rooms/busy      | GET    | api_rooms_busy()      | —                       | Query: room_id, date=YYYY-MM-DD |
| /api/doctor_schedule | POST   | api_doctor_schedule() | —                       | Body: { doctor_id }             |
| …                    | …      | …                     | …                       | …                               |
