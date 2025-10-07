# DB_SCHEMA (актуальная схема)

## collections.doctors

- \_id: ObjectId
- full_name: string
- room_id: ObjectId
- schedule: { "0": {start:"09:00", end:"21:00"}, …, "6": {…} }
- specialties: ["Терапия"|"Ортодонтия"|…]

## collections.patients

- \_id: ObjectId
- full_name: string
- birth_date: YYYY-MM-DD
- card_no: string
- allergies: [string]
- diseases: [string]
- surgeries: [string]

## collections.rooms

- \_id: ObjectId
- name: string ("Детский"|"Ортопедия"|…)
- code: string (например, R01)

## collections.events

- \_id: ObjectId
- start: ISODate
- end: ISODate
- doctor_id: ObjectId
- patient_id: ObjectId
- room_id: ObjectId
- status: string ("planned"|"done"|"cancelled")
- note: string
- source: string ("admin"|"web")

## collections.finance

- \_id: ObjectId
- type: string ("income"|"expense"|"deposit"|"purchase")
- amount: number
- category: string
- source: string
- comment: string
- created_at: ISODate

## Indexes (минимум)

- events: { doctor_id:1, start:1 }, { room_id:1, start:1 }
- finance: { created_at:-1 }, { category:1 }
