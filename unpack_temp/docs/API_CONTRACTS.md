# API_CONTRACTS

## GET /api/rooms/busy

Params: room_id=ObjectId, date=YYYY-MM-DD
Response:
{
"ok": true,
"items": [
{"start": "10:00", "end": "10:30"},
{"start": "11:15", "end": "12:00"}
]
}

## POST /api/doctor_schedule

Body:
{ "doctor_id": "<ObjectId>" }
Response:
{
"ok": true,
"schedule": {
"0": {"start": "09:00", "end": "21:00"},
…,
"6": {"start": "09:00", "end": "21:00"}
}
}
