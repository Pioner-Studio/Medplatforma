
# update_time — sample responses

## success
```json
{
    "status":  "ok",
    "update_time":  "2025-09-11T10:30:00Z",
    "message":  "Time updated",
    "appointment_id":  123,
    "action":  "update_time"
}
```

## conflict
```json
{
    "status":  "conflict",
    "message":  "Slot is already booked",
    "appointment_id":  123,
    "action":  "update_time",
    "conflict_with":  {
                          "doctor_id":  7,
                          "appointment_id":  456,
                          "end":  "2025-09-11T10:45:00Z",
                          "room":  "Ортопедия",
                          "start":  "2025-09-11T10:15:00Z"
                      }
}
```

## error
```json
{
    "status":  "error",
    "error":  "validation",
    "message":  "Outside working hours (09:00–21:00)",
    "action":  "update_time",
    "details":  {
                    "end":  "2025-09-11T09:30:00Z",
                    "reason":  "non_working_time",
                    "start":  "2025-09-11T08:30:00Z"
                }
}
```
