
<!-- GENERATED: 2025-09-12 17:08:42 -->
# Rooms panel API — autodetected endpoints

Source calendar: .\templates\calendar.html
BaseUrl: http://localhost:5000

## Detected /api calls (first 10)
- GET /api/appointments @L1864
- DELETE /api/appointments/${encodeURIComponent(id @L1937
- GET /api/appointments/${id}` @L1716
- POST /api/appointments/${qm.id.value}/update`, @L1904
- POST /api/appointments/create @L1865
- DELETE /api/appointments/delete @L1935
- POST /api/appointments/update_time @L1683
- POST /api/create @L1866
- DELETE /api/delete @L1934
- GET /api/dicts @L775

## A1) GET /api/rooms/status_now
- detected url: /api/rooms/status_now
- method guess: GET
- saved: .\artifacts\rooms_panel\rooms_status_now.json

## A2) /api/free_slots (or similar)
- detected url: /api/free_slots
- method guess: GET
- request: .\artifacts\rooms_panel\free_slots_request.json
- response: .\artifacts\rooms_panel\free_slots_response.json

## A3) /api/today_details
- detected url: /api/rooms/today_details
- saved: .\artifacts\rooms_panel\today_details_response.json

## B) update_time
- detected url: /api/appointments/update_time
- method guess: POST
- request template: .\artifacts\rooms_panel\update_time_request_template.json
- expected keys:

