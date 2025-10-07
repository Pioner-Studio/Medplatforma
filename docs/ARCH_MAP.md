# Medplatforma — ARCH_MAP.md (Маршруты, шаблоны, связи)
_Обновлено: 2025-10-07 08:53_

**Легенда статусов:** `verified` — подтверждено сканером кода (`routes.json`); `pending` — вероятно есть частично (нужна проверка/реализация); `planned` — спроектировано, в коде ещё нет.

---

## 1) Verified — найдено в коде (по routes.json)
| Route                                                | Methods  | File                                                                      | Status   |
| ---------------------------------------------------- | -------- | ------------------------------------------------------------------------- | -------- |
| /patients                                            | GET      | D:\Projects\medplatforma\add_missing_patient_routes.py                    | verified |
| /patients                                            | GET      | D:\Projects\medplatforma\add_missing_patient_routes.py                    | verified |
| /patients                                            | GET      | D:\Projects\medplatforma\add_missing_patient_routes.py                    | verified |
| /patients/<patient_id>                               | GET      | D:\Projects\medplatforma\add_missing_patient_routes.py                    | verified |
| /api/patients/<patient_id>/treatment-plans           | GET      | D:\Projects\medplatforma\add_treatment_plan_api.py                        | verified |
| {route}                                              | GET      | D:\Projects\medplatforma\check_and_fix_menu_directly.py                   | verified |
| {route}                                              | GET      | D:\Projects\medplatforma\check_and_fix_menu_directly.py                   | verified |
| /patients                                            | GET      | D:\Projects\medplatforma\check_and_fix_menu_directly.py                   | verified |
| /services                                            | GET      | D:\Projects\medplatforma\check_and_fix_menu_directly.py                   | verified |
| /doctors                                             | GET      | D:\Projects\medplatforma\check_roles_and_fix_access.py                    | verified |
| /add_doctor                                          | GET      | D:\Projects\medplatforma\check_roles_and_fix_access.py                    | verified |
| /services                                            | GET      | D:\Projects\medplatforma\check_roles_and_fix_access.py                    | verified |
| /add_service                                         | GET      | D:\Projects\medplatforma\check_roles_and_fix_access.py                    | verified |
| /edit_service                                        | GET      | D:\Projects\medplatforma\check_roles_and_fix_access.py                    | verified |
| /delete_service                                      | GET      | D:\Projects\medplatforma\check_roles_and_fix_access.py                    | verified |
| /rooms                                               | GET      | D:\Projects\medplatforma\check_roles_and_fix_access.py                    | verified |
| /add_room                                            | GET      | D:\Projects\medplatforma\check_roles_and_fix_access.py                    | verified |
| /edit_room                                           | GET      | D:\Projects\medplatforma\check_roles_and_fix_access.py                    | verified |
| /delete_room                                         | GET      | D:\Projects\medplatforma\check_roles_and_fix_access.py                    | verified |
| /data_tools                                          | GET      | D:\Projects\medplatforma\check_roles_and_fix_access.py                    | verified |
| /backup                                              | GET      | D:\Projects\medplatforma\check_roles_and_fix_access.py                    | verified |
| /patients                                            | GET      | D:\Projects\medplatforma\check_roles_and_fix_access.py                    | verified |
| /add_patient                                         | GET      | D:\Projects\medplatforma\check_roles_and_fix_access.py                    | verified |
| /edit_patient                                        | GET      | D:\Projects\medplatforma\check_roles_and_fix_access.py                    | verified |
| /finance                                             | GET      | D:\Projects\medplatforma\check_roles_and_fix_access.py                    | verified |
| /api/appointments/create                             | GET      | D:\Projects\medplatforma\check_roles_and_fix_access.py                    | verified |
| /api/patients                                        | POST     | D:\Projects\medplatforma\check_roles_and_fix_access.py                    | verified |
| /patients                                            | GET      | D:\Projects\medplatforma\debug_patients_route.py                          | verified |
| /patients                                            | GET      | D:\Projects\medplatforma\debug_patients_route.py                          | verified |
| /patients/<patient_id>                               | GET      | D:\Projects\medplatforma\debug_patients_route.py                          | verified |
| /api/admin/seed/dicts                                | GET      | D:\Projects\medplatforma\fix_admin_seed_api.py                            | verified |
| /api/events                                          | GET      | D:\Projects\medplatforma\fix_api_authentication.py                        | verified |
| /calendar                                            | GET      | D:\Projects\medplatforma\fix_api_authentication.py                        | verified |
| /api/dicts                                           | GET      | D:\Projects\medplatforma\fix_api_dicts.py                                 | verified |
| /api/dicts                                           | GET      | D:\Projects\medplatforma\fix_api_dicts_correct.py                         | verified |
| /api/dicts                                           | GET      | D:\Projects\medplatforma\fix_api_dicts_final.py                           | verified |
| /api/events                                          | GET      | D:\Projects\medplatforma\fix_calendar_events_display.py                   | verified |
| /api/events                                          | GET      | D:\Projects\medplatforma\fix_calendar_events_display.py                   | verified |
| /calendar                                            | GET      | D:\Projects\medplatforma\fix_calendar_view.py                             | verified |
| /patients                                            | GET      | D:\Projects\medplatforma\fix_duplicate_routes.py                          | verified |
| /services                                            | GET      | D:\Projects\medplatforma\fix_duplicate_routes.py                          | verified |
| /doctors                                             | GET      | D:\Projects\medplatforma\fix_duplicate_routes.py                          | verified |
| /rooms                                               | GET      | D:\Projects\medplatforma\fix_duplicate_routes.py                          | verified |
| /reports                                             | GET      | D:\Projects\medplatforma\fix_duplicate_routes.py                          | verified |
| /patients                                            | GET      | D:\Projects\medplatforma\fix_navigation_and_integration.py                | verified |
| /services                                            | GET      | D:\Projects\medplatforma\fix_navigation_and_integration.py                | verified |
| /doctors                                             | GET      | D:\Projects\medplatforma\fix_navigation_and_integration.py                | verified |
| /rooms                                               | GET      | D:\Projects\medplatforma\fix_navigation_and_integration.py                | verified |
| /reports                                             | GET      | D:\Projects\medplatforma\fix_navigation_and_integration.py                | verified |
| /patients                                            | GET      | D:\Projects\medplatforma\fix_navigation_and_integration.py                | verified |
| /services                                            | GET      | D:\Projects\medplatforma\fix_navigation_and_integration.py                | verified |
| /doctors                                             | GET      | D:\Projects\medplatforma\fix_navigation_and_integration.py                | verified |
| /rooms                                               | GET      | D:\Projects\medplatforma\fix_navigation_and_integration.py                | verified |
| /reports                                             | GET      | D:\Projects\medplatforma\fix_navigation_and_integration.py                | verified |
| {route}                                              | GET      | D:\Projects\medplatforma\fix_navigation_and_missing_pages.py              | verified |
| /patients                                            | GET      | D:\Projects\medplatforma\fix_navigation_and_missing_pages.py              | verified |
| /services                                            | GET      | D:\Projects\medplatforma\fix_navigation_and_missing_pages.py              | verified |
| /debug/info                                          | GET      | D:\Projects\medplatforma\fix_navigation_and_missing_pages.py              | verified |
| /doctors                                             | GET      | D:\Projects\medplatforma\fix_role_implementation.py                       | verified |
| /services                                            | GET      | D:\Projects\medplatforma\fix_role_implementation.py                       | verified |
| /rooms                                               | GET      | D:\Projects\medplatforma\fix_role_implementation.py                       | verified |
| /patients                                            | GET      | D:\Projects\medplatforma\fix_role_implementation.py                       | verified |
| /api/events                                          | GET      | D:\Projects\medplatforma\fix_role_implementation.py                       | verified |
| /api/events                                          | GET      | D:\Projects\medplatforma\fix_role_implementation.py                       | verified |
| /api/events                                          | GET      | D:\Projects\medplatforma\implement_calendar_role_filtering.py             | verified |
| /calendar                                            | GET      | D:\Projects\medplatforma\implement_calendar_role_filtering.py             | verified |
| /api/payments/process                                | POST     | D:\Projects\medplatforma\implement_finance_integration.py                 | verified |
| /api/reports/doctors_revenue                         | GET      | D:\Projects\medplatforma\implement_finance_integration.py                 | verified |
| /api/patients/<id>/history                           | GET      | D:\Projects\medplatforma\implement_patients_crud.py                       | verified |
| /api/patients/search                                 | GET      | D:\Projects\medplatforma\implement_patients_crud.py                       | verified |
| /doctors                                             | GET      | D:\Projects\medplatforma\implement_role_system.py                         | verified |
| /add_doctor                                          | GET      | D:\Projects\medplatforma\implement_role_system.py                         | verified |
| /edit_doctor                                         | GET      | D:\Projects\medplatforma\implement_role_system.py                         | verified |
| /services                                            | GET      | D:\Projects\medplatforma\implement_role_system.py                         | verified |
| /add_service                                         | GET      | D:\Projects\medplatforma\implement_role_system.py                         | verified |
| /edit_service                                        | GET      | D:\Projects\medplatforma\implement_role_system.py                         | verified |
| /rooms                                               | GET      | D:\Projects\medplatforma\implement_role_system.py                         | verified |
| /add_room                                            | GET      | D:\Projects\medplatforma\implement_role_system.py                         | verified |
| /edit_room                                           | GET      | D:\Projects\medplatforma\implement_role_system.py                         | verified |
| /patients                                            | GET      | D:\Projects\medplatforma\implement_role_system.py                         | verified |
| /add_patient                                         | GET      | D:\Projects\medplatforma\implement_role_system.py                         | verified |
| /edit_patient                                        | GET      | D:\Projects\medplatforma\implement_role_system.py                         | verified |
| /finance                                             | GET      | D:\Projects\medplatforma\implement_role_system.py                         | verified |
| /data_tools                                          | GET      | D:\Projects\medplatforma\implement_role_system.py                         | verified |
| /backup                                              | GET      | D:\Projects\medplatforma\implement_role_system.py                         | verified |
| /patients/<id>                                       | GET      | D:\Projects\medplatforma\integrate_patient_cards_and_navigation.py        | verified |
| /switch-user/<user_id>                               | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /api/patients/<id>                                   | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /api/patients/<id>/update                            | POST     | D:\Projects\medplatforma\main.py                                          | verified |
| /api/patients/<patient_id>/bonus                     | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /api/patients/<patient_id>/bonus/add                 | POST     | D:\Projects\medplatforma\main.py                                          | verified |
| /api/patients/<patient_id>/bonus/withdraw            | POST     | D:\Projects\medplatforma\main.py                                          | verified |
| /api/patients/<patient_id>/bonus/history             | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /api/patients/<patient_id>/treatment-plans           | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /patients/<id>                                       | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /patients/<patient_id>/current-visit/complete        | POST     | D:\Projects\medplatforma\main.py                                          | verified |
| /roadmap                                             | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /api/free_slots                                      | POST     | D:\Projects\medplatforma\main.py                                          | verified |
| /                                                    | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /favicon.ico                                         | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /schedule                                            | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /api/rooms/status_now                                | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /api/rooms/today_details                             | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /update_event_time                                   | POST     | D:\Projects\medplatforma\main.py                                          | verified |
| /export_calendar                                     | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /api/patients/export/csv                             | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /api/patients/export/excel                           | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /patients/import                                     | GET,POST | D:\Projects\medplatforma\main.py                                          | verified |
| /dashboard                                           | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /add_event                                           | GET,POST | D:\Projects\medplatforma\main.py                                          | verified |
| /edit_event/<event_id>                               | GET,POST | D:\Projects\medplatforma\main.py                                          | verified |
| /api/busy_slots                                      | POST     | D:\Projects\medplatforma\main.py                                          | verified |
| /busy_slots/<doctor_id>                              | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /doctors                                             | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /add_doctor                                          | GET,POST | D:\Projects\medplatforma\main.py                                          | verified |
| /doctor_card/<doctor_id>                             | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /doctor_busy_slots/<doctor_id>                       | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /api/doctor_schedule                                 | POST     | D:\Projects\medplatforma\main.py                                          | verified |
| /finance_report                                      | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /finance/debtors                                     | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /api/reports/doctors_revenue                         | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /finance_report/export                               | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /tasks                                               | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /add_task                                            | POST     | D:\Projects\medplatforma\main.py                                          | verified |
| /mark_task_done/<task_id>                            | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /task/<task_id>                                      | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /messages                                            | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /ztl                                                 | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /add_ztl                                             | GET,POST | D:\Projects\medplatforma\main.py                                          | verified |
| /partners                                            | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /logs                                                | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /logs/export                                         | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /audit                                               | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /api/audit/<log_id>                                  | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /backup                                              | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /profile                                             | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /settings                                            | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /data_tools                                          | GET,POST | D:\Projects\medplatforma\main.py                                          | verified |
| /export_data                                         | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /import_data                                         | POST     | D:\Projects\medplatforma\main.py                                          | verified |
| /cabinet/<cabinet_name>                              | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /api/events                                          | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /api/services/<id>                                   | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /api/dicts                                           | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /delete_appointment/<id>                             | POST     | D:\Projects\medplatforma\main.py                                          | verified |
| /api/appointments/<id>                               | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /api/appointments/<id>/update                        | POST     | D:\Projects\medplatforma\main.py                                          | verified |
| /api/appointments/update_time                        | POST     | D:\Projects\medplatforma\main.py                                          | verified |
| /api/appointments/<id>                               | DELETE   | D:\Projects\medplatforma\main.py                                          | verified |
| /api/appointments/delete                             | POST     | D:\Projects\medplatforma\main.py                                          | verified |
| /schedule/api/delete                                 | POST     | D:\Projects\medplatforma\main.py                                          | verified |
| /api/services_min                                    | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /api/visit_statuses_min                              | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /api/finance/record                                  | POST     | D:\Projects\medplatforma\main.py                                          | verified |
| /api/chat/<id>/send                                  | POST     | D:\Projects\medplatforma\main.py                                          | verified |
| /services                                            | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /add_service                                         | GET,POST | D:\Projects\medplatforma\main.py                                          | verified |
| /edit_service/<id>                                   | GET,POST | D:\Projects\medplatforma\main.py                                          | verified |
| /delete_service/<id>                                 | POST     | D:\Projects\medplatforma\main.py                                          | verified |
| /rooms                                               | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /add_room                                            | GET,POST | D:\Projects\medplatforma\main.py                                          | verified |
| /edit_room/<id>                                      | GET,POST | D:\Projects\medplatforma\main.py                                          | verified |
| /delete_room/<id>                                    | POST     | D:\Projects\medplatforma\main.py                                          | verified |
| /patients                                            | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /patients/debtors                                    | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /add_patient                                         | GET,POST | D:\Projects\medplatforma\main.py                                          | verified |
| /edit_patient/<id>                                   | GET,POST | D:\Projects\medplatforma\main.py                                          | verified |
| /delete_patient/<id>                                 | POST     | D:\Projects\medplatforma\main.py                                          | verified |
| /patient_card/<id>                                   | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /api/patients/<id>/update_info                       | POST     | D:\Projects\medplatforma\main.py                                          | verified |
| /api/patients/<id>/update_questionary                | POST     | D:\Projects\medplatforma\main.py                                          | verified |
| /api/patients/<id>/generate_card_no                  | POST     | D:\Projects\medplatforma\main.py                                          | verified |
| /api/patients/<id>/full                              | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /patients/<patient_id>/questionnaire                 | GET,POST | D:\Projects\medplatforma\main.py                                          | verified |
| /api/patients                                        | POST     | D:\Projects\medplatforma\main.py                                          | verified |
| /api/appointments/create_core                        | POST     | D:\Projects\medplatforma\main.py                                          | verified |
| /api/appointments                                    | POST     | D:\Projects\medplatforma\main.py                                          | verified |
| /api/appointments/create                             | POST     | D:\Projects\medplatforma\main.py                                          | verified |
| /schedule/api/create                                 | POST     | D:\Projects\medplatforma\main.py                                          | verified |
| /api/patients/search                                 | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /api/dashboard/today-appointments                    | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /api/dashboard/doctor-plans                          | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /api/dashboard/pending-plans                         | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /api/dashboard/debtors                               | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /services                                            | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /rooms                                               | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /reports                                             | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /patients                                            | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /admin/clean_all_demo                                | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /admin/create_test_patient                           | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /admin/mass_cleanup                                  | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /admin/init_production_data                          | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /debug/patients                                      | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /patients/<patient_id>/treatment-plan/new            | GET,POST | D:\Projects\medplatforma\main.py                                          | verified |
| /patients/<patient_id>/treatment-plan/<plan_id>/edit | GET,POST | D:\Projects\medplatforma\main.py                                          | verified |
| /chief/pending-plans                                 | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /doctor/my-plans                                     | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /chief/plan-details/<plan_id>                        | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /chief/approve-plan/<plan_id>                        | POST     | D:\Projects\medplatforma\main.py                                          | verified |
| /chief/request-revision/<plan_id>                    | POST     | D:\Projects\medplatforma\main.py                                          | verified |
| /test-session                                        | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /test-treatment-plan                                 | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /appointments/<appointment_id>/arrive                | POST     | D:\Projects\medplatforma\main.py                                          | verified |
| /appointments/<appointment_id>/no-show               | POST     | D:\Projects\medplatforma\main.py                                          | verified |
| /appointments/<appointment_id>/cancel                | POST     | D:\Projects\medplatforma\main.py                                          | verified |
| /appointments/<appointment_id>/reschedule            | POST     | D:\Projects\medplatforma\main.py                                          | verified |
| /appointments/<appointment_id>/complete              | POST     | D:\Projects\medplatforma\main.py                                          | verified |
| /api/patients/<patient_id>/debts                     | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /services                                            | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /debug/info                                          | GET      | D:\Projects\medplatforma\main.py                                          | verified |
| /api/patients/<id>                                   | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /api/patients/<id>/update                            | POST     | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /patients/<id>                                       | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /roadmap                                             | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /api/free_slots                                      | POST     | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /                                                    | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /favicon.ico                                         | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /calendar                                            | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /api/rooms/status_now                                | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /api/rooms/today_details                             | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /update_event_time                                   | POST     | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /export_calendar                                     | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /api/patients/export/csv                             | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /api/patients/export/excel                           | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /patients/import                                     | GET,POST | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /dashboard                                           | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /add_event                                           | GET,POST | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /edit_event/<event_id>                               | GET,POST | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /api/busy_slots                                      | POST     | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /busy_slots/<doctor_id>                              | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /doctors                                             | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /add_doctor                                          | GET,POST | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /doctor_card/<doctor_id>                             | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /doctor_busy_slots/<doctor_id>                       | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /api/doctor_schedule                                 | POST     | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /finance_report                                      | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /api/reports/doctors_revenue                         | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /finance_report/export                               | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /tasks                                               | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /add_task                                            | POST     | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /mark_task_done/<task_id>                            | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /task/<task_id>                                      | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /messages                                            | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /ztl                                                 | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /add_ztl                                             | GET,POST | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /partners                                            | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /logs                                                | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /logs/export                                         | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /audit                                               | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /api/audit/<log_id>                                  | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /backup                                              | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /profile                                             | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /settings                                            | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /data_tools                                          | GET,POST | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /export_data                                         | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /import_data                                         | POST     | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /cabinet/<cabinet_name>                              | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /api/events                                          | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /api/services/<id>                                   | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /api/dicts                                           | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /delete_appointment/<id>                             | POST     | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /api/appointments/<id>                               | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /api/appointments/<id>/update                        | POST     | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /api/appointments/update_time                        | POST     | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /api/appointments/<id>                               | DELETE   | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /api/appointments/delete                             | POST     | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /schedule/api/delete                                 | POST     | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /api/services_min                                    | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /api/visit_statuses_min                              | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /api/finance/record                                  | POST     | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /api/chat/<id>/send                                  | POST     | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /services                                            | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /add_service                                         | GET,POST | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /edit_service/<id>                                   | GET,POST | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /delete_service/<id>                                 | POST     | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /rooms                                               | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /add_room                                            | GET,POST | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /edit_room/<id>                                      | GET,POST | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /delete_room/<id>                                    | POST     | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /patients                                            | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /add_patient                                         | GET,POST | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /edit_patient/<id>                                   | GET,POST | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /delete_patient/<id>                                 | POST     | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /patient_card/<id>                                   | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /api/patients/<id>/update_info                       | POST     | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /api/patients/<id>/update_questionary                | POST     | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /api/patients/<id>/generate_card_no                  | POST     | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /api/patients/<id>/full                              | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /patients/<patient_id>/questionnaire                 | GET,POST | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /api/patients                                        | POST     | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /api/appointments/create_core                        | POST     | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /api/appointments                                    | POST     | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /api/appointments/create                             | POST     | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /schedule/api/create                                 | POST     | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /api/patients/search                                 | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /services                                            | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /rooms                                               | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /reports                                             | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /patients                                            | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /admin/clean_all_demo                                | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /admin/create_test_patient                           | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /admin/mass_cleanup                                  | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /admin/init_production_data                          | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /debug/patients                                      | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /services                                            | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /debug/info                                          | GET      | D:\Projects\medplatforma\main_clean.py                                    | verified |
| /add_patient                                         | GET,POST | D:\Projects\medplatforma\missing_routes_fix.py                            | verified |
| /add_service                                         | GET,POST | D:\Projects\medplatforma\missing_routes_fix.py                            | verified |
| /edit_patient/<patient_id>                           | GET,POST | D:\Projects\medplatforma\missing_routes_fix.py                            | verified |
| /rooms                                               | GET      | D:\Projects\medplatforma\missing_routes_fix.py                            | verified |
| /reports                                             | GET      | D:\Projects\medplatforma\missing_routes_fix.py                            | verified |
| /login                                               | GET,POST | D:\Projects\medplatforma\production_auth.py                               | verified |
| /logout                                              | GET      | D:\Projects\medplatforma\production_auth.py                               | verified |
| /api/current-user                                    | GET      | D:\Projects\medplatforma\production_auth.py                               | verified |
| /change-password                                     | POST     | D:\Projects\medplatforma\production_auth.py                               | verified |
| /doctors                                             | GET      | D:\Projects\medplatforma\remove_duplicate_doctors_final.py                | verified |
| /doctors                                             | GET      | D:\Projects\medplatforma\remove_duplicate_doctors_final.py                | verified |
| /doctors                                             | GET      | D:\Projects\medplatforma\remove_duplicate_doctors_final.py                | verified |
| /doctors                                             | GET      | D:\Projects\medplatforma\remove_duplicate_doctors_final.py                | verified |
| /doctors                                             | GET      | D:\Projects\medplatforma\remove_duplicate_doctors_final.py                | verified |
| /doctors                                             | GET      | D:\Projects\medplatforma\remove_duplicate_doctors_final.py                | verified |
| /add                                                 | GET      | D:\Projects\medplatforma\routes_finance.py                                | verified |
| /add                                                 | POST     | D:\Projects\medplatforma\routes_finance.py                                | verified |
| /delete/<operation_id>                               | GET,POST | D:\Projects\medplatforma\routes_finance.py                                | verified |
| /                                                    | GET      | D:\Projects\medplatforma\routes_schedule.py                               | verified |
| /add                                                 | POST     | D:\Projects\medplatforma\routes_schedule.py                               | verified |
| /free_slots                                          | GET      | D:\Projects\medplatforma\routes_schedule.py                               | verified |
| /transfer                                            | GET      | D:\Projects\medplatforma\routes_transfer.py                               | verified |
| /transfer                                            | POST     | D:\Projects\medplatforma\routes_transfer.py                               | verified |
| /transfer/history                                    | GET      | D:\Projects\medplatforma\routes_transfer.py                               | verified |
| /transfer/delete/<id>                                | POST     | D:\Projects\medplatforma\routes_transfer.py                               | verified |
| /api/patients/<patient_id>/treatment-plans           | GET      | D:\Projects\medplatforma\treatment_plan_api_insert.py                     | verified |
| /switch-user/<user_id>                               | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /api/patients/<id>                                   | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /api/patients/<id>/update                            | POST     | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /api/patients/<patient_id>/bonus                     | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /api/patients/<patient_id>/bonus/add                 | POST     | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /api/patients/<patient_id>/bonus/withdraw            | POST     | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /api/patients/<patient_id>/bonus/history             | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /api/patients/<patient_id>/treatment-plans           | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /patients/<id>                                       | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /patients/<patient_id>/current-visit/complete        | POST     | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /roadmap                                             | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /api/free_slots                                      | POST     | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /                                                    | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /favicon.ico                                         | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /schedule                                            | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /api/rooms/status_now                                | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /api/rooms/today_details                             | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /update_event_time                                   | POST     | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /export_calendar                                     | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /api/patients/export/csv                             | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /api/patients/export/excel                           | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /patients/import                                     | GET,POST | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /dashboard                                           | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /add_event                                           | GET,POST | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /edit_event/<event_id>                               | GET,POST | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /api/busy_slots                                      | POST     | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /busy_slots/<doctor_id>                              | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /doctors                                             | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /add_doctor                                          | GET,POST | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /doctor_card/<doctor_id>                             | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /doctor_busy_slots/<doctor_id>                       | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /api/doctor_schedule                                 | POST     | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /finance_report                                      | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /finance/debtors                                     | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /api/reports/doctors_revenue                         | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /finance_report/export                               | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /tasks                                               | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /add_task                                            | POST     | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /mark_task_done/<task_id>                            | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /task/<task_id>                                      | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /messages                                            | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /ztl                                                 | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /add_ztl                                             | GET,POST | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /partners                                            | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /logs                                                | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /logs/export                                         | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /audit                                               | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /api/audit/<log_id>                                  | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /backup                                              | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /profile                                             | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /settings                                            | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /data_tools                                          | GET,POST | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /export_data                                         | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /import_data                                         | POST     | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /cabinet/<cabinet_name>                              | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /api/events                                          | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /api/services/<id>                                   | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /api/dicts                                           | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /delete_appointment/<id>                             | POST     | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /api/appointments/<id>                               | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /api/appointments/<id>/update                        | POST     | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /api/appointments/update_time                        | POST     | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /api/appointments/<id>                               | DELETE   | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /api/appointments/delete                             | POST     | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /schedule/api/delete                                 | POST     | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /api/services_min                                    | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /api/visit_statuses_min                              | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /api/finance/record                                  | POST     | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /api/chat/<id>/send                                  | POST     | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /services                                            | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /add_service                                         | GET,POST | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /edit_service/<id>                                   | GET,POST | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /delete_service/<id>                                 | POST     | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /rooms                                               | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /add_room                                            | GET,POST | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /edit_room/<id>                                      | GET,POST | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /delete_room/<id>                                    | POST     | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /patients                                            | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /patients/debtors                                    | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /add_patient                                         | GET,POST | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /edit_patient/<id>                                   | GET,POST | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /delete_patient/<id>                                 | POST     | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /patient_card/<id>                                   | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /api/patients/<id>/update_info                       | POST     | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /api/patients/<id>/update_questionary                | POST     | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /api/patients/<id>/generate_card_no                  | POST     | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /api/patients/<id>/full                              | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /patients/<patient_id>/questionnaire                 | GET,POST | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /api/patients                                        | POST     | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /api/appointments/create_core                        | POST     | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /api/appointments                                    | POST     | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /api/appointments/create                             | POST     | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /schedule/api/create                                 | POST     | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /api/patients/search                                 | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /api/dashboard/today-appointments                    | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /api/dashboard/doctor-plans                          | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /api/dashboard/pending-plans                         | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /api/dashboard/debtors                               | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /services                                            | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /rooms                                               | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /reports                                             | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /patients                                            | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /admin/clean_all_demo                                | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /admin/create_test_patient                           | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /admin/mass_cleanup                                  | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /admin/init_production_data                          | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /debug/patients                                      | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /patients/<patient_id>/treatment-plan/new            | GET,POST | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /patients/<patient_id>/treatment-plan/<plan_id>/edit | GET,POST | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /chief/pending-plans                                 | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /doctor/my-plans                                     | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /chief/plan-details/<plan_id>                        | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /chief/approve-plan/<plan_id>                        | POST     | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /chief/request-revision/<plan_id>                    | POST     | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /test-session                                        | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /test-treatment-plan                                 | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /appointments/<appointment_id>/arrive                | POST     | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /appointments/<appointment_id>/no-show               | POST     | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /appointments/<appointment_id>/cancel                | POST     | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /appointments/<appointment_id>/reschedule            | POST     | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /appointments/<appointment_id>/complete              | POST     | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /api/patients/<patient_id>/debts                     | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /services                                            | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /debug/info                                          | GET      | D:\Projects\medplatforma\backups\main_backup_2025-10-07_10-26.py          | verified |
| /                                                    | GET      | D:\Projects\medplatforma\.venv\Lib\site-packages\flask\ctx.py             | verified |
| /                                                    | GET      | D:\Projects\medplatforma\.venv\Lib\site-packages\flask\ctx.py             | verified |
| /stream                                              | GET      | D:\Projects\medplatforma\.venv\Lib\site-packages\flask\helpers.py         | verified |
| /stream                                              | GET      | D:\Projects\medplatforma\.venv\Lib\site-packages\flask\helpers.py         | verified |
| /uploads/<path:name>                                 | GET      | D:\Projects\medplatforma\.venv\Lib\site-packages\flask\helpers.py         | verified |
| /                                                    | GET      | D:\Projects\medplatforma\.venv\Lib\site-packages\flask\sansio\scaffold.py | verified |
| /                                                    | GET      | D:\Projects\medplatforma\.venv\Lib\site-packages\flask\sansio\scaffold.py | verified |

---

## 2) Pending / Planned — спроектировано (нужно реализовать/подтвердить)
| Route                                      | Methods   | File (expected)      | Status  |
| ------------------------------------------ | --------- | -------------------- | ------- |
| /api/patients/<id>/plans                   | POST,GET  | plans.py (expected)  | planned |
| /api/plans/<plan_id>                       | GET,PATCH | plans.py (expected)  | planned |
| /api/plans/<plan_id>/submit                | POST      | plans.py (expected)  | planned |
| /api/plans/<plan_id>/approve               | POST      | chief.py (expected)  | planned |
| /api/plans/<plan_id>/reject                | POST      | chief.py (expected)  | planned |
| /api/plans/<plan_id>/services              | POST      | plans.py (expected)  | planned |
| /api/plans/<plan_id>/services/<i>          | PATCH     | plans.py (expected)  | planned |
| /api/plans/<plan_id>/services/<i>/complete | POST      | plans.py (expected)  | planned |
| /api/dental-legend                         | GET       | dental.py (expected) | planned |
| /api/patients/<id>/dental-chart            | PATCH     | dental.py (expected) | pending |
| /api/patients/<id>/dental-chart/image      | POST      | dental.py (expected) | planned |

---

## 3) Шаблоны Jinja2 (обнаружены)
| Template path                 |
| ----------------------------- |
| 404.html                      |
| add_doctor.html               |
| add_event.html                |
| add_patient.html              |
| add_room.html                 |
| add_service.html              |
| add_ztl.html                  |
| audit_logs.html               |
| backup.html                   |
| cabinet_card.html             |
| calendar.html                 |
| chief_pending_plans.html      |
| data_tools.html               |
| doctor_card.html              |
| doctor_my_plans.html          |
| doctors.html                  |
| edit_event.html               |
| edit_patient.html             |
| edit_room.html                |
| edit_service.html             |
| finance/add.html              |
| finance/cashbox.html          |
| finance/debtors.html          |
| finance/list.html             |
| finance/transfer.html         |
| finance/transfer_history.html |
| finance_report.html           |
| import_patients.html          |
| index.html                    |
| login.html                    |
| messages.html                 |
| not_found.html                |
| partners.html                 |
| patient_card.html             |
| patient_edit.html             |
| patient_questionnaire.html    |
| patients.html                 |
| patients_debtors.html         |
| profile.html                  |
| reports.html                  |
| roadmap.html                  |
| roadmap_missing.html          |
| rooms.html                    |
| schedule/list.html            |
| schedule_view.html            |
| services.html                 |
| settings.html                 |
| task_card.html                |
| tasks.html                    |
| treatment_plan_edit.html      |
| treatment_plan_new.html       |
| ztl.html                      | 

---

## 4) JS-переходы/вызовы API (обнаружены)
| URL                                                          |
| ------------------------------------------------------------ |
| /api/admin/seed/disable_demo                                 |
| /api/admin/seed/load                                         |
| /api/admin/seed/ping                                         |
| /api/admin/seed/upload                                       |
| /api/appointments/update_time                                |
| /api/dashboard/debtors                                       |
| /api/dashboard/doctor-plans                                  |
| /api/dashboard/pending-plans                                 |
| /api/dashboard/today-appointments                            |
| /api/dicts                                                   |
| /api/doctor_schedule                                         |
| /api/events?                                                 |
| /api/patients                                                |
| /api/patients/                                               |
| /api/patients/68dd28b620210e8e4cad772b/bonus/add             |
| /api/patients/68dd28b620210e8e4cad772b/bonus/history         |
| /api/patients/68dd28b620210e8e4cad772b/bonus/withdraw        |
| /api/patients/{{ patient._id }}/bonus/add                    |
| /api/patients/{{ patient._id }}/bonus/history                |
| /api/patients/{{ patient._id }}/bonus/withdraw               |
| /api/rooms/status_now                                        |
| /calendar?patient_id=68dd28b620210e8e4cad772b                |
| /calendar?patient_id={{ patient._id }}                       |
| /finance/add?patient_id=68dd28b620210e8e4cad772b&type=income |
| /finance/add?patient_id={{ patient._id }}&type=income        |
| /patients/68dd28b620210e8e4cad772b/edit                      |
| /patients/{{ patient._id }}/edit                             | 

---

## 5) Пересечения (UX Map — ориентир)
- Календарь → Карта пациента: «Подробнее» → `/patients/<id>`
- Календарь → Планы лечения: «Добавить в план» / «Записать повторно»
- Карта пациента → Финансы: операции, долги, оплаты
- Планы → Календарь: слоты после approve, `refetchEvents()` после завершений

---

## 6) Процесс актуализации карты (обязательно к использованию)
1. При создании/изменении маршрута/шаблона/файла — в PR добавь секцию:
```
UPDATE:
- ARCH_MAP: добавить/обновить маршрут {"METHODS /path"} → <file> (status: planned→verified)
```
2. Запусти сканер и приложи `routes.json` в PR:
```powershell
python arch_verify.py --root . --out routes.json
```
3. Если маршрут найден — меняем статус строки на **verified**. Если нет — оставляем **planned/pending** до реализации.
4. В `docs_bundle.md` (оперативка) обнови блок **Route Summary** (см. ниже).

---

## 7) Route Summary (топ-5 переходов)
- `/calendar` → модалка → `POST /appointments/<id>/complete`
- Модалка → «Подробнее» → `GET /patients/<id>`
- Модалка → «Записать повторно» → черновик записи (JS → `/calendar?...`)
- Финансы: `POST /finance/add`, `POST /finance/transfer`
- Согласование планов: `GET /chief/pending-plans`

> Полная таблица — в разделах 1–2 выше.
